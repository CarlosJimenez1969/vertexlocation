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
    """Crea todas las tablas y aplica migraciones ligeras idempotentes."""
    # Importa los modelos para que se registren en la metadata
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)

    # Migraciones ligeras: columnas agregadas a tablas existentes (create_all
    # NO altera tablas ya creadas). Son idempotentes (ADD COLUMN IF NOT EXISTS).
    from sqlalchemy import text
    _light_migrations = [
        "ALTER TABLE vehiculos ADD COLUMN IF NOT EXISTS km_actual INTEGER",
    ]
    with engine.begin() as conn:
        for sql in _light_migrations:
            try:
                conn.execute(text(sql))
            except Exception as e:  # no romper el arranque por una migración
                print(f"[init_db] migración ligera omitida: {e}")
