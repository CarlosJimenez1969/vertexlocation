"""Modelo de Reporte veterinario (plan Premium)."""
import uuid
from datetime import datetime, date

from sqlalchemy import DateTime, Date, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class VetReport(Base):
    __tablename__ = "reportes_veterinario"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mascota_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("mascotas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    periodo_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    periodo_fin: Mapped[date] = mapped_column(Date, nullable=False)
    resumen: Mapped[dict] = mapped_column(JSONB, nullable=False)
    pdf_url: Mapped[str | None] = mapped_column(String(300))
    generado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
