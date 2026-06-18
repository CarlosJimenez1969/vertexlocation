"""Rutas de autenticación: registro, login (JWT) y reset de contraseña."""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.password_reset import PasswordReset
from app.models.user import User
from app.schemas.auth import (
    ForgotPassword, ResetPassword, Token, UserLogin, UserOut, UserRegister,
)
from app.services.email_service import send_password_reset_email

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    existe = db.scalar(select(User).where(User.email == payload.email))
    if existe:
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    user = User(
        nombre=payload.nombre,
        email=payload.email,
        password_hash=hash_password(payload.password),
        telefono=payload.telefono,
        ciudad=payload.ciudad or "Quito",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id, {"email": user.email, "rol": user.rol})
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Compatible con OAuth2: usa `username` (email) y `password`."""
    user = db.scalar(select(User).where(User.email == form.username))
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")

    user.ultimo_acceso = datetime.now(timezone.utc)
    db.commit()

    token = create_access_token(user.id, {"email": user.email, "rol": user.rol})
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.post("/login-json", response_model=Token)
def login_json(payload: UserLogin, db: Session = Depends(get_db)):
    """Login alternativo con JSON (para la app móvil / dashboard)."""
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")

    token = create_access_token(user.id, {"email": user.email, "rol": user.rol})
    return Token(access_token=token, user=UserOut.model_validate(user))


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
def forgot_password(payload: ForgotPassword, db: Session = Depends(get_db)):
    """
    Genera un token de reset y envía el correo con el enlace.
    Responde siempre lo mismo (no revela si el email existe) para evitar
    enumeración de usuarios.
    """
    generico = {
        "message": "Si el correo está registrado, te enviamos un enlace para restablecer tu contraseña."
    }
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user or not user.activo:
        return generico

    raw_token = secrets.token_urlsafe(32)
    db.add(PasswordReset(
        usuario_id=user.id,
        token_hash=_hash_token(raw_token),
        expira_en=datetime.now(timezone.utc)
        + timedelta(minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES),
    ))
    db.commit()

    try:
        send_password_reset_email(user.email, user.nombre, raw_token)
    except Exception as e:  # no exponer fallos de correo al cliente
        print(f"[Reset] Error enviando el correo: {e}")

    return generico


@router.post("/reset-password")
def reset_password(payload: ResetPassword, db: Session = Depends(get_db)):
    """Valida el token y actualiza la contraseña. El token es de un solo uso."""
    reset = db.scalar(
        select(PasswordReset).where(PasswordReset.token_hash == _hash_token(payload.token))
    )
    ahora = datetime.now(timezone.utc)
    if not reset or reset.usado or reset.expira_en < ahora:
        raise HTTPException(400, "El enlace es inválido o ha expirado. Solicita uno nuevo.")

    user = db.get(User, reset.usuario_id)
    if not user:
        raise HTTPException(400, "Usuario no encontrado.")

    user.password_hash = hash_password(payload.new_password)
    # Invalida este token y cualquier otro pendiente del usuario.
    for r in db.scalars(
        select(PasswordReset).where(
            PasswordReset.usuario_id == user.id, PasswordReset.usado.is_(False)
        )
    ).all():
        r.usado = True
    db.commit()

    return {"message": "Contraseña actualizada. Ya puedes iniciar sesión."}


@router.get("/me", response_model=UserOut)
def me(current: User = Depends(get_current_user)):
    return current
