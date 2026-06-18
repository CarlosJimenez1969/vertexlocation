"""
traccar_bridge.py — Puente en tiempo real con Traccar usando la librería
`websockets` de Python.

Flujo:
  1. Inicia sesión en Traccar vía REST para obtener la cookie JSESSIONID.
  2. Abre el WebSocket de Traccar (ws://.../api/socket) con esa cookie.
  3. Por cada mensaje (positions / events / devices), normaliza y reenvía a
     los clientes conectados mediante el ConnectionManager, y persiste las
     posiciones en la base de datos.

Se ejecuta como tarea de fondo (asyncio) al arrancar FastAPI.
"""
from __future__ import annotations

import asyncio
import json
import time

import requests
import websockets
from sqlalchemy import select

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.device import Device
from app.models.pet import Pet
from app.models.position import Position
from app.models.vehicle import Vehicle
from app.realtime.manager import manager
from app.services.traccar import normalize_position
from app.services.vehicle_security import (
    check_armed_movement, check_geofence_exit, check_speeding,
)

RECONNECT_DELAY = 10  # segundos

# --- Cache del mapa traccar_device_id -> owner ---
# Se reconstruye desde la DB como máximo cada OWNER_CACHE_TTL segundos, o de
# inmediato cuando una ruta registra/edita/elimina dispositivos o mascotas
# (vía invalidate_owner_cache()). Evita varias queries por cada mensaje del WS.
OWNER_CACHE_TTL = 30.0  # segundos
_owner_cache: dict[int, dict] | None = None
_owner_cache_ts: float = 0.0


def invalidate_owner_cache() -> None:
    """Fuerza la reconstrucción del mapa en la próxima consulta."""
    global _owner_cache
    _owner_cache = None


def _login_get_cookie() -> str | None:
    """Inicia sesión en Traccar y devuelve la cookie de sesión."""
    try:
        r = requests.post(
            f"{settings.TRACCAR_URL.rstrip('/')}/api/session",
            data={"email": settings.TRACCAR_USER, "password": settings.TRACCAR_PASSWORD},
            timeout=10,
        )
        r.raise_for_status()
        return "; ".join(f"{k}={v}" for k, v in r.cookies.get_dict().items())
    except Exception as e:
        print(f"[Bridge] Login en Traccar falló: {e}")
        return None


def _build_owner_map() -> dict[int, dict]:
    """traccar_device_id -> {usuario_id, dispositivo_id, mascota_id} (desde DB)."""
    mapping: dict[int, dict] = {}
    with SessionLocal() as db:
        devices = db.scalars(select(Device).where(Device.traccar_device_id.isnot(None))).all()
        dev_ids = [d.id for d in devices]
        # Una sola query por tipo de activo (evita el N+1 por dispositivo).
        pets = (
            db.scalars(select(Pet).where(Pet.dispositivo_id.in_(dev_ids))).all()
            if dev_ids else []
        )
        vehicles = (
            db.scalars(select(Vehicle).where(Vehicle.dispositivo_id.in_(dev_ids))).all()
            if dev_ids else []
        )
        pet_por_dispositivo = {p.dispositivo_id: p for p in pets}
        veh_por_dispositivo = {v.dispositivo_id: v for v in vehicles}
        for d in devices:
            pet = pet_por_dispositivo.get(d.id)
            veh = veh_por_dispositivo.get(d.id)
            # Dueño: el del dispositivo o, en su defecto, el del activo asignado.
            owner_id = d.usuario_id or (pet.usuario_id if pet else None) or (veh.usuario_id if veh else None)
            if not owner_id:
                continue  # dispositivo sin asignar: no hay a quién notificar
            mapping[d.traccar_device_id] = {
                "usuario_id": str(owner_id),
                "dispositivo_id": d.id,
                "mascota_id": pet.id if pet else None,
                "vehiculo_id": veh.id if veh else None,
            }
    return mapping


def _device_owner_map() -> dict[int, dict]:
    """Devuelve el mapa cacheado, reconstruyéndolo si expiró o fue invalidado."""
    global _owner_cache, _owner_cache_ts
    ahora = time.monotonic()
    if _owner_cache is not None and (ahora - _owner_cache_ts) < OWNER_CACHE_TTL:
        return _owner_cache
    _owner_cache = _build_owner_map()
    _owner_cache_ts = ahora
    return _owner_cache


async def _handle_message(raw: str) -> None:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return

    owner_map = _device_owner_map()

    # Posiciones en vivo
    for pos in data.get("positions", []) or []:
        tdid = pos.get("deviceId")
        owner = owner_map.get(tdid)
        if not owner:
            continue
        norm = normalize_position(pos)

        # Persistir + chequeos de vehículo (anti-robo armado y exceso de velocidad)
        alertas_veh: list[dict] = []
        try:
            with SessionLocal() as db:
                if norm["traccar_pos_id"] and not db.scalar(
                    select(Position).where(
                        Position.dispositivo_id == owner["dispositivo_id"],
                        Position.traccar_pos_id == norm["traccar_pos_id"],
                    )
                ):
                    db.add(Position(
                        dispositivo_id=owner["dispositivo_id"],
                        mascota_id=owner["mascota_id"], **norm,
                    ))
                    db.commit()
                if owner.get("vehiculo_id"):
                    veh = db.get(Vehicle, owner["vehiculo_id"])  # estado fresco cada vez
                    if veh:
                        a1 = check_armed_movement(db, veh, norm["latitud"], norm["longitud"])
                        if a1:
                            alertas_veh.append(a1)
                        a2 = check_speeding(db, veh, norm["velocidad"], norm["latitud"], norm["longitud"])
                        if a2:
                            alertas_veh.append(a2)
                        alertas_veh.extend(
                            check_geofence_exit(db, veh, norm["latitud"], norm["longitud"])
                        )
        except Exception as e:
            print(f"[Bridge] Error guardando posición: {e}")

        # Alertas de vehículo en tiempo real
        for al in alertas_veh:
            await manager.send_to_user(owner["usuario_id"], al)

        await manager.send_to_user(owner["usuario_id"], {
            "type": "position",
            "mascota_id": str(owner["mascota_id"]) if owner["mascota_id"] else None,
            "vehiculo_id": str(owner["vehiculo_id"]) if owner.get("vehiculo_id") else None,
            "latitud": norm["latitud"],
            "longitud": norm["longitud"],
            "velocidad": norm["velocidad"],
            "rumbo": norm["rumbo"],
            "bateria": norm["bateria"],
            "fija_en": norm["fija_en"],
        })

    # Eventos (geocerca, etc.)
    for ev in data.get("events", []) or []:
        owner = owner_map.get(ev.get("deviceId"))
        if owner:
            await manager.send_to_user(owner["usuario_id"], {"type": "event", "event": ev})


async def run_bridge() -> None:
    """Bucle principal del puente con reconexión automática."""
    while True:
        cookie = _login_get_cookie()
        if not cookie:
            await asyncio.sleep(RECONNECT_DELAY)
            continue
        try:
            async with websockets.connect(
                settings.TRACCAR_WS_URL,
                extra_headers={"Cookie": cookie},
                ping_interval=30,
            ) as ws:
                print("[Bridge] Conectado al WebSocket de Traccar.")
                async for message in ws:
                    await _handle_message(message)
        except Exception as e:
            print(f"[Bridge] Conexión perdida ({e}); reintentando en {RECONNECT_DELAY}s.")
            await asyncio.sleep(RECONNECT_DELAY)
