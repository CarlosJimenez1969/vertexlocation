"""Rutas de posiciones e historial de rutas (hasta 180 días según plan)."""
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.device import Device
from app.models.pet import Pet
from app.models.position import Position
from app.models.user import User
from app.schemas.tracking import PositionOut
from app.services.traccar import traccar, normalize_position

router = APIRouter(prefix="/positions", tags=["posiciones"])


@router.get("/latest/{pet_id}", response_model=PositionOut | None)
def ultima_posicion(
    pet_id: uuid.UUID,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Última posición conocida de la mascota (cache local + Traccar en vivo)."""
    pet = _owned_pet(db, pet_id, current.id)
    if not pet.dispositivo_id:
        raise HTTPException(400, "La mascota no tiene collar asignado")

    device = db.get(Device, pet.dispositivo_id)
    # Intentar posición en vivo desde Traccar
    if device and device.traccar_device_id:
        try:
            live = traccar.get_latest_positions([device.traccar_device_id])
            if live:
                norm = normalize_position(live[0])
                return PositionOut(
                    id=0,
                    latitud=norm["latitud"],
                    longitud=norm["longitud"],
                    velocidad=norm["velocidad"],
                    rumbo=norm["rumbo"],
                    bateria=norm["bateria"],
                    fija_en=norm["fija_en"],
                )
        except Exception as e:
            print(f"[Traccar] posición en vivo falló: {e}")

    # Fallback a la última guardada en DB
    pos = db.scalar(
        select(Position)
        .where(Position.dispositivo_id == pet.dispositivo_id)
        .order_by(Position.fija_en.desc())
        .limit(1)
    )
    return pos


@router.get("/history/{pet_id}", response_model=list[PositionOut])
def historial(
    pet_id: uuid.UUID,
    dias: int = Query(7, ge=1, le=180),
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Historial de rutas de los últimos N días (límite según plan: 7/30/180)."""
    pet = _owned_pet(db, pet_id, current.id)
    desde = datetime.now(timezone.utc) - timedelta(days=dias)
    rows = db.scalars(
        select(Position)
        .where(Position.dispositivo_id == pet.dispositivo_id, Position.fija_en >= desde)
        .order_by(Position.fija_en.asc())
    ).all()
    return rows


def _owned_pet(db: Session, pet_id: uuid.UUID, user_id: uuid.UUID) -> Pet:
    pet = db.get(Pet, pet_id)
    if not pet or pet.usuario_id != user_id:
        raise HTTPException(404, "Mascota no encontrada")
    return pet
