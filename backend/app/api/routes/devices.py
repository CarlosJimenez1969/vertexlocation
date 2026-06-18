"""
Pantalla unificada de dispositivos (rastreadores GPS).

Registrar un rastreador (en Traccar + DB) y asignarlo a una mascota O a un
vehículo. La asignación se refleja en Pet.dispositivo_id / Vehicle.dispositivo_id
(que el puente usa para mapear las posiciones al dueño correcto).
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_admin_user, get_current_user
from app.core.database import get_db
from app.models.device import Device
from app.models.pet import Pet
from app.models.user import User
from app.models.vehicle import Vehicle
from app.realtime.traccar_bridge import invalidate_owner_cache
from app.schemas.device import Asignacion, AssignRequest, DeviceFull, DeviceRegister, DeviceUpdate
from app.services.traccar import traccar

router = APIRouter(prefix="/devices", tags=["dispositivos"])


def _owned(db: Session, device_id: uuid.UUID, user_id: uuid.UUID) -> Device:
    d = db.get(Device, device_id)
    if not d or d.usuario_id != user_id:
        raise HTTPException(404, "Dispositivo no encontrado")
    return d


def _to_full(db: Session, d: Device) -> DeviceFull:
    """DeviceFull con su asignación actual (mascota o vehículo)."""
    asign = None
    p = db.scalar(select(Pet).where(Pet.dispositivo_id == d.id))
    if p:
        asign = Asignacion(tipo="mascota", id=p.id, nombre=p.nombre)
    else:
        v = db.scalar(select(Vehicle).where(Vehicle.dispositivo_id == d.id))
        if v:
            asign = Asignacion(tipo="vehiculo", id=v.id, nombre=v.alias)
    out = DeviceFull.model_validate(d)
    out.asignado = asign
    return out


def _desasignar_todo(db: Session, device_id: uuid.UUID) -> None:
    """Quita este dispositivo de cualquier mascota o vehículo que lo tenga."""
    for p in db.scalars(select(Pet).where(Pet.dispositivo_id == device_id)).all():
        p.dispositivo_id = None
    for v in db.scalars(select(Vehicle).where(Vehicle.dispositivo_id == device_id)).all():
        v.dispositivo_id = None
    db.flush()


@router.get("", response_model=list[DeviceFull])
def listar(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    devices = db.scalars(select(Device).where(Device.usuario_id == current.id)).all()
    pets = {
        p.dispositivo_id: p for p in
        db.scalars(select(Pet).where(Pet.usuario_id == current.id, Pet.dispositivo_id.isnot(None))).all()
    }
    vehs = {
        v.dispositivo_id: v for v in
        db.scalars(select(Vehicle).where(Vehicle.usuario_id == current.id, Vehicle.dispositivo_id.isnot(None))).all()
    }
    out: list[DeviceFull] = []
    for d in devices:
        asign = None
        if d.id in pets:
            asign = Asignacion(tipo="mascota", id=pets[d.id].id, nombre=pets[d.id].nombre)
        elif d.id in vehs:
            asign = Asignacion(tipo="vehiculo", id=vehs[d.id].id, nombre=vehs[d.id].alias)
        out.append(DeviceFull(
            id=d.id, imei=d.imei, traccar_device_id=d.traccar_device_id, modelo=d.modelo,
            nombre=d.nombre, sim_operador=d.sim_operador, bateria=d.bateria, online=d.online,
            ultima_conexion=d.ultima_conexion, asignado=asign,
        ))
    return out


@router.post("", response_model=DeviceFull, status_code=201)
def registrar(payload: DeviceRegister, current: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    if db.scalar(select(Device).where(Device.imei == payload.imei)):
        raise HTTPException(400, "El IMEI/ID ya está registrado")
    device = Device(
        usuario_id=current.id,
        imei=payload.imei,
        nombre=payload.nombre or f"Rastreador {payload.imei[-4:]}",
        sim_operador=payload.sim_operador,
    )
    # Registrar en Traccar (no bloqueante si Traccar está caído)
    try:
        t = traccar.create_device(name=device.nombre, unique_id=payload.imei)
        device.traccar_device_id = t.get("id")
    except Exception as e:
        print(f"[Traccar] No se pudo registrar el dispositivo: {e}")
    db.add(device)
    db.commit()
    db.refresh(device)
    invalidate_owner_cache()
    return DeviceFull.model_validate(device)


@router.patch("/{device_id}", response_model=DeviceFull)
def actualizar(device_id: uuid.UUID, payload: DeviceUpdate,
               current: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    """Corrige los datos del dispositivo (IMEI/ID, nombre, operador) y los
    sincroniza con Traccar."""
    device = _owned(db, device_id, current.id)
    data = payload.model_dump(exclude_none=True)
    nuevo_imei = data.get("imei")
    if nuevo_imei and nuevo_imei != device.imei:
        if db.scalar(select(Device).where(Device.imei == nuevo_imei, Device.id != device.id)):
            raise HTTPException(400, "Ese IMEI/ID ya está registrado en otro dispositivo")
    for k, v in data.items():
        setattr(device, k, v)
    if device.traccar_device_id:
        try:
            traccar.update_device(device.traccar_device_id, name=device.nombre, unique_id=device.imei)
        except Exception as e:
            print(f"[Traccar] No se pudo actualizar el dispositivo: {e}")
    db.commit()
    db.refresh(device)
    invalidate_owner_cache()
    return _to_full(db, device)


@router.post("/{device_id}/assign", response_model=DeviceFull)
def asignar(device_id: uuid.UUID, payload: AssignRequest,
            current: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    device = _owned(db, device_id, current.id)
    _desasignar_todo(db, device.id)  # un dispositivo solo puede estar en un activo

    if payload.tipo == "mascota":
        target = db.get(Pet, payload.target_id)
    elif payload.tipo == "vehiculo":
        target = db.get(Vehicle, payload.target_id)
    else:
        raise HTTPException(400, "tipo debe ser 'mascota' o 'vehiculo'")
    if not target or target.usuario_id != current.id:
        raise HTTPException(404, f"{payload.tipo.capitalize()} no encontrado")

    target.dispositivo_id = device.id
    db.commit()
    invalidate_owner_cache()

    nombre = target.nombre if payload.tipo == "mascota" else target.alias
    out = DeviceFull.model_validate(device)
    out.asignado = Asignacion(tipo=payload.tipo, id=target.id, nombre=nombre)
    return out


@router.post("/{device_id}/unassign", response_model=DeviceFull)
def desasignar(device_id: uuid.UUID, current: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    device = _owned(db, device_id, current.id)
    _desasignar_todo(db, device.id)
    db.commit()
    invalidate_owner_cache()
    return DeviceFull.model_validate(device)


@router.delete("/{device_id}", status_code=204)
def eliminar(device_id: uuid.UUID, current: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    device = _owned(db, device_id, current.id)
    _desasignar_todo(db, device.id)
    if device.traccar_device_id:
        try:
            traccar.delete_device(device.traccar_device_id)
        except Exception as e:
            print(f"[Traccar] No se pudo borrar el dispositivo: {e}")
    db.delete(device)
    db.commit()
    invalidate_owner_cache()
