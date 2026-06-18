"""
email_service.py — Envío de correos vía SMTP (reset de contraseña).

Si SMTP_HOST está vacío, se "simula": el correo (y el enlace de reset) se
imprime en la consola del backend, igual que el WhatsApp simulado. Así el
flujo funciona en desarrollo sin configurar un servidor de correo.
"""
from __future__ import annotations

import smtplib
from email.message import EmailMessage

from app.core.config import settings


def send_email(to: str, subject: str, html: str, text: str | None = None) -> bool:
    """Envía un correo. Devuelve True si se entregó por SMTP, False si se simuló."""
    if not settings.SMTP_HOST:
        print(f"[Email:simulado] Para: {to} | Asunto: {subject}\n{text or html}")
        return False

    msg = EmailMessage()
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(text or "Abre este correo en un cliente compatible con HTML.")
    msg.add_alternative(html, subtype="html")

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
        if settings.SMTP_TLS:
            server.starttls()
        if settings.SMTP_USER:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)
    return True


def send_invitation_email(to: str, nombre: str, raw_token: str) -> bool:
    """Correo de bienvenida: el cliente define su contraseña por primera vez."""
    link = f"{settings.public_frontend_url.rstrip('/')}/reset-password?token={raw_token}"
    subject = "Bienvenido a VertexLocation — Crea tu contraseña"
    text = (
        f"Hola {nombre},\n\n"
        f"Se creó una cuenta para ti en VertexLocation.\n"
        f"Para empezar, crea tu contraseña en este enlace (válido por 48 horas):\n{link}\n\n"
        f"Luego podrás iniciar sesión y ver la ubicación de tus activos."
    )
    html = f"""\
    <div style="font-family:Inter,Arial,sans-serif;background:#0A0E1A;color:#E5EDFF;padding:24px;border-radius:12px;max-width:480px">
      <h2 style="margin:0 0 8px">📍 Vertex<span style="color:#3B82F6">Location</span></h2>
      <p>Hola <b>{nombre}</b>,</p>
      <p>Se creó una cuenta para ti. Crea tu contraseña para empezar:</p>
      <p style="margin:24px 0">
        <a href="{link}" style="background:#3B82F6;color:#fff;text-decoration:none;padding:12px 20px;border-radius:10px;font-weight:600">
          Crear mi contraseña
        </a>
      </p>
      <p style="font-size:12px;color:#4A6B9A">El enlace caduca en 48 horas. Si no esperabas este correo, ignóralo.</p>
    </div>"""
    return send_email(to, subject, html, text)


def send_password_reset_email(to: str, nombre: str, raw_token: str) -> bool:
    """Construye y envía el correo con el enlace para restablecer la contraseña."""
    link = f"{settings.public_frontend_url.rstrip('/')}/reset-password?token={raw_token}"
    mins = settings.PASSWORD_RESET_EXPIRE_MINUTES
    subject = "Restablece tu contraseña — VertexLocation"
    text = (
        f"Hola {nombre},\n\n"
        f"Recibimos una solicitud para restablecer tu contraseña.\n"
        f"Abre este enlace (válido por {mins} minutos):\n{link}\n\n"
        f"Si no fuiste tú, ignora este correo."
    )
    html = f"""\
    <div style="font-family:Inter,Arial,sans-serif;background:#0A0E1A;color:#E5EDFF;padding:24px;border-radius:12px;max-width:480px">
      <h2 style="margin:0 0 8px">📍 Vertex<span style="color:#3B82F6">Location</span></h2>
      <p>Hola <b>{nombre}</b>,</p>
      <p>Recibimos una solicitud para restablecer tu contraseña.</p>
      <p style="margin:24px 0">
        <a href="{link}" style="background:#3B82F6;color:#fff;text-decoration:none;padding:12px 20px;border-radius:10px;font-weight:600">
          Restablecer contraseña
        </a>
      </p>
      <p style="font-size:12px;color:#4A6B9A">El enlace caduca en {mins} minutos. Si no fuiste tú, ignora este correo.</p>
    </div>"""
    return send_email(to, subject, html, text)
