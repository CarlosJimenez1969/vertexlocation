"""
mood_service.py — Puente entre la base de datos y mood_algorithm.

Carga posiciones desde la DB a un DataFrame, calcula la línea base de 7
días, detecta salida de geocerca y persiste el resultado en estados_animo.
También dispara alertas cuando el ánimo es crítico.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.geofence import Geofence
from app.models.mood import MoodState
from app.models.pet import Pet
from app.models.position import Position
from app.services import geofence as geo
from app.services import mood_algorithm as algo
from app.services.alerts import create_alert

POSITION_COLS = [
    "fija_en", "latitud", "longitud", "velocidad", "rumbo",
    "accel_x", "accel_y", "accel_z", "magnitud_accel",
]

# Disparan alerta automática
MOOD_ALERT_MAP = {
    "posiblemente_enfermo": ("animo_enfermo", "Tu mascota podría estar enferma"),
    "asustado": ("animo_asustado", "Tu mascota parece asustada"),
    "ansioso": ("animo_ansioso", "Tu mascota muestra ansiedad"),
}


def _positions_to_df(rows: list[Position]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=POSITION_COLS)
    data = [{c: getattr(r, c) for c in POSITION_COLS} for r in rows]
    return pd.DataFrame(data)


def _low_activity_days(db: Session, pet_id: uuid.UUID, base: float) -> int:
    """Cuenta días consecutivos (hacia atrás) con actividad < 40% del promedio."""
    if base <= 0:
        return 0
    dias = 0
    hoy = datetime.now(timezone.utc).date()
    for offset in range(0, 7):
        d = hoy - timedelta(days=offset)
        inicio = datetime.combine(d, datetime.min.time(), tzinfo=timezone.utc)
        fin = inicio + timedelta(days=1)
        rows = db.scalars(
            select(Position).where(
                Position.mascota_id == pet_id,
                Position.fija_en >= inicio, Position.fija_en < fin,
            )
        ).all()
        if len(rows) < 3:
            break
        score = algo.compute_window_metrics(_positions_to_df(rows))["actividad_score"]
        if score < base * algo.THRESHOLDS["enfermo_actividad"]:
            dias += 1
        else:
            break
    return dias


def _is_outside_geofence(db: Session, pet: Pet, lat: float, lng: float) -> tuple[bool, Geofence | None]:
    """True si la mascota está fuera de TODAS sus geocercas activas con alerta_salida."""
    gfs = db.scalars(
        select(Geofence).where(
            Geofence.usuario_id == pet.usuario_id,
            Geofence.activa.is_(True),
        )
    ).all()
    relevantes = [g for g in gfs if g.mascota_id in (None, pet.id) and g.alerta_salida]
    if not relevantes:
        return False, None
    for g in relevantes:
        if geo.is_inside(lat, lng, g):
            return False, None
    return True, relevantes[0]


def compute_and_store_mood(
    db: Session, pet_id: uuid.UUID, window_hours: int = 3
) -> MoodState | None:
    """Calcula y guarda el estado de ánimo de una mascota."""
    pet = db.get(Pet, pet_id)
    if not pet or not pet.dispositivo_id:
        return None

    ahora = datetime.now(timezone.utc)
    ventana_inicio = ahora - timedelta(hours=window_hours)
    base_inicio = ahora - timedelta(days=7)

    ventana_rows = db.scalars(
        select(Position).where(
            Position.mascota_id == pet_id, Position.fija_en >= ventana_inicio
        ).order_by(Position.fija_en.asc())
    ).all()
    hist_rows = db.scalars(
        select(Position).where(
            Position.mascota_id == pet_id, Position.fija_en >= base_inicio
        )
    ).all()

    ventana_df = _positions_to_df(ventana_rows)
    hist_df = _positions_to_df(hist_rows)

    base = algo.baseline_activity(hist_df, window_hours=window_hours)

    fuera = False
    if ventana_rows:
        ultima = ventana_rows[-1]
        fuera, _ = _is_outside_geofence(db, pet, ultima.latitud, ultima.longitud)

    dias_bajos = _low_activity_days(db, pet_id, base)

    result = algo.evaluate_mood(
        ventana_df, base_actividad=base, fuera_geocerca=fuera,
        dias_actividad_baja=dias_bajos,
    )

    mood = MoodState(
        mascota_id=pet_id,
        estado=result.estado,
        confianza=result.confianza,
        actividad_pct=result.actividad_pct,
        reposo_pct=result.reposo_pct,
        velocidad_max=result.velocidad_max,
        movimiento_erratico=result.movimiento_erratico,
        fuera_geocerca=result.fuera_geocerca,
        ventana_inicio=ventana_inicio,
        ventana_fin=ahora,
        detalle={"razones": result.razones, "metricas": result.metricas},
    )
    db.add(mood)
    db.commit()
    db.refresh(mood)

    # Alerta automática para estados críticos
    if result.estado in MOOD_ALERT_MAP and result.confianza >= 0.7:
        tipo, titulo = MOOD_ALERT_MAP[result.estado]
        create_alert(
            db,
            usuario_id=pet.usuario_id,
            mascota_id=pet_id,
            tipo=tipo,
            titulo=f"{titulo}: {pet.nombre}",
            mensaje=" ".join(result.razones),
            canales=["app", "whatsapp"],
            metadata={"estado": result.estado, "confianza": result.confianza},
        )

    return mood
