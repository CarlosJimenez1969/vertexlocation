"""
plan_service.py — Resolución del plan del usuario y verificación de límites.

Los planes se siembran en `db_seed.py` (basico/estandar/premium) con sus
límites (`max_mascotas`, `max_geocercas`; -1 = ilimitado). Aquí se resuelve el
plan de la suscripción activa del usuario y se hacen cumplir esos límites al
crear mascotas, dispositivos (collares) y geocercas.
"""
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.device import Device
from app.models.geofence import Geofence
from app.models.pet import Pet
from app.models.plan import Plan, Subscription
from app.models.user import User

# Fallback seguro (= plan Básico) si el usuario no tiene suscripción activa
# ni existe el plan "basico" sembrado.
DEFAULT_LIMITS = {"max_mascotas": 1, "max_geocercas": 1}


def get_user_plan(db: Session, user: User) -> Plan | None:
    """Plan de la suscripción activa del usuario; si no hay, el plan 'basico'."""
    plan = db.scalar(
        select(Plan)
        .join(Subscription, Subscription.plan_id == Plan.id)
        .where(Subscription.usuario_id == user.id, Subscription.estado == "activa")
        .order_by(Subscription.creado_en.desc())
        .limit(1)
    )
    if plan:
        return plan
    return db.scalar(select(Plan).where(Plan.codigo == "basico"))


def _limit(plan: Plan | None, attr: str, default: int) -> int:
    if plan is None:
        return default
    val = getattr(plan, attr, default)
    return val if val is not None else default


def _enforce(db: Session, user: User, model, attr: str, default: int, etiqueta: str) -> None:
    """Verifica que el usuario no supere el límite del plan para `model`."""
    limite = _limit(get_user_plan(db, user), attr, default)
    if limite < 0:
        return  # -1 = ilimitado
    actuales = db.scalar(
        select(func.count()).select_from(model).where(model.usuario_id == user.id)
    )
    if actuales >= limite:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            f"Tu plan permite hasta {limite} {etiqueta}. Mejora tu plan para agregar más.",
        )


def enforce_pet_limit(db: Session, user: User) -> None:
    _enforce(db, user, Pet, "max_mascotas", DEFAULT_LIMITS["max_mascotas"], "mascota(s)")


def enforce_device_limit(db: Session, user: User) -> None:
    # El collar mapea 1:1 con la mascota, así que se limita por max_mascotas.
    _enforce(db, user, Device, "max_mascotas", DEFAULT_LIMITS["max_mascotas"], "collar(es)")


def enforce_geofence_limit(db: Session, user: User) -> None:
    _enforce(db, user, Geofence, "max_geocercas", DEFAULT_LIMITS["max_geocercas"], "geocerca(s)")
