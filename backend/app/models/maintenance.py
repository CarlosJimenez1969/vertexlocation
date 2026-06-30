"""Modelo de Mantenimiento preventivo de un vehículo (recordatorios por fecha/km)."""
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Maintenance(Base):
    __tablename__ = "mantenimientos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehiculo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vehiculos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tipo: Mapped[str] = mapped_column(String(80), nullable=False)        # "Cambio de aceite"
    notas: Mapped[str | None] = mapped_column(String(300))

    # Vencimiento por fecha y/o por kilometraje (al menos uno)
    fecha_proxima: Mapped[date | None] = mapped_column(Date)
    km_proximo: Mapped[int | None] = mapped_column(Integer)

    # Recurrencia (opcional): al marcar "realizado" se reprograma con estos intervalos
    intervalo_dias: Mapped[int | None] = mapped_column(Integer)
    intervalo_km: Mapped[int | None] = mapped_column(Integer)

    realizado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
