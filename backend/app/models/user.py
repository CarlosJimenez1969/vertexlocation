"""Modelo de Usuario."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "usuarios"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(160), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    telefono: Mapped[str | None] = mapped_column(String(20))  # E.164 (+593...) para WhatsApp
    whatsapp_opt_in: Mapped[bool] = mapped_column(Boolean, default=True)
    ciudad: Mapped[str | None] = mapped_column(String(80), default="Quito")
    pais: Mapped[str | None] = mapped_column(String(60), default="Ecuador")
    rol: Mapped[str] = mapped_column(String(20), default="cliente")  # cliente|admin|veterinario
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    ultimo_acceso: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    pets = relationship("Pet", back_populates="owner", cascade="all, delete-orphan")
    devices = relationship("Device", back_populates="owner", cascade="all, delete-orphan")
    geofences = relationship("Geofence", back_populates="owner", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")
