"""Tareas Celery: sincronización, recálculo de ánimo, resumen de actividad."""
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.device import Device
from app.models.pet import Pet
from app.models.position import Position
from app.models.activity import DailyActivity
from app.services import mood_algorithm as algo
from app.services.mood_service import compute_and_store_mood
from app.services.sync_service import sync_all
from app.tasks.celery_app import celery_app

OFFLINE_MINUTOS = 15


@celery_app.task
def sync_traccar() -> dict:
    """Trae las últimas posiciones de Traccar a la DB y revisa geocercas."""
    with SessionLocal() as db:
        return sync_all(db)


@celery_app.task
def recalcular_animos() -> dict:
    """Recalcula el estado de ánimo de todas las mascotas con collar."""
    n = 0
    with SessionLocal() as db:
        pets = db.scalars(select(Pet).where(Pet.dispositivo_id.isnot(None))).all()
        for pet in pets:
            if compute_and_store_mood(db, pet.id, window_hours=3):
                n += 1
    return {"mascotas_evaluadas": n}


@celery_app.task
def resumen_actividad_diaria() -> dict:
    """Calcula el resumen de actividad del día anterior para cada mascota."""
    ayer = (datetime.now(timezone.utc) - timedelta(days=1)).date()
    inicio = datetime.combine(ayer, datetime.min.time(), tzinfo=timezone.utc)
    fin = inicio + timedelta(days=1)
    procesadas = 0

    with SessionLocal() as db:
        pets = db.scalars(select(Pet).where(Pet.dispositivo_id.isnot(None))).all()
        for pet in pets:
            rows = db.scalars(
                select(Position).where(
                    Position.mascota_id == pet.id,
                    Position.fija_en >= inicio, Position.fija_en < fin,
                ).order_by(Position.fija_en.asc())
            ).all()
            if len(rows) < 2:
                continue

            resumen = _resumen_dia(rows, float(pet.peso_kg or 15))

            existente = db.scalar(
                select(DailyActivity).where(
                    DailyActivity.mascota_id == pet.id, DailyActivity.fecha == ayer
                )
            )
            if existente:
                for k, v in resumen.items():
                    setattr(existente, k, v)
            else:
                db.add(DailyActivity(mascota_id=pet.id, fecha=ayer, **resumen))
            procesadas += 1
        db.commit()
    return {"resumenes": procesadas, "fecha": str(ayer)}


@celery_app.task
def marcar_dispositivos_offline() -> dict:
    """Marca como offline los dispositivos sin reportar en OFFLINE_MINUTOS."""
    limite = datetime.now(timezone.utc) - timedelta(minutes=OFFLINE_MINUTOS)
    n = 0
    with SessionLocal() as db:
        devices = db.scalars(select(Device).where(Device.online.is_(True))).all()
        for d in devices:
            if not d.ultima_conexion or d.ultima_conexion < limite:
                d.online = False
                n += 1
        db.commit()
    return {"marcados_offline": n}


def _resumen_dia(rows: list[Position], peso_kg: float) -> dict:
    """Calcula pasos, distancia, calorías y tiempos a partir de las posiciones."""
    df = pd.DataFrame([{
        "fija_en": r.fija_en, "latitud": r.latitud, "longitud": r.longitud,
        "velocidad": r.velocidad or 0, "rumbo": r.rumbo,
        "accel_x": r.accel_x, "accel_y": r.accel_y, "accel_z": r.accel_z,
        "magnitud_accel": r.magnitud_accel,
    } for r in rows])

    metrics = algo.compute_window_metrics(df)
    distancia_km = round(metrics["distancia_total_m"] / 1000, 3)

    # Pasos estimados a partir de la energía del acelerómetro.
    mags = algo._magnitudes(df)
    pasos = int(np.sum(np.abs(mags - 1.0) > 0.3))

    # Tiempo activo vs reposo a partir de la velocidad.
    vel = df["velocidad"].to_numpy(dtype=float)
    intervalos = df["fija_en"].diff().dt.total_seconds().fillna(0).to_numpy()
    min_activo = float(np.sum(intervalos[vel > 1]) / 60)
    min_reposo = float(np.sum(intervalos[vel <= 1]) / 60)

    # Calorías (modelo simple): MET ~ 3 caminando, peso en kg.
    horas_activo = min_activo / 60
    calorias = round(3.0 * peso_kg * horas_activo, 2)

    return {
        "pasos": pasos,
        "distancia_km": distancia_km,
        "calorias": calorias,
        "minutos_activo": int(min_activo),
        "minutos_reposo": int(min_reposo),
        "velocidad_prom": float(np.mean(vel)) if len(vel) else 0.0,
        "actividad_score": round(metrics["actividad_score"], 2),
    }
