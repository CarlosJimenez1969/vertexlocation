"""Enlaces públicos para compartir la ubicación en vivo de un activo (sin login)."""
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.device import Device
from app.models.pet import Pet
from app.models.position import Position
from app.models.share_link import ShareLink
from app.models.user import User
from app.models.vehicle import Vehicle
from app.services.traccar import normalize_position, traccar

router = APIRouter(prefix="/share", tags=["compartir"])

EMOJI_VEH = {"auto": "🚗", "camioneta": "🛻", "moto": "🏍️", "otro": "🚙"}
EMOJI_PET = {"perro": "🐶", "gato": "🐱", "otro": "🐾"}
MAX_HORAS = 168  # 7 días


class ShareCreate(BaseModel):
    tipo: str                       # mascota | vehiculo
    target_id: uuid.UUID
    horas: int = Field(default=24, ge=1, le=MAX_HORAS)


def _asset(db: Session, tipo: str, target_id):
    if tipo == "mascota":
        return db.get(Pet, target_id)
    if tipo == "vehiculo":
        return db.get(Vehicle, target_id)
    return None


def _latest_position(db: Session, dispositivo_id):
    """Última posición (intenta Traccar en vivo, cae a la BD)."""
    if not dispositivo_id:
        return None
    device = db.get(Device, dispositivo_id)
    if device and device.traccar_device_id:
        try:
            live = traccar.get_latest_positions([device.traccar_device_id])
            if live:
                return normalize_position(live[0])
        except Exception:
            pass
    p = db.scalar(
        select(Position).where(Position.dispositivo_id == dispositivo_id)
        .order_by(Position.fija_en.desc()).limit(1)
    )
    if not p:
        return None
    return {"latitud": p.latitud, "longitud": p.longitud, "velocidad": p.velocidad,
            "rumbo": p.rumbo, "bateria": p.bateria, "fija_en": p.fija_en}


@router.post("", status_code=201)
def crear_enlace(payload: ShareCreate, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.tipo not in ("mascota", "vehiculo"):
        raise HTTPException(400, "tipo inválido")
    asset = _asset(db, payload.tipo, payload.target_id)
    if not asset:
        raise HTTPException(404, "Activo no encontrado")
    if str(asset.usuario_id) != str(current.id) and current.rol != "admin":
        raise HTTPException(403, "No es tu activo")
    link = ShareLink(
        token=secrets.token_urlsafe(9),
        tipo=payload.tipo,
        target_id=payload.target_id,
        usuario_id=current.id,   # el creador del enlace (lo ve en /share/me)
        expira_en=datetime.now(timezone.utc) + timedelta(hours=payload.horas),
    )
    db.add(link); db.commit(); db.refresh(link)
    return {"id": str(link.id), "token": link.token, "expira_en": link.expira_en}


@router.get("/me")
def mis_enlaces(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ahora = datetime.now(timezone.utc)
    rows = db.scalars(
        select(ShareLink).where(ShareLink.usuario_id == current.id, ShareLink.activo.is_(True))
        .order_by(ShareLink.creado_en.desc())
    ).all()
    return [{"id": str(r.id), "token": r.token, "tipo": r.tipo,
             "target_id": str(r.target_id), "expira_en": r.expira_en,
             "vigente": r.expira_en > ahora} for r in rows]


@router.delete("/{link_id}", status_code=204)
def revocar(link_id: uuid.UUID, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    link = db.get(ShareLink, link_id)
    if not link or (str(link.usuario_id) != str(current.id) and current.rol != "admin"):
        raise HTTPException(404, "Enlace no encontrado")
    link.activo = False
    db.commit()


@router.get("/{token}")
def ver_publico(token: str, db: Session = Depends(get_db)):
    """PÚBLICO (sin login): ubicación en vivo del activo compartido."""
    link = db.scalar(select(ShareLink).where(ShareLink.token == token, ShareLink.activo.is_(True)))
    if not link:
        raise HTTPException(404, "Enlace no válido")
    if link.expira_en <= datetime.now(timezone.utc):
        raise HTTPException(410, "El enlace expiró")
    asset = _asset(db, link.tipo, link.target_id)
    if not asset:
        raise HTTPException(404, "Activo no disponible")
    if link.tipo == "mascota":
        nombre, emoji = asset.nombre, EMOJI_PET.get(asset.especie, "🐾")
    else:
        nombre, emoji = asset.alias, EMOJI_VEH.get(asset.tipo, "🚗")
    pos = _latest_position(db, asset.dispositivo_id)
    return {
        "nombre": nombre, "tipo": link.tipo, "emoji": emoji,
        "expira_en": link.expira_en,
        "posicion": ({
            "latitud": pos["latitud"], "longitud": pos["longitud"],
            "velocidad": pos["velocidad"], "fija_en": pos["fija_en"],
        } if pos else None),
    }
