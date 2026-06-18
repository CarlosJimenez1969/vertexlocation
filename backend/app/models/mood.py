"""Modelo de Estado de ánimo (snapshot calculado desde el acelerómetro)."""
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger, Boolean, DateTime, Float, ForeignKey, Numeric, String, func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

# Estados posibles
MOOD_STATES = (
    "feliz", "tranquilo", "ansioso", "asustado", "posiblemente_enfermo", "sin_datos",
)


class MoodState(Base):
    __tablename__ = "estados_animo"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    mascota_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("mascotas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    estado: Mapped[str] = mapped_column(String(24), nullable=False)
    confianza: Mapped[float | None] = mapped_column(Numeric(4, 3))   # 0.000 - 1.000
    actividad_pct: Mapped[float | None] = mapped_column(Numeric(6, 2))
    reposo_pct: Mapped[float | None] = mapped_column(Numeric(6, 2))
    velocidad_max: Mapped[float | None] = mapped_column(Float)
    movimiento_erratico: Mapped[float | None] = mapped_column(Numeric(6, 2))
    fuera_geocerca: Mapped[bool] = mapped_column(Boolean, default=False)
    ventana_inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ventana_fin: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    detalle: Mapped[dict | None] = mapped_column(JSONB)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    pet = relationship("Pet", back_populates="moods")
