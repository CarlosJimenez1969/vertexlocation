"""Modelo de Posición (historial de rutas + telemetría del acelerómetro)."""
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Position(Base):
    __tablename__ = "posiciones"
    __table_args__ = (
        UniqueConstraint("dispositivo_id", "traccar_pos_id", name="uq_pos_traccar"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    dispositivo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dispositivos.id", ondelete="CASCADE"), nullable=False
    )
    mascota_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("mascotas.id", ondelete="SET NULL")
    )
    traccar_pos_id: Mapped[int | None] = mapped_column(BigInteger)
    fija_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    latitud: Mapped[float] = mapped_column(Float, nullable=False)
    longitud: Mapped[float] = mapped_column(Float, nullable=False)
    altitud: Mapped[float | None] = mapped_column(Float)
    velocidad: Mapped[float | None] = mapped_column(Float)   # km/h
    rumbo: Mapped[float | None] = mapped_column(Float)       # grados
    precision_m: Mapped[float | None] = mapped_column(Float)
    satelites: Mapped[int | None] = mapped_column(Integer)
    bateria: Mapped[int | None] = mapped_column(Integer)
    # Acelerómetro de 3 ejes del C059
    accel_x: Mapped[float | None] = mapped_column(Float)
    accel_y: Mapped[float | None] = mapped_column(Float)
    accel_z: Mapped[float | None] = mapped_column(Float)
    magnitud_accel: Mapped[float | None] = mapped_column(Float)
    motion: Mapped[bool | None] = mapped_column(Boolean)
    attributes: Mapped[dict | None] = mapped_column(JSONB)   # payload crudo de Traccar
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    device = relationship("Device", back_populates="positions")
    pet = relationship("Pet", back_populates="positions")
