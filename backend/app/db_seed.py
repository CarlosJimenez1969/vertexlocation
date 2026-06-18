"""Inserta/actualiza los planes de suscripción por defecto y el admin inicial."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models.plan import Plan
from app.models.user import User

PLANES = [
    dict(codigo="basico", nombre="Básico", precio_mensual=20.00, max_mascotas=1,
         max_geocercas=1, dias_historial=7, estado_animo=False, alertas_whatsapp=False,
         reporte_semanal=False, reporte_veterinario=False, soporte_prioritario=False),
    dict(codigo="estandar", nombre="Estándar", precio_mensual=25.00, max_mascotas=1,
         max_geocercas=-1, dias_historial=30, estado_animo=True, alertas_whatsapp=True,
         reporte_semanal=True, reporte_veterinario=False, soporte_prioritario=False),
    dict(codigo="premium", nombre="Premium", precio_mensual=30.00, max_mascotas=3,
         max_geocercas=-1, dias_historial=180, estado_animo=True, alertas_whatsapp=True,
         reporte_semanal=True, reporte_veterinario=True, soporte_prioritario=True),
]


def seed_plans(db: Session) -> None:
    for data in PLANES:
        plan = db.scalar(select(Plan).where(Plan.codigo == data["codigo"]))
        if plan:
            for k, v in data.items():
                setattr(plan, k, v)
        else:
            db.add(Plan(**data))
    db.commit()


def seed_admin(db: Session) -> None:
    """Crea (o asegura) el usuario administrador inicial a partir de las
    variables ADMIN_EMAIL / ADMIN_PASSWORD. Idempotente: no pisa la
    contraseña si el usuario ya existe."""
    email = (settings.ADMIN_EMAIL or "").strip().lower()
    if not email or not settings.ADMIN_PASSWORD:
        return
    user = db.scalar(select(User).where(User.email == email))
    if user:
        # Asegura que tenga rol admin y esté activo, sin tocar su contraseña.
        if user.rol != "admin" or not user.activo:
            user.rol = "admin"
            user.activo = True
            db.commit()
        return
    db.add(User(
        nombre=settings.ADMIN_NAME or "Administrador",
        email=email,
        password_hash=hash_password(settings.ADMIN_PASSWORD),
        rol="admin",
        activo=True,
    ))
    db.commit()
    print(f"[seed] Admin inicial creado: {email}")
