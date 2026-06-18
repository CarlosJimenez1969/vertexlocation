"""Rutas de reportes veterinarios PDF (plan Premium)."""
import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.activity import DailyActivity
from app.models.mood import MoodState
from app.models.pet import Pet
from app.models.user import User
from app.services.report_generator import generate_vet_report

router = APIRouter(prefix="/reports", tags=["reportes"])


@router.get("/vet/{pet_id}")
def reporte_veterinario(
    pet_id: uuid.UUID,
    dias: int = 30,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Genera un PDF de reporte veterinario del último periodo."""
    pet = db.get(Pet, pet_id)
    if not pet or pet.usuario_id != current.id:
        raise HTTPException(404, "Mascota no encontrada")

    fin = date.today()
    inicio = fin - timedelta(days=dias)

    # Agregar actividad
    actividades = db.scalars(
        select(DailyActivity).where(
            DailyActivity.mascota_id == pet_id, DailyActivity.fecha >= inicio
        )
    ).all()
    moods = db.scalars(
        select(MoodState).where(MoodState.mascota_id == pet_id, MoodState.creado_en >= inicio)
    ).all()

    resumen = _build_resumen(actividades, moods)

    path = generate_vet_report(
        pet={
            "nombre": pet.nombre, "especie": pet.especie, "raza": pet.raza,
            "sexo": pet.sexo, "edad_meses": pet.edad_meses, "peso_kg": float(pet.peso_kg or 0),
        },
        periodo=(inicio, fin),
        resumen=resumen,
    )
    return FileResponse(path, media_type="application/pdf", filename=path.split("/")[-1])


def _build_resumen(actividades, moods) -> dict:
    n = len(actividades) or 1
    promedio_pasos = round(sum(a.pasos for a in actividades) / n)
    distancia_total = round(sum(float(a.distancia_km) for a in actividades), 2)
    calorias_prom = round(sum(float(a.calorias) for a in actividades) / n, 1)
    activo_prom = round(sum(a.minutos_activo for a in actividades) / n)
    reposo_prom = round(sum(a.minutos_reposo for a in actividades) / n)

    # Distribución de ánimo
    dist: dict[str, int] = {}
    for m in moods:
        dist[m.estado] = dist.get(m.estado, 0) + 1
    total = sum(dist.values()) or 1
    dist_pct = {k: round(v / total * 100, 1) for k, v in dist.items()}
    dominante = max(dist, key=dist.get) if dist else "sin_datos"

    anomalias = []
    if dist_pct.get("posiblemente_enfermo", 0) > 10:
        anomalias.append("Se detectaron periodos de baja actividad compatibles con malestar.")
    if dist_pct.get("ansioso", 0) > 20:
        anomalias.append("Episodios de ansiedad frecuentes; considerar evaluación de comportamiento.")

    return {
        "actividad": {
            "promedio_pasos": promedio_pasos,
            "distancia_total_km": distancia_total,
            "calorias_prom": calorias_prom,
            "minutos_activo_prom": activo_prom,
            "minutos_reposo_prom": reposo_prom,
        },
        "animo": {"distribucion": dist_pct, "dominante": dominante},
        "anomalias": anomalias,
    }
