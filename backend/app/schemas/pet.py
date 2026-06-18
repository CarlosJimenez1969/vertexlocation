"""Schemas de mascota y dispositivo."""
import uuid
from datetime import datetime, date

from pydantic import BaseModel, Field, ConfigDict


class DeviceCreate(BaseModel):
    imei: str = Field(min_length=6, max_length=20)
    nombre: str | None = None
    sim_operador: str | None = None  # Claro | Movistar


class DeviceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    imei: str
    traccar_device_id: int | None
    modelo: str
    nombre: str | None
    bateria: int | None
    online: bool
    ultima_conexion: datetime | None


class PetCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=60)
    especie: str = "perro"
    raza: str | None = None
    sexo: str = "desconocido"
    fecha_nacimiento: date | None = None
    edad_meses: int | None = None
    peso_kg: float | None = None
    dispositivo_id: uuid.UUID | None = None


class PetUpdate(BaseModel):
    nombre: str | None = None
    raza: str | None = None
    sexo: str | None = None
    fecha_nacimiento: date | None = None
    edad_meses: int | None = None
    peso_kg: float | None = None
    foto_url: str | None = None
    dispositivo_id: uuid.UUID | None = None


class PetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    nombre: str
    especie: str
    raza: str | None
    sexo: str
    edad_meses: int | None
    peso_kg: float | None
    foto_url: str | None
    dispositivo_id: uuid.UUID | None
    creado_en: datetime
