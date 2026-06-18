"""Schemas de posiciones, geocercas, ánimo y alertas."""
import uuid
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


# ---------- Posiciones ----------
class PositionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    latitud: float
    longitud: float
    velocidad: float | None
    rumbo: float | None
    bateria: int | None
    fija_en: datetime


# ---------- Geocercas ----------
class PuntoPoligono(BaseModel):
    lat: float
    lng: float


class GeofenceCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=80)
    tipo: str = "circular"  # circular | poligono
    mascota_id: uuid.UUID | None = None
    vehiculo_id: uuid.UUID | None = None
    centro_lat: float | None = None
    centro_lng: float | None = None
    radio_m: float | None = None
    poligono: list[PuntoPoligono] | None = None
    color: str = "#3B82F6"
    alerta_entrada: bool = False
    alerta_salida: bool = True


class GeofenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    nombre: str
    tipo: str
    mascota_id: uuid.UUID | None = None
    vehiculo_id: uuid.UUID | None = None
    centro_lat: float | None
    centro_lng: float | None
    radio_m: float | None
    poligono: list | None
    color: str
    alerta_entrada: bool
    alerta_salida: bool
    activa: bool


# ---------- Estado de ánimo ----------
class MoodOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    mascota_id: uuid.UUID
    estado: str
    confianza: float | None
    actividad_pct: float | None
    reposo_pct: float | None
    velocidad_max: float | None
    movimiento_erratico: float | None
    fuera_geocerca: bool
    ventana_inicio: datetime
    ventana_fin: datetime
    detalle: dict | None
    creado_en: datetime


# ---------- Alertas ----------
class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    mascota_id: uuid.UUID | None
    tipo: str
    titulo: str
    mensaje: str | None
    latitud: float | None
    longitud: float | None
    leida: bool
    enviada_whatsapp: bool
    creado_en: datetime


# ---------- Actividad semanal ----------
class ActivityDayOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    fecha: datetime | None = None
    pasos: int
    distancia_km: float
    calorias: float
    minutos_activo: int
    minutos_reposo: int
    animo_dominante: str | None
