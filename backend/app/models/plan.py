"""Modelos de Plan de suscripción y Suscripción del usuario."""
import uuid
from datetime import datetime, date

from sqlalchemy import (
    Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Plan(Base):
    __tablename__ = "planes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)  # basico|estandar|premium
    nombre: Mapped[str] = mapped_column(String(60), nullable=False)
    precio_mensual: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    max_mascotas: Mapped[int] = mapped_column(Integer, default=1)
    max_geocercas: Mapped[int] = mapped_column(Integer, default=1)   # -1 = ilimitadas
    dias_historial: Mapped[int] = mapped_column(Integer, default=7)
    estado_animo: Mapped[bool] = mapped_column(Boolean, default=False)
    alertas_whatsapp: Mapped[bool] = mapped_column(Boolean, default=False)
    reporte_semanal: Mapped[bool] = mapped_column(Boolean, default=False)
    reporte_veterinario: Mapped[bool] = mapped_column(Boolean, default=False)
    soporte_prioritario: Mapped[bool] = mapped_column(Boolean, default=False)

    subscriptions = relationship("Subscription", back_populates="plan")


class Subscription(Base):
    __tablename__ = "suscripciones"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False
    )
    plan_id: Mapped[int] = mapped_column(ForeignKey("planes.id"), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), default="pendiente")  # activa|pendiente|cancelada|vencida
    inicio: Mapped[date] = mapped_column(Date, default=date.today)
    proximo_cobro: Mapped[date | None] = mapped_column(Date)
    precio: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    metodo_pago: Mapped[str | None] = mapped_column(String(40))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="subscriptions")
    plan = relationship("Plan", back_populates="subscriptions")
