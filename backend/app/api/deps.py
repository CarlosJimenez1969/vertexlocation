"""Dependencias compartidas de la API (usuario autenticado vía JWT)."""
import uuid

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=True)

CRED_EXC = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Credenciales inválidas",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise CRED_EXC
        user_uuid = uuid.UUID(user_id)
    except (jwt.PyJWTError, ValueError):
        raise CRED_EXC

    user = db.get(User, user_uuid)
    if user is None or not user.activo:
        raise CRED_EXC
    return user


def get_admin_user(current: User = Depends(get_current_user)) -> User:
    """Exige rol de administrador para operaciones de gestión de datos."""
    if current.rol != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta acción requiere permisos de administrador.",
        )
    return current
