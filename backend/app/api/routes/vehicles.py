"""Rutas de vehículos (plataforma multi-activo). Reutilizan Dispositivo/Posiciones."""
import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from app.api.deps import get_admin_user, get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.security import verify_password
from app.models.device import Device
from app.models.position import Position
from app.models.user import User
from app.models.vehicle import Vehicle
from app.realtime.traccar_bridge import invalidate_owner_cache
from app.schemas.tracking import PositionOut
from app.schemas.vehicle import EngineAction, VehicleCreate, VehicleOut, VehicleUpdate
from app.services.alerts import create_alert
from app.services.traccar import normalize_position, traccar

router = APIRouter(prefix="/vehicles", tags=["vehiculos"])

ALLOWED_IMG = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


# ---------------- CRUD ----------------
@router.post("", response_model=VehicleOut, status_code=201)
def crear_vehiculo(
    payload: VehicleCreate,
    current: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    data = payload.model_dump(exclude_none=True)
    imei = data.pop("imei", None)
    sim_operador = data.pop("sim_operador", None)

    vehicle = Vehicle(usuario_id=current.id, **data)

    # Registro opcional del rastreador (en Traccar + DB), igual que en mascotas.
    if imei:
        if db.scalar(select(Device).where(Device.imei == imei)):
            raise HTTPException(400, "El IMEI/ID ya está registrado")
        device = Device(
            usuario_id=current.id,
            imei=imei,
            nombre=payload.alias,
            sim_operador=sim_operador,
        )
        try:
            t = traccar.create_device(name=device.nombre, unique_id=imei)
            device.traccar_device_id = t.get("id")
        except Exception as e:
            print(f"[Traccar] No se pudo registrar el rastreador del vehículo: {e}")
        db.add(device)
        db.flush()  # obtener device.id
        vehicle.dispositivo_id = device.id

    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    invalidate_owner_cache()
    return vehicle


@router.get("", response_model=list[VehicleOut])
def listar_vehiculos(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.scalars(select(Vehicle).where(Vehicle.usuario_id == current.id)).all()


@router.get("/{veh_id}", response_model=VehicleOut)
def obtener_vehiculo(veh_id: uuid.UUID, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _owned(db, veh_id, current.id)


@router.patch("/{veh_id}", response_model=VehicleOut)
def actualizar_vehiculo(
    veh_id: uuid.UUID, payload: VehicleUpdate,
    current: User = Depends(get_admin_user), db: Session = Depends(get_db),
):
    v = db.get(Vehicle, veh_id)
    if not v:
        raise HTTPException(404, "Vehículo no encontrado")
    for k, val in payload.model_dump(exclude_none=True).items():
        setattr(v, k, val)
    db.commit()
    db.refresh(v)
    invalidate_owner_cache()
    return v


@router.delete("/{veh_id}", status_code=204)
def eliminar_vehiculo(veh_id: uuid.UUID, current: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    v = db.get(Vehicle, veh_id)
    if not v:
        raise HTTPException(404, "Vehículo no encontrado")
    db.delete(v)
    db.commit()
    invalidate_owner_cache()


# ---------------- Anti-robo (modo armado) ----------------
def _ultima_lat_lng(db: Session, v: Vehicle) -> tuple[float | None, float | None]:
    """Última posición conocida del vehículo (Traccar en vivo o DB)."""
    device = db.get(Device, v.dispositivo_id) if v.dispositivo_id else None
    if device and device.traccar_device_id:
        try:
            live = traccar.get_latest_positions([device.traccar_device_id])
            if live:
                norm = normalize_position(live[0])
                return norm["latitud"], norm["longitud"]
        except Exception:
            pass
    pos = db.scalar(
        select(Position).where(Position.dispositivo_id == v.dispositivo_id)
        .order_by(Position.fija_en.desc()).limit(1)
    )
    return (pos.latitud, pos.longitud) if pos else (None, None)


@router.post("/{veh_id}/arm", response_model=VehicleOut)
def armar(veh_id: uuid.UUID, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Arma el vehículo (modo estacionado): registra su posición de referencia."""
    v = _owned(db, veh_id, current.id)
    if not v.dispositivo_id:
        raise HTTPException(400, "El vehículo no tiene rastreador asignado")
    lat, lng = _ultima_lat_lng(db, v)
    v.armado = True
    v.armado_en = datetime.now(timezone.utc)
    v.armado_lat = lat
    v.armado_lng = lng
    v.alerta_movimiento_enviada = False
    db.commit()
    db.refresh(v)
    invalidate_owner_cache()
    return v


@router.post("/{veh_id}/disarm", response_model=VehicleOut)
def desarmar(veh_id: uuid.UUID, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Desarma el vehículo (lo estás usando tú)."""
    v = _owned(db, veh_id, current.id)
    v.armado = False
    v.alerta_movimiento_enviada = False
    db.commit()
    db.refresh(v)
    invalidate_owner_cache()
    return v


# ---------------- Inmovilizador (corte de motor) ----------------
SAFE_CUT_SPEED_KMH = 10.0


def _velocidad_actual(db: Session, v: Vehicle) -> float | None:
    device = db.get(Device, v.dispositivo_id) if v.dispositivo_id else None
    if device and device.traccar_device_id:
        try:
            live = traccar.get_latest_positions([device.traccar_device_id])
            if live:
                return normalize_position(live[0])["velocidad"]
        except Exception:
            pass
    pos = db.scalar(
        select(Position).where(Position.dispositivo_id == v.dispositivo_id)
        .order_by(Position.fija_en.desc()).limit(1)
    )
    return pos.velocidad if pos else None


def _device_inmovilizador(db: Session, v: Vehicle) -> Device:
    if not v.tiene_inmovilizador:
        raise HTTPException(400, "Este vehículo no tiene inmovilizador configurado")
    device = db.get(Device, v.dispositivo_id) if v.dispositivo_id else None
    if not device or not device.traccar_device_id:
        raise HTTPException(400, "El vehículo no tiene un rastreador asignado")
    return device


@router.post("/{veh_id}/engine-cut", response_model=VehicleOut)
def cortar_motor(
    veh_id: uuid.UUID, payload: EngineAction,
    current: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    """Corta el motor (inmovilizador). Requiere contraseña y vehículo detenido."""
    v = _owned(db, veh_id, current.id)
    if not verify_password(payload.password, current.password_hash):
        raise HTTPException(401, "Contraseña incorrecta")
    device = _device_inmovilizador(db, v)
    # Seguridad: nunca cortar el motor a velocidad alta.
    vel = _velocidad_actual(db, v)
    if vel is not None and vel > SAFE_CUT_SPEED_KMH:
        raise HTTPException(
            400,
            f"Por seguridad, el motor solo se corta con el vehículo detenido "
            f"(velocidad actual {vel:.0f} km/h).",
        )
    try:
        traccar.send_command(device.traccar_device_id, "engineStop")
    except Exception as e:
        raise HTTPException(502, f"No se pudo enviar el comando al dispositivo: {e}")

    v.motor_cortado = True
    db.commit()
    db.refresh(v)
    create_alert(
        db, usuario_id=current.id, tipo="motor_cortado",
        titulo=f"🛑 Motor cortado — {v.alias}",
        mensaje="Se envió el comando de corte de motor (inmovilizador).",
        canales=["app"], metadata={"vehiculo_id": str(v.id), "accion": "engineStop"},
    )
    return v


@router.post("/{veh_id}/engine-restore", response_model=VehicleOut)
def restablecer_motor(
    veh_id: uuid.UUID, payload: EngineAction,
    current: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    """Restablece el motor (quita el inmovilizador). Requiere contraseña."""
    v = _owned(db, veh_id, current.id)
    if not verify_password(payload.password, current.password_hash):
        raise HTTPException(401, "Contraseña incorrecta")
    device = _device_inmovilizador(db, v)
    try:
        traccar.send_command(device.traccar_device_id, "engineResume")
    except Exception as e:
        raise HTTPException(502, f"No se pudo enviar el comando al dispositivo: {e}")

    v.motor_cortado = False
    db.commit()
    db.refresh(v)
    create_alert(
        db, usuario_id=current.id, tipo="motor_restablecido",
        titulo=f"🔁 Motor restablecido — {v.alias}",
        mensaje="Se envió el comando para restablecer el motor.",
        canales=["app"], metadata={"vehiculo_id": str(v.id), "accion": "engineResume"},
    )
    return v


# ---------------- Posiciones ----------------
@router.get("/{veh_id}/latest", response_model=PositionOut | None)
def ultima_posicion(veh_id: uuid.UUID, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    v = _owned(db, veh_id, current.id)
    if not v.dispositivo_id:
        raise HTTPException(400, "El vehículo no tiene rastreador asignado")

    device = db.get(Device, v.dispositivo_id)
    if device and device.traccar_device_id:
        try:
            live = traccar.get_latest_positions([device.traccar_device_id])
            if live:
                norm = normalize_position(live[0])
                return PositionOut(
                    id=0, latitud=norm["latitud"], longitud=norm["longitud"],
                    velocidad=norm["velocidad"], rumbo=norm["rumbo"],
                    bateria=norm["bateria"], fija_en=norm["fija_en"],
                )
        except Exception as e:
            print(f"[Traccar] posición en vivo (vehículo) falló: {e}")

    return db.scalar(
        select(Position).where(Position.dispositivo_id == v.dispositivo_id)
        .order_by(Position.fija_en.desc()).limit(1)
    )


@router.get("/{veh_id}/history", response_model=list[PositionOut])
def historial(
    veh_id: uuid.UUID, dias: int = Query(7, ge=1, le=180),
    current: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    v = _owned(db, veh_id, current.id)
    desde = datetime.now(timezone.utc) - timedelta(days=dias)
    return db.scalars(
        select(Position)
        .where(Position.dispositivo_id == v.dispositivo_id, Position.fija_en >= desde)
        .order_by(Position.fija_en.asc())
    ).all()


# ---------------- Foto ----------------
@router.post("/{veh_id}/photo", response_model=VehicleOut)
def subir_foto(
    veh_id: uuid.UUID, file: UploadFile = File(...),
    current: User = Depends(get_admin_user), db: Session = Depends(get_db),
):
    v = db.get(Vehicle, veh_id)
    if not v:
        raise HTTPException(404, "Vehículo no encontrado")
    ext = ALLOWED_IMG.get(file.content_type)
    if not ext:
        raise HTTPException(400, "Formato no permitido. Usa JPG, PNG o WEBP.")
    contenido = file.file.read()
    if len(contenido) > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(400, f"La imagen supera el máximo de {settings.MAX_UPLOAD_MB} MB.")
    veh_dir = os.path.join(settings.UPLOAD_DIR, "vehicles")
    os.makedirs(veh_dir, exist_ok=True)
    for prev_ext in set(ALLOWED_IMG.values()):
        prev = os.path.join(veh_dir, f"{veh_id}{prev_ext}")
        if prev_ext != ext and os.path.exists(prev):
            os.remove(prev)
    filename = f"{veh_id}{ext}"
    with open(os.path.join(veh_dir, filename), "wb") as f:
        f.write(contenido)
    v.foto_url = f"/uploads/vehicles/{filename}"
    db.commit()
    db.refresh(v)
    return v


def _owned(db: Session, veh_id: uuid.UUID, user_id: uuid.UUID) -> Vehicle:
    v = db.get(Vehicle, veh_id)
    if not v or v.usuario_id != user_id:
        raise HTTPException(404, "Vehículo no encontrado")
    return v
