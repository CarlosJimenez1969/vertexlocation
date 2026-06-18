"""Modelo de Geocerca (circular o polígono)."""
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Integer, String, func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Geofence(Base):
    __tablename__ = "geocercas"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False
    )
    mascota_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("mascotas.id", ondelete="CASCADE")
    )
    vehiculo_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vehiculos.id", ondelete="CASCADE")
    )
    traccar_geofence_id: Mapped[int | None] = mapped_column(Integer)
    nombre: Mapped[str] = mapped_column(String(80), nullable=False)
    tipo: Mapped[str] = mapped_column(String(12), default="circular")  # circular|poligono
    # Circular
    centro_lat: Mapped[float | None] = mapped_column(Float)
    centro_lng: Mapped[float | None] = mapped_column(Float)
    radio_m: Mapped[float | None] = mapped_column(Float)
    # Polígono: lista [{lat,lng}, ...]
    poligono: Mapped[list | None] = mapped_column(JSONB)
    color: Mapped[str] = mapped_column(String(9), default="#3B82F6")
    alerta_entrada: Mapped[bool] = mapped_column(Boolean, default=False)
    alerta_salida: Mapped[bool] = mapped_column(Boolean, default=True)
    activa: Mapped[bool] = mapped_column(Boolean, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="geofences")
