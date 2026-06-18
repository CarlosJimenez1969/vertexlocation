"""Modelo de Alerta."""
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger, Boolean, DateTime, Float, ForeignKey, String, Text, func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

ALERT_TYPES = (
    "salida_geocerca", "entrada_geocerca", "bateria_baja",
    "animo_enfermo", "animo_asustado", "animo_ansioso",
    "sin_senal", "dispositivo_offline", "velocidad_alta",
)


class Alert(Base):
    __tablename__ = "alertas"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    mascota_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("mascotas.id", ondelete="CASCADE")
    )
    geocerca_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("geocercas.id", ondelete="SET NULL")
    )
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    titulo: Mapped[str] = mapped_column(String(140), nullable=False)
    mensaje: Mapped[str | None] = mapped_column(Text)
    latitud: Mapped[float | None] = mapped_column(Float)
    longitud: Mapped[float | None] = mapped_column(Float)
    canales: Mapped[list | None] = mapped_column(ARRAY(String), default=["app"])
    leida: Mapped[bool] = mapped_column(Boolean, default=False)
    enviada_whatsapp: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    user = relationship("User", back_populates="alerts")
