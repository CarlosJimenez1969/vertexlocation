"""Rutas de alertas."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.alert import Alert
from app.models.user import User
from app.schemas.tracking import AlertOut

router = APIRouter(prefix="/alerts", tags=["alertas"])


@router.get("", response_model=list[AlertOut])
def listar_alertas(
    solo_no_leidas: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = select(Alert).where(Alert.usuario_id == current.id)
    if solo_no_leidas:
        stmt = stmt.where(Alert.leida.is_(False))
    stmt = stmt.order_by(Alert.creado_en.desc()).limit(limit)
    return db.scalars(stmt).all()


@router.post("/{alert_id}/read", response_model=AlertOut)
def marcar_leida(alert_id: int, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    alert = db.get(Alert, alert_id)
    if not alert or alert.usuario_id != current.id:
        from fastapi import HTTPException
        raise HTTPException(404, "Alerta no encontrada")
    alert.leida = True
    db.commit()
    db.refresh(alert)
    return alert
