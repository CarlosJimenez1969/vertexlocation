"""Schemas del panel de administración."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    # Sin contraseña: el usuario la define vía el correo de invitación.
    nombre: str = Field(min_length=2, max_length=120)
    email: EmailStr
    telefono: str | None = None
    ciudad: str | None = "Quito"
    rol: str = "cliente"          # cliente | admin | veterinario


class UserUpdate(BaseModel):
    nombre: str | None = None
    telefono: str | None = None
    ciudad: str | None = None
    rol: str | None = None
    activo: bool | None = None


class UserAdminOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    nombre: str
    email: EmailStr
    telefono: str | None
    ciudad: str | None
    rol: str
    activo: bool
    creado_en: datetime
