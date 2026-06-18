"""
Panel de administración (solo rol admin).

El administrador gestiona los datos de TODOS los clientes: usuarios, mascotas,
vehículos y dispositivos, asignándolos al usuario correspondiente. Todas las
rutas requieren rol admin (dependencia a nivel de router).
"""
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_admin_user
from app.core.config import settings
from app.core.database import get_db
from app.core.security import hash_password
from app.models.device import Device
from app.models.password_reset import PasswordReset
from app.models.pet import Pet
from app.models.user import User
from app.models.vehicle import Vehicle
from app.realtime.traccar_bridge import invalidate_owner_cache
from app.schemas.admin import UserAdminOut, UserCreate, UserUpdate
from app.schemas.device import DeviceRegister, DeviceUpdate
from app.schemas.pet import PetCreate, PetOut, PetUpdate
from app.schemas.vehicle import VehicleCreate, VehicleOut, VehicleUpdate
from app.services.email_service import send_invitation_email
from app.services.traccar import traccar

INVITE_EXPIRE_HOURS = 48

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(get_admin_user)])


# ==================== USUARIOS ====================
@router.get("/users", response_model=list[UserAdminOut])
def listar_usuarios(db: Session = Depends(get_db)):
    return db.scalars(select(User).order_by(User.creado_en.desc())).all()


@router.post("/users", response_model=UserAdminOut, status_code=201)
def crear_usuario(payload: UserCreate, db: Session = Depends(get_db)):
    """Crea el usuario SIN contraseña y le envía un correo de invitación
    para que la defina él mismo (link al /reset-password)."""
    if db.scalar(select(User).where(User.email == payload.email)):
        raise HTTPException(400, "El email ya está registrado")
    # Contraseña aleatoria no usable: el usuario la define vía el correo.
    u = User(
        nombre=payload.nombre, email=payload.email,
        password_hash=hash_password(secrets.token_urlsafe(24)),
        telefono=payload.telefono, ciudad=payload.ciudad or "Quito",
        rol=payload.rol or "cliente",
    )
    db.add(u); db.commit(); db.refresh(u)

    # Token de invitación (mismo mecanismo que el reset de contraseña).
    raw = secrets.token_urlsafe(32)
    db.add(PasswordReset(
        usuario_id=u.id,
        token_hash=hashlib.sha256(raw.encode()).hexdigest(),
        expira_en=datetime.now(timezone.utc) + timedelta(hours=INVITE_EXPIRE_HOURS),
    ))
    db.commit()
    try:
        send_invitation_email(u.email, u.nombre, raw)
    except Exception as e:
        print(f"[Invitación] Error enviando el correo a {u.email}: {e}")
    return u


@router.patch("/users/{user_id}", response_model=UserAdminOut)
def actualizar_usuario(user_id: uuid.UUID, payload: UserUpdate, db: Session = Depends(get_db)):
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(404, "Usuario no encontrado")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(u, k, v)
    db.commit(); db.refresh(u)
    return u


def _user(db: Session, user_id: uuid.UUID) -> User:
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(404, "Usuario no encontrado")
    return u


# ==================== MASCOTAS ====================
def _pet_dict(p: Pet, owner: User | None) -> dict:
    return {
        "id": str(p.id), "nombre": p.nombre, "especie": p.especie, "raza": p.raza,
        "sexo": p.sexo, "edad_meses": p.edad_meses, "peso_kg": float(p.peso_kg) if p.peso_kg else None,
        "foto_url": p.foto_url,
        "dispositivo_id": str(p.dispositivo_id) if p.dispositivo_id else None,
        "usuario_id": str(p.usuario_id),
        "dueno": {"id": str(owner.id), "nombre": owner.nombre, "email": owner.email} if owner else None,
    }


@router.get("/pets")
def listar_mascotas(db: Session = Depends(get_db)):
    pets = db.scalars(select(Pet)).all()
    users = {u.id: u for u in db.scalars(select(User)).all()}
    return [_pet_dict(p, users.get(p.usuario_id)) for p in pets]


@router.post("/pets", response_model=PetOut, status_code=201)
def crear_mascota(payload: PetCreate, usuario_id: uuid.UUID = Query(...), db: Session = Depends(get_db)):
    _user(db, usuario_id)
    pet = Pet(usuario_id=usuario_id, **payload.model_dump(exclude_none=True))
    db.add(pet); db.commit(); db.refresh(pet)
    invalidate_owner_cache()
    return pet


@router.patch("/pets/{pet_id}", response_model=PetOut)
def actualizar_mascota(pet_id: uuid.UUID, payload: PetUpdate, db: Session = Depends(get_db)):
    pet = db.get(Pet, pet_id)
    if not pet:
        raise HTTPException(404, "Mascota no encontrada")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(pet, k, v)
    db.commit(); db.refresh(pet)
    invalidate_owner_cache()
    return pet


@router.delete("/pets/{pet_id}", status_code=204)
def eliminar_mascota(pet_id: uuid.UUID, db: Session = Depends(get_db)):
    pet = db.get(Pet, pet_id)
    if not pet:
        raise HTTPException(404, "Mascota no encontrada")
    db.delete(pet); db.commit()
    invalidate_owner_cache()


# ==================== VEHICULOS ====================
def _veh_dict(v: Vehicle, owner: User | None) -> dict:
    return {
        "id": str(v.id), "alias": v.alias, "placa": v.placa, "marca": v.marca, "modelo": v.modelo,
        "anio": v.anio, "color": v.color, "tipo": v.tipo, "foto_url": v.foto_url,
        "tiene_inmovilizador": v.tiene_inmovilizador,
        "dispositivo_id": str(v.dispositivo_id) if v.dispositivo_id else None,
        "usuario_id": str(v.usuario_id),
        "dueno": {"id": str(owner.id), "nombre": owner.nombre, "email": owner.email} if owner else None,
    }


@router.get("/vehicles")
def listar_vehiculos(db: Session = Depends(get_db)):
    vehs = db.scalars(select(Vehicle)).all()
    users = {u.id: u for u in db.scalars(select(User)).all()}
    return [_veh_dict(v, users.get(v.usuario_id)) for v in vehs]


@router.post("/vehicles", response_model=VehicleOut, status_code=201)
def crear_vehiculo(payload: VehicleCreate, usuario_id: uuid.UUID = Query(...), db: Session = Depends(get_db)):
    _user(db, usuario_id)
    data = payload.model_dump(exclude_none=True)
    data.pop("imei", None)
    data.pop("sim_operador", None)
    veh = Vehicle(usuario_id=usuario_id, **data)
    db.add(veh); db.commit(); db.refresh(veh)
    invalidate_owner_cache()
    return veh


@router.patch("/vehicles/{veh_id}", response_model=VehicleOut)
def actualizar_vehiculo(veh_id: uuid.UUID, payload: VehicleUpdate, db: Session = Depends(get_db)):
    veh = db.get(Vehicle, veh_id)
    if not veh:
        raise HTTPException(404, "Vehículo no encontrado")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(veh, k, v)
    db.commit(); db.refresh(veh)
    invalidate_owner_cache()
    return veh


@router.delete("/vehicles/{veh_id}", status_code=204)
def eliminar_vehiculo(veh_id: uuid.UUID, db: Session = Depends(get_db)):
    veh = db.get(Vehicle, veh_id)
    if not veh:
        raise HTTPException(404, "Vehículo no encontrado")
    db.delete(veh); db.commit()
    invalidate_owner_cache()


# ==================== DISPOSITIVOS ====================
def _dev_dict(d: Device, owner: User | None, asign: dict | None) -> dict:
    return {
        "id": str(d.id), "imei": d.imei, "traccar_device_id": d.traccar_device_id,
        "modelo": d.modelo, "nombre": d.nombre, "sim_operador": d.sim_operador,
        "bateria": d.bateria, "online": d.online, "ultima_conexion": d.ultima_conexion,
        "usuario_id": str(d.usuario_id) if d.usuario_id else None,
        "dueno": {"id": str(owner.id), "nombre": owner.nombre, "email": owner.email} if owner else None,
        "asignado": asign,
    }


@router.get("/devices")
def listar_dispositivos(db: Session = Depends(get_db)):
    devices = db.scalars(select(Device)).all()
    users = {u.id: u for u in db.scalars(select(User)).all()}
    pets = {p.dispositivo_id: p for p in db.scalars(select(Pet).where(Pet.dispositivo_id.isnot(None))).all()}
    vehs = {v.dispositivo_id: v for v in db.scalars(select(Vehicle).where(Vehicle.dispositivo_id.isnot(None))).all()}
    out = []
    for d in devices:
        asign = None
        if d.id in pets:
            asign = {"tipo": "mascota", "id": str(pets[d.id].id), "nombre": pets[d.id].nombre}
        elif d.id in vehs:
            asign = {"tipo": "vehiculo", "id": str(vehs[d.id].id), "nombre": vehs[d.id].alias}
        out.append(_dev_dict(d, users.get(d.usuario_id), asign))
    return out


@router.post("/devices", status_code=201)
def registrar_dispositivo(payload: DeviceRegister, db: Session = Depends(get_db)):
    # Sin dueño: el dispositivo hereda el dueño de la mascota/vehículo al asignarse.
    if db.scalar(select(Device).where(Device.imei == payload.imei)):
        raise HTTPException(400, "El IMEI/ID ya está registrado")
    device = Device(
        imei=payload.imei,
        nombre=payload.nombre or f"Rastreador {payload.imei[-4:]}",
        sim_operador=payload.sim_operador,
    )
    try:
        t = traccar.create_device(name=device.nombre, unique_id=payload.imei)
        device.traccar_device_id = t.get("id")
    except Exception as e:
        print(f"[Traccar] No se pudo registrar el dispositivo: {e}")
    db.add(device); db.commit(); db.refresh(device)
    invalidate_owner_cache()
    return _dev_dict(device, None, None)


@router.patch("/devices/{device_id}")
def actualizar_dispositivo(device_id: uuid.UUID, payload: DeviceUpdate, db: Session = Depends(get_db)):
    device = db.get(Device, device_id)
    if not device:
        raise HTTPException(404, "Dispositivo no encontrado")
    data = payload.model_dump(exclude_none=True)
    nuevo = data.get("imei")
    if nuevo and nuevo != device.imei and db.scalar(select(Device).where(Device.imei == nuevo, Device.id != device.id)):
        raise HTTPException(400, "Ese IMEI/ID ya está registrado en otro dispositivo")
    for k, v in data.items():
        setattr(device, k, v)
    if device.traccar_device_id:
        try:
            traccar.update_device(device.traccar_device_id, name=device.nombre, unique_id=device.imei)
        except Exception as e:
            print(f"[Traccar] No se pudo actualizar: {e}")
    db.commit(); db.refresh(device)
    invalidate_owner_cache()
    return _dev_dict(device, db.get(User, device.usuario_id), None)


@router.post("/devices/{device_id}/assign")
def asignar_dispositivo(device_id: uuid.UUID, tipo: str = Query(...), target_id: uuid.UUID = Query(...),
                        db: Session = Depends(get_db)):
    device = db.get(Device, device_id)
    if not device:
        raise HTTPException(404, "Dispositivo no encontrado")
    # quitar de cualquier activo
    for p in db.scalars(select(Pet).where(Pet.dispositivo_id == device.id)).all():
        p.dispositivo_id = None
    for v in db.scalars(select(Vehicle).where(Vehicle.dispositivo_id == device.id)).all():
        v.dispositivo_id = None
    db.flush()
    target = db.get(Pet, target_id) if tipo == "mascota" else db.get(Vehicle, target_id) if tipo == "vehiculo" else None
    if not target:
        raise HTTPException(404, "Destino no encontrado")
    target.dispositivo_id = device.id
    device.usuario_id = target.usuario_id  # el dispositivo hereda el dueño del activo
    db.commit()
    invalidate_owner_cache()
    nombre = target.nombre if tipo == "mascota" else target.alias
    return _dev_dict(device, db.get(User, device.usuario_id),
                     {"tipo": tipo, "id": str(target.id), "nombre": nombre})


@router.post("/devices/{device_id}/unassign")
def desasignar_dispositivo(device_id: uuid.UUID, db: Session = Depends(get_db)):
    device = db.get(Device, device_id)
    if not device:
        raise HTTPException(404, "Dispositivo no encontrado")
    for p in db.scalars(select(Pet).where(Pet.dispositivo_id == device.id)).all():
        p.dispositivo_id = None
    for v in db.scalars(select(Vehicle).where(Vehicle.dispositivo_id == device.id)).all():
        v.dispositivo_id = None
    device.usuario_id = None  # al quedar sin asignar, pierde el dueño
    db.commit()
    invalidate_owner_cache()
    return _dev_dict(device, None, None)


@router.delete("/devices/{device_id}", status_code=204)
def eliminar_dispositivo(device_id: uuid.UUID, db: Session = Depends(get_db)):
    device = db.get(Device, device_id)
    if not device:
        raise HTTPException(404, "Dispositivo no encontrado")
    for p in db.scalars(select(Pet).where(Pet.dispositivo_id == device.id)).all():
        p.dispositivo_id = None
    for v in db.scalars(select(Vehicle).where(Vehicle.dispositivo_id == device.id)).all():
        v.dispositivo_id = None
    if device.traccar_device_id:
        try:
            traccar.delete_device(device.traccar_device_id)
        except Exception as e:
            print(f"[Traccar] No se pudo borrar: {e}")
    db.delete(device); db.commit()
    invalidate_owner_cache()
