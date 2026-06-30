"""Mantenimientos preventivos de vehículos (recordatorios por fecha/km)."""
import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.maintenance import Maintenance
from app.models.user import User
from app.models.vehicle import Vehicle

router = APIRouter(prefix="/maintenance", tags=["mantenimiento"])

DIAS_PROXIMO = 15     # "próximo" si faltan <= 15 días
KM_PROXIMO = 500      # "próximo" si faltan <= 500 km
_ORDEN = {"vencido": 3, "proximo": 2, "vigente": 1}


class MaintenanceIn(BaseModel):
    tipo: str = Field(min_length=2, max_length=80)
    notas: str | None = None
    fecha_proxima: date | None = None
    km_proximo: int | None = Field(default=None, ge=0)
    intervalo_dias: int | None = Field(default=None, ge=1)
    intervalo_km: int | None = Field(default=None, ge=1)


class MaintenanceCreate(MaintenanceIn):
    vehiculo_id: uuid.UUID


def _vehiculo(db: Session, veh_id, current: User) -> Vehicle:
    v = db.get(Vehicle, veh_id)
    if not v or (v.usuario_id != current.id and current.rol != "admin"):
        raise HTTPException(404, "Vehículo no encontrado")
    return v


def _maint(db: Session, mid, current: User) -> tuple[Maintenance, Vehicle]:
    m = db.get(Maintenance, mid)
    if not m:
        raise HTTPException(404, "Mantenimiento no encontrado")
    v = _vehiculo(db, m.vehiculo_id, current)
    return m, v


def _estado(m: Maintenance, km_actual: int | None) -> str:
    if m.realizado:
        return "realizado"
    estados = []
    if m.fecha_proxima:
        d = (m.fecha_proxima - date.today()).days
        estados.append("vencido" if d < 0 else "proximo" if d <= DIAS_PROXIMO else "vigente")
    if m.km_proximo is not None and km_actual is not None:
        k = m.km_proximo - km_actual
        estados.append("vencido" if k <= 0 else "proximo" if k <= KM_PROXIMO else "vigente")
    return max(estados, key=lambda e: _ORDEN[e]) if estados else "vigente"


def _dict(m: Maintenance, km_actual: int | None) -> dict:
    dias = (m.fecha_proxima - date.today()).days if m.fecha_proxima else None
    kms = (m.km_proximo - km_actual) if (m.km_proximo is not None and km_actual is not None) else None
    return {
        "id": str(m.id), "vehiculo_id": str(m.vehiculo_id), "tipo": m.tipo, "notas": m.notas,
        "fecha_proxima": m.fecha_proxima, "km_proximo": m.km_proximo,
        "intervalo_dias": m.intervalo_dias, "intervalo_km": m.intervalo_km,
        "realizado": m.realizado, "estado": _estado(m, km_actual),
        "dias_restantes": dias, "km_restantes": kms,
    }


@router.get("")
def listar(vehiculo_id: uuid.UUID = Query(...), current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    v = _vehiculo(db, vehiculo_id, current)
    rows = db.scalars(
        select(Maintenance).where(Maintenance.vehiculo_id == v.id).order_by(Maintenance.creado_en.desc())
    ).all()
    return [_dict(m, v.km_actual) for m in rows]


@router.post("", status_code=201)
def crear(payload: MaintenanceCreate, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    v = _vehiculo(db, payload.vehiculo_id, current)
    if payload.fecha_proxima is None and payload.km_proximo is None:
        raise HTTPException(400, "Indica una fecha o un kilometraje de vencimiento.")
    m = Maintenance(vehiculo_id=v.id, **payload.model_dump(exclude={"vehiculo_id"}))
    db.add(m); db.commit(); db.refresh(m)
    return _dict(m, v.km_actual)


@router.patch("/{mid}")
def actualizar(mid: uuid.UUID, payload: MaintenanceIn, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    m, v = _maint(db, mid, current)
    for k, val in payload.model_dump(exclude_unset=True).items():
        setattr(m, k, val)
    db.commit(); db.refresh(m)
    return _dict(m, v.km_actual)


@router.post("/{mid}/done")
def marcar_realizado(mid: uuid.UUID, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Marca como hecho. Si tiene recurrencia, lo reprograma; si no, lo cierra."""
    m, v = _maint(db, mid, current)
    if m.intervalo_dias or m.intervalo_km:
        if m.intervalo_dias:
            m.fecha_proxima = date.today() + timedelta(days=m.intervalo_dias)
        if m.intervalo_km and v.km_actual is not None:
            m.km_proximo = v.km_actual + m.intervalo_km
        m.realizado = False   # recurrente: sigue activo, reprogramado
    else:
        m.realizado = True
    db.commit(); db.refresh(m)
    return _dict(m, v.km_actual)


@router.delete("/{mid}", status_code=204)
def eliminar(mid: uuid.UUID, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    m, _ = _maint(db, mid, current)
    db.delete(m); db.commit()
