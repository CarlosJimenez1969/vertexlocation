"""Rutas de mascotas y dispositivos (collar C059)."""
import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_admin_user, get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.device import Device
from app.models.pet import Pet
from app.models.user import User
from app.realtime.traccar_bridge import invalidate_owner_cache
from app.schemas.pet import (
    DeviceCreate, DeviceOut, PetCreate, PetOut, PetUpdate,
)
from app.services.plan_service import enforce_device_limit, enforce_pet_limit
from app.services.traccar import traccar

router = APIRouter(prefix="/pets", tags=["mascotas"])


# ---------------- Dispositivos (collar C059) ----------------
@router.post("/devices", response_model=DeviceOut, status_code=201)
def registrar_dispositivo(
    payload: DeviceCreate,
    current: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    enforce_device_limit(db, current)
    if db.scalar(select(Device).where(Device.imei == payload.imei)):
        raise HTTPException(400, "El IMEI ya está registrado")

    device = Device(
        usuario_id=current.id,
        imei=payload.imei,
        nombre=payload.nombre or f"Collar {payload.imei[-4:]}",
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
    invalidate_owner_cache()  # el bridge debe ver el nuevo collar de inmediato
    return device


@router.get("/devices", response_model=list[DeviceOut])
def listar_dispositivos(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.scalars(select(Device).where(Device.usuario_id == current.id)).all()


# ---------------- Mascotas ----------------
@router.post("", response_model=PetOut, status_code=201)
def crear_mascota(
    payload: PetCreate,
    current: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    enforce_pet_limit(db, current)
    pet = Pet(usuario_id=current.id, **payload.model_dump(exclude_none=True))
    db.add(pet)
    db.commit()
    db.refresh(pet)
    invalidate_owner_cache()  # la mascota puede traer dispositivo asignado
    return pet


@router.get("", response_model=list[PetOut])
def listar_mascotas(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.scalars(select(Pet).where(Pet.usuario_id == current.id)).all()


@router.get("/{pet_id}", response_model=PetOut)
def obtener_mascota(pet_id: uuid.UUID, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    pet = _get_owned_pet(db, pet_id, current.id)
    return pet


@router.patch("/{pet_id}", response_model=PetOut)
def actualizar_mascota(
    pet_id: uuid.UUID, payload: PetUpdate,
    current: User = Depends(get_admin_user), db: Session = Depends(get_db),
):
    pet = _get_owned_pet(db, pet_id, current.id)
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(pet, k, v)
    db.commit()
    db.refresh(pet)
    invalidate_owner_cache()  # pudo cambiar el dispositivo asignado
    return pet


@router.delete("/{pet_id}", status_code=204)
def eliminar_mascota(pet_id: uuid.UUID, current: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    pet = _get_owned_pet(db, pet_id, current.id)
    db.delete(pet)
    db.commit()
    invalidate_owner_cache()


# Tipos de imagen permitidos -> extensión
ALLOWED_IMG = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


@router.post("/{pet_id}/photo", response_model=PetOut)
def subir_foto(
    pet_id: uuid.UUID,
    file: UploadFile = File(...),
    current: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Sube/reemplaza la foto de la mascota (JPG, PNG o WEBP). Solo admin."""
    pet = db.get(Pet, pet_id)
    if not pet:
        raise HTTPException(404, "Mascota no encontrada")

    ext = ALLOWED_IMG.get(file.content_type)
    if not ext:
        raise HTTPException(400, "Formato no permitido. Usa JPG, PNG o WEBP.")

    contenido = file.file.read()
    if len(contenido) > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(400, f"La imagen supera el máximo de {settings.MAX_UPLOAD_MB} MB.")

    pets_dir = os.path.join(settings.UPLOAD_DIR, "pets")
    os.makedirs(pets_dir, exist_ok=True)
    # Limpia versiones previas con otra extensión (evita huérfanos).
    for prev_ext in set(ALLOWED_IMG.values()):
        prev = os.path.join(pets_dir, f"{pet_id}{prev_ext}")
        if prev_ext != ext and os.path.exists(prev):
            os.remove(prev)

    filename = f"{pet_id}{ext}"
    with open(os.path.join(pets_dir, filename), "wb") as f:
        f.write(contenido)

    pet.foto_url = f"/uploads/pets/{filename}"
    db.commit()
    db.refresh(pet)
    return pet


def _get_owned_pet(db: Session, pet_id: uuid.UUID, user_id: uuid.UUID) -> Pet:
    pet = db.get(Pet, pet_id)
    if not pet or pet.usuario_id != user_id:
        raise HTTPException(404, "Mascota no encontrada")
    return pet
