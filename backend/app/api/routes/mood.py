"""Rutas de estado de ánimo y actividad semanal."""
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.activity import DailyActivity
from app.models.mood import MoodState
from app.models.pet import Pet
from app.models.user import User
from app.schemas.tracking import ActivityDayOut, MoodOut
from app.services.mood_service import compute_and_store_mood

router = APIRouter(prefix="/mood", tags=["estado-animo"])


@router.get("/{pet_id}/current", response_model=MoodOut | None)
def animo_actual(
    pet_id: uuid.UUID,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Último estado de ánimo calculado para la mascota."""
    _owned_pet(db, pet_id, current.id)
    return db.scalar(
        select(MoodState).where(MoodState.mascota_id == pet_id)
        .order_by(MoodState.creado_en.desc()).limit(1)
    )


@router.post("/{pet_id}/recalculate", response_model=MoodOut | None)
def recalcular_animo(
    pet_id: uuid.UUID,
    horas: int = Query(3, ge=1, le=24),
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Recalcula el ánimo bajo demanda usando las últimas N horas."""
    _owned_pet(db, pet_id, current.id)
    return compute_and_store_mood(db, pet_id, window_hours=horas)


@router.get("/{pet_id}/history", response_model=list[MoodOut])
def historial_animo(
    pet_id: uuid.UUID,
    dias: int = Query(7, ge=1, le=180),
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _owned_pet(db, pet_id, current.id)
    desde = datetime.now(timezone.utc) - timedelta(days=dias)
    return db.scalars(
        select(MoodState)
        .where(MoodState.mascota_id == pet_id, MoodState.creado_en >= desde)
        .order_by(MoodState.creado_en.asc())
    ).all()


@router.get("/{pet_id}/activity", response_model=list[ActivityDayOut])
def actividad_semanal(
    pet_id: uuid.UUID,
    dias: int = Query(7, ge=1, le=180),
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Resumen de actividad: pasos, distancia, calorías, activo/reposo."""
    _owned_pet(db, pet_id, current.id)
    desde = (datetime.now(timezone.utc) - timedelta(days=dias)).date()
    return db.scalars(
        select(DailyActivity)
        .where(DailyActivity.mascota_id == pet_id, DailyActivity.fecha >= desde)
        .order_by(DailyActivity.fecha.asc())
    ).all()


def _owned_pet(db: Session, pet_id: uuid.UUID, user_id: uuid.UUID) -> Pet:
    pet = db.get(Pet, pet_id)
    if not pet or pet.usuario_id != user_id:
        raise HTTPException(404, "Mascota no encontrada")
    return pet
