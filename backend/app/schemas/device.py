"""Schemas para la pantalla unificada de dispositivos (rastreadores)."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DeviceRegister(BaseModel):
    imei: str = Field(min_length=6, max_length=20)   # IMEI/ID que transmite el rastreador
    nombre: str | None = None
    sim_operador: str | None = None                  # CNT | Claro | Movistar


class DeviceUpdate(BaseModel):
    imei: str | None = Field(default=None, min_length=6, max_length=20)
    nombre: str | None = None
    sim_operador: str | None = None


class Asignacion(BaseModel):
    tipo: str            # mascota | vehiculo
    id: uuid.UUID
    nombre: str


class DeviceFull(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    imei: str
    traccar_device_id: int | None
    modelo: str
    nombre: str | None
    sim_operador: str | None
    bateria: int | None
    online: bool
    ultima_conexion: datetime | None
    asignado: Asignacion | None = None


class AssignRequest(BaseModel):
    tipo: str                 # mascota | vehiculo
    target_id: uuid.UUID      # id de la mascota o vehículo
