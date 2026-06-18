"""
vehicle_security.py — Lógica anti-robo del modo estacionado/armado.

Cuando un vehículo está "armado" y su posición se aleja más de
MOVE_THRESHOLD_M de donde se armó, se dispara una alerta (app + WhatsApp)
una sola vez por sesión de armado.
"""
from __future__ import annotations

import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.geofence import Geofence
from app.models.vehicle import Vehicle
from app.services.alerts import create_alert
from app.services.geofence import haversine_m, is_inside

MOVE_THRESHOLD_M = 80.0           # metros de tolerancia antes de alertar
SPEED_ALERT_COOLDOWN = 300.0      # s entre alertas de velocidad por vehículo

# Estado en memoria (proceso único)
_last_speed_alert: dict[str, float] = {}            # vehiculo_id -> última alerta (monotonic)
_geofence_inside: dict[tuple[str, str], bool] = {}  # (vehiculo_id, geocerca_id) -> dentro?


def check_armed_movement(db: Session, vehicle: Vehicle, lat: float | None, lng: float | None) -> dict | None:
    """
    Si el vehículo está armado y se movió más allá del umbral, crea la alerta
    y devuelve un dict para difundir por WebSocket. Si no, devuelve None.
    """
    if not vehicle.armado or vehicle.alerta_movimiento_enviada:
        return None
    if None in (vehicle.armado_lat, vehicle.armado_lng, lat, lng):
        return None

    dist = haversine_m(vehicle.armado_lat, vehicle.armado_lng, lat, lng)
    if dist < MOVE_THRESHOLD_M:
        return None

    titulo = f"🚨 ¡Movimiento detectado! {vehicle.alias}"
    mensaje = (
        f"Tu vehículo se movió {dist:.0f} m estando estacionado/armado. "
        f"Si no eres tú, podría tratarse de un robo."
    )
    create_alert(
        db,
        usuario_id=vehicle.usuario_id,
        tipo="vehiculo_movimiento",
        titulo=titulo,
        mensaje=mensaje,
        lat=lat,
        lng=lng,
        canales=["app", "whatsapp"],
        metadata={"vehiculo_id": str(vehicle.id), "alias": vehicle.alias, "distancia_m": round(dist)},
    )
    vehicle.alerta_movimiento_enviada = True
    db.commit()

    return {
        "type": "alert",
        "tipo": "vehiculo_movimiento",
        "titulo": titulo,
        "mensaje": mensaje,
        "latitud": lat,
        "longitud": lng,
        "vehiculo_id": str(vehicle.id),
    }


def check_speeding(db: Session, vehicle: Vehicle, speed_kmh: float | None,
                   lat: float | None, lng: float | None) -> dict | None:
    """
    Si la velocidad supera el límite del vehículo, crea una alerta (con
    enfriamiento para no repetir). Devuelve dict para WebSocket o None.
    """
    limite = vehicle.limite_velocidad
    if not limite or speed_kmh is None or speed_kmh <= limite:
        return None

    ahora = time.monotonic()
    if ahora - _last_speed_alert.get(str(vehicle.id), 0.0) < SPEED_ALERT_COOLDOWN:
        return None
    _last_speed_alert[str(vehicle.id)] = ahora

    titulo = f"⚡ Exceso de velocidad — {vehicle.alias}"
    mensaje = f"Velocidad {speed_kmh:.0f} km/h (límite {limite} km/h)."
    create_alert(
        db,
        usuario_id=vehicle.usuario_id,
        tipo="exceso_velocidad",
        titulo=titulo,
        mensaje=mensaje,
        lat=lat,
        lng=lng,
        canales=["app", "whatsapp"],
        metadata={"vehiculo_id": str(vehicle.id), "alias": vehicle.alias,
                  "velocidad": round(speed_kmh), "limite": limite},
    )
    return {
        "type": "alert",
        "tipo": "exceso_velocidad",
        "titulo": titulo,
        "mensaje": mensaje,
        "latitud": lat,
        "longitud": lng,
        "vehiculo_id": str(vehicle.id),
    }


def check_geofence_exit(db: Session, vehicle: Vehicle, lat: float | None, lng: float | None) -> list[dict]:
    """
    Alerta si el vehículo SALE de alguna de sus geocercas activas con
    alerta_salida. Usa estado en memoria para detectar la transición
    dentro -> fuera (no repite mientras siga afuera).
    """
    avisos: list[dict] = []
    if lat is None or lng is None:
        return avisos

    geocercas = db.scalars(
        select(Geofence).where(
            Geofence.vehiculo_id == vehicle.id,
            Geofence.activa.is_(True),
            Geofence.alerta_salida.is_(True),
        )
    ).all()

    for g in geocercas:
        dentro = is_inside(lat, lng, g)
        clave = (str(vehicle.id), str(g.id))
        previo = _geofence_inside.get(clave)
        _geofence_inside[clave] = dentro
        # Solo alerta en la transición dentro -> fuera.
        if previo and not dentro:
            titulo = f"📍 Salió de la zona — {vehicle.alias}"
            mensaje = f"Tu vehículo salió de la zona segura '{g.nombre}'."
            create_alert(
                db,
                usuario_id=vehicle.usuario_id,
                tipo="salida_geocerca",
                titulo=titulo,
                mensaje=mensaje,
                lat=lat,
                lng=lng,
                geocerca_id=g.id,
                canales=["app", "whatsapp"],
                metadata={"vehiculo_id": str(vehicle.id), "geocerca": g.nombre},
            )
            avisos.append({
                "type": "alert",
                "tipo": "salida_geocerca",
                "titulo": titulo,
                "mensaje": mensaje,
                "latitud": lat,
                "longitud": lng,
                "vehiculo_id": str(vehicle.id),
            })
    return avisos
