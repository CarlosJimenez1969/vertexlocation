"""Schemas de autenticación y usuario."""
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserRegister(BaseModel):
    nombre: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6, max_length=72)
    telefono: str | None = Field(default=None, max_length=20)
    ciudad: str | None = "Quito"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class ForgotPassword(BaseModel):
    email: EmailStr


class ResetPassword(BaseModel):
    token: str = Field(min_length=10, max_length=128)
    new_password: str = Field(min_length=6, max_length=72)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    nombre: str
    email: EmailStr
    telefono: str | None
    ciudad: str | None
    pais: str | None
    rol: str
    creado_en: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
