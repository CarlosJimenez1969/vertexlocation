"""
=====================================================================
 mood_algorithm.py — Algoritmo de estado de ánimo del perro
=====================================================================
 Deriva el "ánimo" de la mascota a partir de la telemetría del collar
 C059: acelerómetro de 3 ejes (movimiento/postura), velocidad GPS y
 cambios de ubicación, comparado contra una línea base histórica de
 7 días.

 Reglas de producto (VertexMascota):
   - Feliz:                actividad > 120% del promedio histórico (7 días)
   - Tranquilo:            reposo > 70% sin movimiento brusco
   - Ansioso:              movimiento errático, alta varianza de ubicación
   - Asustado:             velocidad alta repentina + salida de geocerca
   - Posiblemente enfermo: actividad < 40% por 2+ días consecutivos

 Implementado con NumPy + Pandas. Es PURO (sin I/O): recibe DataFrames
 ya cargados y devuelve un veredicto. La capa de servicio/Celery se
 encarga de leer de la DB y persistir en `estados_animo`.
=====================================================================
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

import numpy as np
import pandas as pd

# --- Umbrales configurables ---
THRESHOLDS = {
    "feliz_actividad": 1.20,      # > 120% del promedio
    "tranquilo_reposo": 0.70,     # > 70% del tiempo en reposo
    "movimiento_brusco_g": 1.8,   # magnitud (g) considerada "brusca"
    "erratico_indice": 0.65,      # índice de erraticidad [0..1]
    "velocidad_alta_kmh": 18.0,   # ~5 m/s, perro corriendo muy rápido
    "salto_velocidad_kmh": 12.0,  # subida repentina de velocidad entre muestras
    "enfermo_actividad": 0.40,    # < 40% del promedio
    "enfermo_dias": 2,            # sostenido 2+ días
    "gravedad_g": 1.0,            # 1 g de referencia (reposo)
    "movilidad_min_m": 150.0,     # movilidad alta en la ventana (m)
}

EARTH_R = 6_371_000.0  # m


@dataclass
class MoodResult:
    estado: str
    confianza: float
    actividad_pct: float | None = None
    reposo_pct: float | None = None
    velocidad_max: float | None = None
    movimiento_erratico: float | None = None
    fuera_geocerca: bool = False
    razones: list[str] = field(default_factory=list)
    metricas: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# --------------------------------------------------------------------
#  Funciones de soporte (NumPy / Pandas)
# --------------------------------------------------------------------
def _haversine_series(lat: np.ndarray, lng: np.ndarray) -> np.ndarray:
    """Distancia (m) entre puntos consecutivos de dos arreglos lat/lng."""
    if len(lat) < 2:
        return np.array([])
    lat1, lat2 = np.radians(lat[:-1]), np.radians(lat[1:])
    dlat = lat2 - lat1
    dlng = np.radians(lng[1:]) - np.radians(lng[:-1])
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlng / 2) ** 2
    return 2 * EARTH_R * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def _magnitudes(df: pd.DataFrame) -> np.ndarray:
    """Magnitud del vector de aceleración (g) por muestra."""
    if "magnitud_accel" in df and df["magnitud_accel"].notna().any():
        m = df["magnitud_accel"].fillna(0).to_numpy(dtype=float)
        if np.any(m > 0):
            return m
    ax = df.get("accel_x", pd.Series(0, index=df.index)).fillna(0).to_numpy(dtype=float)
    ay = df.get("accel_y", pd.Series(0, index=df.index)).fillna(0).to_numpy(dtype=float)
    az = df.get("accel_z", pd.Series(0, index=df.index)).fillna(0).to_numpy(dtype=float)
    return np.sqrt(ax**2 + ay**2 + az**2)


def compute_window_metrics(df: pd.DataFrame) -> dict[str, Any]:
    """
    Calcula métricas agregadas de una ventana de muestras.

    `df` debe tener columnas: fija_en, latitud, longitud, velocidad,
    rumbo, accel_x/accel_y/accel_z (o magnitud_accel).
    """
    n = len(df)
    if n == 0:
        return {
            "n": 0, "actividad_score": 0.0, "reposo_pct": 1.0,
            "movimiento_brusco_max": 0.0, "erratico_indice": 0.0,
            "velocidad_max": 0.0, "salto_velocidad_max": 0.0,
            "distancia_total_m": 0.0, "varianza_ubicacion": 0.0,
        }

    df = df.sort_values("fija_en")
    mags = _magnitudes(df)
    # Energía del acelerómetro: desviación respecto a 1 g (reposo).
    energia = np.abs(mags - THRESHOLDS["gravedad_g"])
    vel = df.get("velocidad", pd.Series(0, index=df.index)).fillna(0).to_numpy(dtype=float)

    # Reposo: poca energía y velocidad casi nula.
    en_reposo = np.logical_and(energia < 0.15, vel < 1.0)
    reposo_pct = float(en_reposo.mean()) if n else 1.0

    # Movimiento brusco: pico de magnitud.
    movimiento_brusco_max = float(mags.max()) if n else 0.0

    # Erraticidad: variabilidad de energía + variabilidad de rumbo.
    var_energia = float(np.std(energia)) if n > 1 else 0.0
    rumbo = df.get("rumbo", pd.Series(0, index=df.index)).fillna(0).to_numpy(dtype=float)
    rumbo_valid = rumbo[rumbo > 0]
    var_rumbo = float(np.std(rumbo_valid) / 180.0) if rumbo_valid.size > 1 else 0.0
    erratico_indice = float(min(1.0, var_energia * 1.5 + var_rumbo * 0.5))

    # Movilidad y varianza de ubicación.
    lat = df["latitud"].to_numpy(dtype=float)
    lng = df["longitud"].to_numpy(dtype=float)
    dist = _haversine_series(lat, lng)
    distancia_total_m = float(dist.sum()) if dist.size else 0.0
    # Varianza espacial (dispersión de la nube de puntos en metros).
    if n > 1:
        lat_m = (lat - lat.mean()) * (np.pi / 180) * EARTH_R
        lng_m = (lng - lng.mean()) * (np.pi / 180) * EARTH_R * np.cos(np.radians(lat.mean()))
        varianza_ubicacion = float(np.sqrt(np.var(lat_m) + np.var(lng_m)))
    else:
        varianza_ubicacion = 0.0

    # Salto de velocidad repentino entre muestras consecutivas.
    salto_velocidad_max = float(np.max(np.abs(np.diff(vel)))) if n > 1 else 0.0

    # Score de actividad (adimensional, comparable contra la línea base).
    actividad_score = float(energia.mean() * 100 + (distancia_total_m / max(1, n)) * 0.5)

    return {
        "n": n,
        "actividad_score": actividad_score,
        "reposo_pct": reposo_pct,
        "movimiento_brusco_max": movimiento_brusco_max,
        "erratico_indice": erratico_indice,
        "velocidad_max": float(vel.max()) if n else 0.0,
        "salto_velocidad_max": salto_velocidad_max,
        "distancia_total_m": distancia_total_m,
        "varianza_ubicacion": varianza_ubicacion,
    }


def baseline_activity(historico_df: pd.DataFrame, window_hours: float = 3.0) -> float:
    """
    Línea base: promedio del `actividad_score` en ventanas del histórico
    (últimos 7 días). Devuelve 0 si no hay datos suficientes.
    """
    if historico_df is None or historico_df.empty:
        return 0.0
    df = historico_df.copy()
    df["fija_en"] = pd.to_datetime(df["fija_en"], utc=True)
    df = df.set_index("fija_en").sort_index()

    scores: list[float] = []
    freq = f"{int(window_hours)}h"
    for _, grupo in df.groupby(pd.Grouper(freq=freq)):
        if len(grupo) >= 3:
            scores.append(compute_window_metrics(grupo.reset_index())["actividad_score"])
    return float(np.mean(scores)) if scores else 0.0


# --------------------------------------------------------------------
#  Evaluación del estado de ánimo
# --------------------------------------------------------------------
def evaluate_mood(
    ventana_df: pd.DataFrame,
    base_actividad: float = 0.0,
    fuera_geocerca: bool = False,
    dias_actividad_baja: int = 0,
) -> MoodResult:
    """
    Determina el estado de ánimo a partir de la ventana actual.

    Args:
        ventana_df: muestras recientes (1-6 h) como DataFrame.
        base_actividad: actividad_score promedio histórico (7 días).
        fuera_geocerca: True si la mascota salió de una geocerca activa.
        dias_actividad_baja: nº de días consecutivos con actividad < 40%.
    """
    m = compute_window_metrics(ventana_df)

    if m["n"] < 3:
        return MoodResult(
            estado="sin_datos", confianza=0.0,
            razones=["Muestras insuficientes en la ventana."], metricas=m,
        )

    ratio = (m["actividad_score"] / base_actividad) if base_actividad > 0 else 1.0
    razones: list[str] = []

    def build(estado: str, conf: float, motivo: str) -> MoodResult:
        razones.append(motivo)
        return MoodResult(
            estado=estado,
            confianza=conf,
            actividad_pct=round(ratio * 100, 2),
            reposo_pct=round(m["reposo_pct"] * 100, 2),
            velocidad_max=round(m["velocidad_max"], 2),
            movimiento_erratico=round(m["erratico_indice"] * 100, 2),
            fuera_geocerca=fuera_geocerca,
            razones=razones,
            metricas=m,
        )

    # Prioridad 1: ASUSTADO (velocidad alta repentina + salida de geocerca)
    velocidad_repentina = (
        m["velocidad_max"] >= THRESHOLDS["velocidad_alta_kmh"]
        and m["salto_velocidad_max"] >= THRESHOLDS["salto_velocidad_kmh"]
    )
    if velocidad_repentina and fuera_geocerca:
        return build(
            "asustado", 0.90,
            f"Velocidad máx {m['velocidad_max']:.1f} km/h (salto {m['salto_velocidad_max']:.1f}) "
            f"y fuera de geocerca.",
        )

    # Prioridad 2: POSIBLEMENTE ENFERMO (actividad < 40% por 2+ días)
    if ratio < THRESHOLDS["enfermo_actividad"] and dias_actividad_baja >= THRESHOLDS["enfermo_dias"]:
        return build(
            "posiblemente_enfermo", 0.85,
            f"Actividad {ratio*100:.0f}% del promedio durante {dias_actividad_baja} días.",
        )

    # Prioridad 3: ANSIOSO (movimiento errático + alta varianza de ubicación)
    if (
        m["erratico_indice"] >= THRESHOLDS["erratico_indice"]
        and m["varianza_ubicacion"] >= THRESHOLDS["movilidad_min_m"]
    ):
        return build(
            "ansioso", 0.75,
            f"Movimiento errático (índice {m['erratico_indice']:.2f}) y alta varianza de "
            f"ubicación ({m['varianza_ubicacion']:.0f} m).",
        )

    # Prioridad 4: FELIZ (actividad > 120% del promedio)
    if ratio > THRESHOLDS["feliz_actividad"]:
        return build(
            "feliz", 0.80,
            f"Actividad {ratio*100:.0f}% del promedio (juego/ejercicio).",
        )

    # Prioridad 5: TRANQUILO (reposo > 70% sin movimiento brusco)
    if (
        m["reposo_pct"] > THRESHOLDS["tranquilo_reposo"]
        and m["movimiento_brusco_max"] < THRESHOLDS["movimiento_brusco_g"]
    ):
        return build(
            "tranquilo", 0.80,
            f"Reposo {m['reposo_pct']*100:.0f}% sin picos de movimiento.",
        )

    # Estado neutro por defecto.
    return build("tranquilo", 0.50, "Sin patrón dominante; estado neutro.")


__all__ = [
    "evaluate_mood",
    "compute_window_metrics",
    "baseline_activity",
    "MoodResult",
    "THRESHOLDS",
]
