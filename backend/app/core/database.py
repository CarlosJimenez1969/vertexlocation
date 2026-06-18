"""Configuración de SQLAlchemy: engine, sesión y Base declarativa."""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from app.core.config import settings

engine = create_engine(
    settings.sqlalchemy_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=False,  # log SQL desactivado (inundaba la consola y ocultaba mensajes del puente)
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Base declarativa para todos los modelos."""
    pass


def get_db() -> Generator[Session, None, None]:
    """Dependencia de FastAPI que provee una sesión de base de datos."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Crea todas las tablas (para desarrollo; en prod usar Alembic)."""
    # Importa los modelos para que se registren en la metadata
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
