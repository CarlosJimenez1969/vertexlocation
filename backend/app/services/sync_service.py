"""
sync_service.py — Sincroniza posiciones desde Traccar hacia la DB,
verifica geocercas, batería y dispara alertas.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.device import Device
from app.models.geofence import Geofence
from app.models.pet import Pet
from app.models.position import Position
from app.services import geofence as geo
from app.services.alerts import create_alert
from app.services.traccar import traccar, normalize_position

BATERIA_BAJA = 20  # %


def sync_device_positions(db: Session, device: Device) -> int:
    """
    Trae la última posición de un dispositivo desde Traccar, la guarda si es
    nueva y ejecuta las verificaciones de geocerca/batería. Devuelve nº de
    posiciones nuevas insertadas.
    """
    if not device.traccar_device_id:
        return 0

    try:
        live = traccar.get_latest_positions([device.traccar_device_id])
    except Exception as e:
        print(f"[Sync] Traccar no respondió para {device.imei}: {e}")
        return 0

    nuevas = 0
    pet = db.scalar(select(Pet).where(Pet.dispositivo_id == device.id))

    for raw in live or []:
        norm = normalize_position(raw)
        if norm["latitud"] is None or norm["traccar_pos_id"] is None:
            continue

        # Evitar duplicados
        existe = db.scalar(
            select(Position).where(
                Position.dispositivo_id == device.id,
                Position.traccar_pos_id == norm["traccar_pos_id"],
            )
        )
        if existe:
            continue

        pos = Position(dispositivo_id=device.id, mascota_id=pet.id if pet else None, **norm)
        db.add(pos)
        nuevas += 1

        # Actualizar estado del dispositivo
        device.online = True
        device.ultima_conexion = datetime.now(timezone.utc)
        if norm["bateria"] is not None:
            device.bateria = norm["bateria"]

        # Verificaciones
        if pet:
            _check_geofences(db, pet, norm["latitud"], norm["longitud"])
        _check_battery(db, device, pet, norm["bateria"])

    db.commit()
    return nuevas


def _check_geofences(db: Session, pet: Pet, lat: float, lng: float) -> None:
    gfs = db.scalars(
        select(Geofence).where(
            Geofence.usuario_id == pet.usuario_id, Geofence.activa.is_(True)
        )
    ).all()
    for g in gfs:
        if g.mascota_id not in (None, pet.id):
            continue
        dentro = geo.is_inside(lat, lng, g)
        if not dentro and g.alerta_salida:
            create_alert(
                db, usuario_id=pet.usuario_id, mascota_id=pet.id, geocerca_id=g.id,
                tipo="salida_geocerca",
                titulo=f"{pet.nombre} salió de {g.nombre}",
                mensaje="La mascota abandonó la zona segura.",
                lat=lat, lng=lng, canales=["app", "whatsapp"],
            )
        elif dentro and g.alerta_entrada:
            create_alert(
                db, usuario_id=pet.usuario_id, mascota_id=pet.id, geocerca_id=g.id,
                tipo="entrada_geocerca",
                titulo=f"{pet.nombre} entró a {g.nombre}",
                lat=lat, lng=lng, canales=["app"],
            )


def _check_battery(db: Session, device: Device, pet: Pet | None, bateria: int | None) -> None:
    if bateria is not None and bateria <= BATERIA_BAJA and pet:
        create_alert(
            db, usuario_id=pet.usuario_id, mascota_id=pet.id,
            tipo="bateria_baja",
            titulo=f"Batería baja en el collar de {pet.nombre}",
            mensaje=f"Nivel de batería: {bateria}%. Conecta el cargador magnético.",
            canales=["app"],
        )


def sync_all(db: Session) -> dict:
    """Sincroniza todos los dispositivos activos. Pensado para Celery."""
    devices = db.scalars(select(Device).where(Device.activo.is_(True))).all()
    total = sum(sync_device_positions(db, d) for d in devices)
    return {"dispositivos": len(devices), "posiciones_nuevas": total}
