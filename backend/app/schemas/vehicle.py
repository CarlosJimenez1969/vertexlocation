"""Schemas de vehículo (plataforma multi-activo)."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class VehicleCreate(BaseModel):
    alias: str = Field(min_length=1, max_length=60)
    placa: str | None = Field(default=None, max_length=15)
    marca: str | None = None
    modelo: str | None = None
    anio: int | None = Field(default=None, ge=1950, le=2100)
    color: str | None = None
    tipo: str = "auto"                         # auto|moto|camioneta|otro
    tipo_combustible: str | None = None
    limite_velocidad: int | None = Field(default=None, ge=1, le=300)
    tiene_inmovilizador: bool = False
    # Registro opcional del rastreador en el mismo paso (como en mascotas).
    imei: str | None = Field(default=None, min_length=6, max_length=20)
    sim_operador: str | None = None


class EngineAction(BaseModel):
    """Confirmación con contraseña para acciones del inmovilizador."""
    password: str = Field(min_length=1)


class VehicleUpdate(BaseModel):
    alias: str | None = None
    placa: str | None = None
    marca: str | None = None
    modelo: str | None = None
    anio: int | None = None
    color: str | None = None
    tipo: str | None = None
    tipo_combustible: str | None = None
    limite_velocidad: int | None = Field(default=None, ge=0, le=300)
    tiene_inmovilizador: bool | None = None
    km_actual: int | None = Field(default=None, ge=0)
    foto_url: str | None = None
    dispositivo_id: uuid.UUID | None = None


class VehicleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    alias: str
    placa: str | None
    marca: str | None
    modelo: str | None
    anio: int | None
    color: str | None
    tipo: str
    tipo_combustible: str | None
    limite_velocidad: int | None
    tiene_inmovilizador: bool
    km_actual: int | None
    motor_cortado: bool
    foto_url: str | None
    dispositivo_id: uuid.UUID | None
    activo: bool
    armado: bool
    armado_en: datetime | None
    creado_en: datetime
