"""Rutas de geocercas (ilimitadas en planes Estándar/Premium)."""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.geofence import Geofence
from app.models.user import User
from app.schemas.tracking import GeofenceCreate, GeofenceOut
from app.services.plan_service import enforce_geofence_limit

router = APIRouter(prefix="/geofences", tags=["geocercas"])


@router.post("", response_model=GeofenceOut, status_code=201)
def crear_geocerca(
    payload: GeofenceCreate,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    enforce_geofence_limit(db, current)
    if payload.tipo == "circular" and (
        payload.centro_lat is None or payload.centro_lng is None or payload.radio_m is None
    ):
        raise HTTPException(400, "Geocerca circular requiere centro_lat, centro_lng y radio_m")
    if payload.tipo == "poligono" and not payload.poligono:
        raise HTTPException(400, "Geocerca de polígono requiere lista de puntos")

    data = payload.model_dump()
    if data.get("poligono"):
        data["poligono"] = [p.model_dump() if hasattr(p, "model_dump") else p for p in payload.poligono]

    gf = Geofence(usuario_id=current.id, **data)
    db.add(gf)
    db.commit()
    db.refresh(gf)
    return gf


@router.get("", response_model=list[GeofenceOut])
def listar_geocercas(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.scalars(select(Geofence).where(Geofence.usuario_id == current.id)).all()


@router.delete("/{gf_id}", status_code=204)
def eliminar_geocerca(gf_id: uuid.UUID, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    gf = db.get(Geofence, gf_id)
    if not gf or gf.usuario_id != current.id:
        raise HTTPException(404, "Geocerca no encontrada")
    db.delete(gf)
    db.commit()
