"""Configuración de Celery + Redis y calendario de tareas (beat)."""
from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "vertexmascota",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.jobs"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="America/Guayaquil",
    enable_utc=True,
    task_track_started=True,
)

# Tareas programadas
celery_app.conf.beat_schedule = {
    # Sincroniza posiciones desde Traccar cada minuto (respaldo del WebSocket)
    "sync-traccar-cada-minuto": {
        "task": "app.tasks.jobs.sync_traccar",
        "schedule": 60.0,
    },
    # Recalcula el estado de ánimo de todas las mascotas cada 30 min
    "recalcular-animo-cada-30min": {
        "task": "app.tasks.jobs.recalcular_animos",
        "schedule": 1800.0,
    },
    # Genera el resumen de actividad diaria a las 00:15 (hora Ecuador)
    "resumen-actividad-diario": {
        "task": "app.tasks.jobs.resumen_actividad_diaria",
        "schedule": crontab(hour=0, minute=15),
    },
    # Marca dispositivos sin reportar como offline cada 5 min
    "marcar-offline-cada-5min": {
        "task": "app.tasks.jobs.marcar_dispositivos_offline",
        "schedule": 300.0,
    },
}
