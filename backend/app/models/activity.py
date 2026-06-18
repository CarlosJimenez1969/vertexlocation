"""Modelo de Actividad diaria (resumen para reportes y tendencias)."""
import uuid
from datetime import datetime, date

from sqlalchemy import (
    BigInteger, Date, DateTime, Float, ForeignKey, Integer, Numeric, String,
    UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DailyActivity(Base):
    __tablename__ = "actividad_diaria"
    __table_args__ = (
        UniqueConstraint("mascota_id", "fecha", name="uq_actividad_mascota_fecha"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    mascota_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("mascotas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    pasos: Mapped[int] = mapped_column(Integer, default=0)
    distancia_km: Mapped[float] = mapped_column(Numeric(8, 3), default=0)
    calorias: Mapped[float] = mapped_column(Numeric(8, 2), default=0)
    minutos_activo: Mapped[int] = mapped_column(Integer, default=0)
    minutos_reposo: Mapped[int] = mapped_column(Integer, default=0)
    velocidad_prom: Mapped[float | None] = mapped_column(Float)
    actividad_score: Mapped[float | None] = mapped_column(Numeric(8, 2))
    animo_dominante: Mapped[str | None] = mapped_column(String(24))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    pet = relationship("Pet", back_populates="activities")
