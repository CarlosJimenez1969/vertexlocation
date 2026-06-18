"""Configuración central de la aplicación (Pydantic Settings)."""
import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- App ---
    APP_NAME: str = "VertexLocation"
    ENV: str = "development"
    DEBUG: bool = True
    API_PREFIX: str = "/api"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # --- Base de datos ---
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "vertexmascota"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    DATABASE_URL: str | None = None

    # --- JWT ---
    JWT_SECRET: str = "dev_secret_inseguro"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 días

    # --- Traccar ---
    # En producción (Fase 1, solo web) se desactiva con TRACCAR_ENABLED=false:
    # no hay servidor Traccar y el puente en tiempo real no debe intentar conectarse.
    TRACCAR_ENABLED: bool = True
    TRACCAR_URL: str = "http://localhost:8082"
    TRACCAR_USER: str = "admin"
    TRACCAR_PASSWORD: str = "admin"
    TRACCAR_JT808_PORT: int = 5015
    TRACCAR_WS_URL: str = "ws://localhost:8082/api/socket"

    # --- Redis / Celery ---
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # --- Twilio (WhatsApp) ---
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_WHATSAPP_FROM: str = "whatsapp:+14155238886"

    # --- Email (SMTP) para reset de contraseña ---
    # Si SMTP_HOST queda vacío, el envío se "simula" (el enlace se imprime en consola).
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "VertexLocation <no-reply@vertexmascota.com>"
    SMTP_TLS: bool = True
    FRONTEND_URL: str = "http://localhost:3000"
    PASSWORD_RESET_EXPIRE_MINUTES: int = 30

    # --- CORS ---
    # Se guarda como str (separado por comas) para evitar que pydantic-settings
    # intente json.loads() sobre el valor del .env (lo haría si fuese List[str],
    # un tipo "complejo"). La lista se obtiene con la propiedad cors_origins_list.
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # --- Admin inicial (seed en BD nueva) ---
    # Si se definen, en el arranque se crea/asegura este usuario admin.
    ADMIN_EMAIL: str = ""
    ADMIN_PASSWORD: str = ""
    ADMIN_NAME: str = "Administrador"

    # --- Frontend servido por el backend (un solo servicio en Render) ---
    # Carpeta con el build de Vite (dist) copiado junto al backend.
    FRONTEND_DIST: str = "frontend_dist"

    # --- Archivos ---
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_MB: int = 5

    @property
    def cors_origins_list(self) -> list[str]:
        """Lista de orígenes CORS a partir de la cadena separada por comas."""
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def public_frontend_url(self) -> str:
        """URL pública para construir enlaces (correos de invitación/reset).

        En Render se usa RENDER_EXTERNAL_URL (la URL real del servicio,
        sin depender del nombre exacto); en local cae a FRONTEND_URL.
        """
        return os.getenv("RENDER_EXTERNAL_URL") or self.FRONTEND_URL

    @property
    def sqlalchemy_url(self) -> str:
        """URL definitiva para SQLAlchemy.

        Render entrega DATABASE_URL con el esquema `postgres://` (o
        `postgresql://` sin driver). SQLAlchemy 2.x necesita el driver
        explícito, así que normalizamos a `postgresql+psycopg2://`.
        """
        if self.DATABASE_URL:
            url = self.DATABASE_URL
            if url.startswith("postgres://"):
                url = "postgresql+psycopg2://" + url[len("postgres://"):]
            elif url.startswith("postgresql://"):
                url = "postgresql+psycopg2://" + url[len("postgresql://"):]
            return url
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
