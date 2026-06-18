"""Tests del algoritmo de estado de ánimo."""
from datetime import datetime, timedelta, timezone

import pandas as pd

from app.services import mood_algorithm as algo


def _df(rows):
    return pd.DataFrame(rows)


def _muestra(t, lat, lng, vel=0, ax=0, ay=0, az=1.0, rumbo=0):
    return dict(fija_en=t, latitud=lat, longitud=lng, velocidad=vel,
                rumbo=rumbo, accel_x=ax, accel_y=ay, accel_z=az, magnitud_accel=None)


def test_sin_datos():
    res = algo.evaluate_mood(_df([]), base_actividad=10)
    assert res.estado == "sin_datos"


def test_tranquilo_en_reposo():
    base = datetime.now(timezone.utc)
    rows = [_muestra(base + timedelta(minutes=i), -0.18, -78.46, vel=0, az=1.0) for i in range(10)]
    res = algo.evaluate_mood(_df(rows), base_actividad=50)
    assert res.estado == "tranquilo"
    assert res.reposo_pct > 70


def test_feliz_actividad_alta():
    base = datetime.now(timezone.utc)
    # Mucha energía de acelerómetro y movimiento -> actividad muy por encima de la base
    rows = []
    for i in range(12):
        lat = -0.18 + i * 0.0001
        rows.append(_muestra(base + timedelta(minutes=i), lat, -78.46, vel=6,
                             ax=0.8, ay=0.7, az=1.3, rumbo=(i * 40) % 360))
    res = algo.evaluate_mood(_df(rows), base_actividad=5)
    assert res.estado in ("feliz", "ansioso")  # alta actividad


def test_asustado_velocidad_y_fuera_geocerca():
    base = datetime.now(timezone.utc)
    rows = [_muestra(base, -0.18, -78.46, vel=2)]
    rows.append(_muestra(base + timedelta(seconds=30), -0.182, -78.462, vel=25, ax=1, ay=1, az=1.5))
    rows.append(_muestra(base + timedelta(seconds=60), -0.184, -78.464, vel=28, ax=1, ay=1, az=1.5))
    res = algo.evaluate_mood(_df(rows), base_actividad=5, fuera_geocerca=True)
    assert res.estado == "asustado"


def test_posiblemente_enfermo():
    base = datetime.now(timezone.utc)
    rows = [_muestra(base + timedelta(minutes=i), -0.18, -78.46, vel=0, az=1.0) for i in range(5)]
    # actividad muy baja respecto a base alta + 2 días bajos
    res = algo.evaluate_mood(_df(rows), base_actividad=1000, dias_actividad_baja=3)
    assert res.estado == "posiblemente_enfermo"
