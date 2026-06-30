"""
Modelo de Vehículo (auto/moto) — plataforma multi-activo.

Reutiliza el mismo Dispositivo (rastreador GPS) y Posiciones que las mascotas;
solo cambia el "perfil" del activo. Tabla nueva: no altera nada existente.
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Vehicle(Base):
    __tablename__ = "vehiculos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    dispositivo_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dispositivos.id", ondelete="SET NULL"), unique=True
    )
    alias: Mapped[str] = mapped_column(String(60), nullable=False)          # "Mi Corolla"
    placa: Mapped[str | None] = mapped_column(String(15))                   # ABC-1234
    marca: Mapped[str | None] = mapped_column(String(40))                   # Toyota
    modelo: Mapped[str | None] = mapped_column(String(40))                  # Corolla
    anio: Mapped[int | None] = mapped_column(Integer)
    color: Mapped[str | None] = mapped_column(String(30))
    tipo: Mapped[str] = mapped_column(String(20), default="auto")           # auto|moto|camioneta|otro
    tipo_combustible: Mapped[str | None] = mapped_column(String(20))        # gasolina|diesel|electrico|hibrido
    tiene_inmovilizador: Mapped[bool] = mapped_column(Boolean, default=False)
    motor_cortado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    foto_url: Mapped[str | None] = mapped_column(String(300))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    # Límite de velocidad (km/h); None = sin monitoreo de velocidad.
    limite_velocidad: Mapped[int | None] = mapped_column(Integer)
    # Odómetro actual (km) — lo actualiza el usuario; base de los mantenimientos por km.
    km_actual: Mapped[int | None] = mapped_column(Integer)
    # --- Modo estacionado/armado (anti-robo) ---
    armado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    armado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    armado_lat: Mapped[float | None] = mapped_column(Float)
    armado_lng: Mapped[float | None] = mapped_column(Float)
    # Evita repetir la alerta dentro de la misma sesión de armado.
    alerta_movimiento_enviada: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relaciones (unidireccionales para no tocar User/Device existentes)
    owner = relationship("User")
    device = relationship("Device")
