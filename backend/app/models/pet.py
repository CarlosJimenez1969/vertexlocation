"""Modelo de Mascota."""
import uuid
from datetime import datetime, date

from sqlalchemy import (
    Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Pet(Base):
    __tablename__ = "mascotas"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False
    )
    dispositivo_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dispositivos.id", ondelete="SET NULL"), unique=True
    )
    nombre: Mapped[str] = mapped_column(String(60), nullable=False)
    especie: Mapped[str] = mapped_column(String(20), default="perro")
    raza: Mapped[str | None] = mapped_column(String(80))
    sexo: Mapped[str] = mapped_column(String(12), default="desconocido")  # macho|hembra|desconocido
    fecha_nacimiento: Mapped[date | None] = mapped_column(Date)
    edad_meses: Mapped[int | None] = mapped_column(Integer)
    peso_kg: Mapped[float | None] = mapped_column(Numeric(5, 2))
    foto_url: Mapped[str | None] = mapped_column(String(300))
    notas: Mapped[str | None] = mapped_column(Text)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="pets")
    device = relationship("Device", back_populates="pet")
    positions = relationship("Position", back_populates="pet")
    moods = relationship("MoodState", back_populates="pet", cascade="all, delete-orphan")
    activities = relationship("DailyActivity", back_populates="pet", cascade="all, delete-orphan")
