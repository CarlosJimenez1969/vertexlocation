"""
alerts.py — Creación de alertas y envío por WhatsApp con Twilio.
"""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.alert import Alert
from app.models.user import User

# Cliente Twilio perezoso (solo si hay credenciales)
_twilio_client = None


def _get_twilio():
    global _twilio_client
    if _twilio_client is None and settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
        from twilio.rest import Client
        _twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    return _twilio_client


def send_whatsapp(to_phone: str, body: str) -> bool:
    """
    Envía un WhatsApp con Twilio. Si no hay credenciales, simula (log) y
    devuelve False.
    """
    client = _get_twilio()
    if client is None:
        print(f"[WhatsApp:simulado] -> {to_phone}: {body}")
        return False
    to = to_phone if to_phone.startswith("whatsapp:") else f"whatsapp:{to_phone}"
    client.messages.create(from_=settings.TWILIO_WHATSAPP_FROM, to=to, body=body)
    return True


def create_alert(
    db: Session,
    *,
    usuario_id: uuid.UUID,
    tipo: str,
    titulo: str,
    mensaje: str | None = None,
    mascota_id: uuid.UUID | None = None,
    geocerca_id: uuid.UUID | None = None,
    lat: float | None = None,
    lng: float | None = None,
    canales: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> Alert:
    """Crea la alerta en DB y dispara WhatsApp si corresponde."""
    canales = canales or ["app"]
    alert = Alert(
        usuario_id=usuario_id,
        mascota_id=mascota_id,
        geocerca_id=geocerca_id,
        tipo=tipo,
        titulo=titulo,
        mensaje=mensaje,
        latitud=lat,
        longitud=lng,
        canales=canales,
        metadata_=metadata,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    if "whatsapp" in canales:
        user = db.get(User, usuario_id)
        if user and user.telefono and user.whatsapp_opt_in:
            try:
                ok = send_whatsapp(user.telefono, f"*{titulo}*\n{mensaje or ''}")
                if ok:
                    alert.enviada_whatsapp = True
                    db.commit()
            except Exception as e:  # pragma: no cover
                print(f"[Alerta] Error enviando WhatsApp: {e}")

    return alert
