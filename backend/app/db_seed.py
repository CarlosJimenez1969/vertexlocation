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
    """Crea/asegura el usuario administrador a partir de ADMIN_EMAIL /
    ADMIN_PASSWORD. La variable de entorno es la FUENTE DE VERDAD: en cada
    arranque garantiza rol admin, cuenta activa y la contraseña indicada.
    (Para dejar de restablecerla, basta con quitar ADMIN_PASSWORD del entorno.)"""
    email = (settings.ADMIN_EMAIL or "").strip().lower()
    if not email or not settings.ADMIN_PASSWORD:
        print("[seed] ADMIN_EMAIL/ADMIN_PASSWORD no definidos; se omite el admin.")
        return
    user = db.scalar(select(User).where(User.email == email))
    if user:
        user.rol = "admin"
        user.activo = True
        user.password_hash = hash_password(settings.ADMIN_PASSWORD)
        db.commit()
        print(f"[seed] Admin asegurado (rol + contraseña restablecida): {email}")
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
