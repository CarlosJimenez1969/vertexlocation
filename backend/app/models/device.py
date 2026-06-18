"""Modelo de Dispositivo (collar C059) — espeja un device de Traccar."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Device(Base):
    __tablename__ = "dispositivos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # El dueño se hereda de la mascota/vehículo al asignar el dispositivo;
    # mientras no esté asignado, el dispositivo no tiene dueño (NULL).
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=True
    )
    imei: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)  # uniqueId JT808
    traccar_device_id: Mapped[int | None] = mapped_column(Integer, unique=True, index=True)
    modelo: Mapped[str] = mapped_column(String(40), default="C059 CAT1")
    protocolo: Mapped[str] = mapped_column(String(20), default="jt808")
    nombre: Mapped[str | None] = mapped_column(String(80))
    sim_iccid: Mapped[str | None] = mapped_column(String(30))
    sim_operador: Mapped[str | None] = mapped_column(String(40))  # Claro | Movistar
    bateria: Mapped[int | None] = mapped_column(Integer)          # 0-100 %
    online: Mapped[bool] = mapped_column(Boolean, default=False)
    ultima_conexion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    firmware: Mapped[str | None] = mapped_column(String(40))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="devices")
    pet = relationship("Pet", back_populates="device", uselist=False)
    positions = relationship("Position", back_populates="device", cascade="all, delete-orphan")
