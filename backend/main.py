"""
=====================================================================
 VertexLocation — Backend (FastAPI / Uvicorn ASGI)
=====================================================================
 Plataforma de rastreo GPS multi-activo (mascotas y vehículos) en Ecuador.
 Hardware: collar C059 CAT1 (JT808) -> Traccar (puerto 5015) -> esta API.

 Arranque:
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
=====================================================================
"""
import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import SessionLocal, init_db
from app.db_seed import seed_plans, seed_admin

# Routers REST
from app.api.routes import auth, pets, positions, geofences, mood, alerts, reports, vehicles, devices, admin, share, maintenance
# WebSocket
from app.realtime.ws_routes import router as ws_router
from app.realtime.traccar_bridge import run_bridge


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    init_db()
    with SessionLocal() as db:
        seed_plans(db)
        seed_admin(db)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # Puente en tiempo real con Traccar (tarea de fondo). Se omite si Traccar
    # está desactivado (Fase 1 en la nube: solo la app web, sin hardware GPS).
    bridge_task = None
    if settings.TRACCAR_ENABLED:
        bridge_task = asyncio.create_task(run_bridge())
        print(f"[{settings.APP_NAME}] Backend iniciado. Traccar: {settings.TRACCAR_URL}")
    else:
        print(f"[{settings.APP_NAME}] Backend iniciado SIN Traccar (TRACCAR_ENABLED=false).")

    yield

    # --- Shutdown ---
    if bridge_task:
        bridge_task.cancel()
        try:
            await bridge_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title=f"{settings.APP_NAME} API",
    description="Plataforma de rastreo GPS multi-activo (mascotas y vehículos) con Traccar.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Archivos estáticos (fotos de mascotas, PDFs)
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


# --- Healthcheck ---
@app.get("/health", tags=["sistema"])
def health():
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.ENV}


# --- Registro de routers ---
P = settings.API_PREFIX
app.include_router(auth.router, prefix=P)
app.include_router(pets.router, prefix=P)
app.include_router(positions.router, prefix=P)
app.include_router(geofences.router, prefix=P)
app.include_router(mood.router, prefix=P)
app.include_router(alerts.router, prefix=P)
app.include_router(reports.router, prefix=P)
app.include_router(vehicles.router, prefix=P)
app.include_router(devices.router, prefix=P)
app.include_router(admin.router, prefix=P)
app.include_router(share.router, prefix=P)
app.include_router(maintenance.router, prefix=P)

# WebSocket (sin prefijo de API; ruta /ws)
app.include_router(ws_router)


# --- Frontend (SPA de React/Vite servido por el mismo backend) ---
# En producción (Docker) el build de Vite se copia en settings.FRONTEND_DIST.
# Se sirve después de los routers para que /api, /ws, /uploads y /health tengan
# prioridad; cualquier otra ruta devuelve index.html (ruteo del lado del cliente).
_FRONTEND_DIR = Path(settings.FRONTEND_DIST)
if (_FRONTEND_DIR / "index.html").is_file():
    _assets = _FRONTEND_DIR / "assets"
    if _assets.is_dir():
        app.mount("/assets", StaticFiles(directory=_assets), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def servir_spa(full_path: str):
        archivo = _FRONTEND_DIR / full_path
        if full_path and archivo.is_file():
            return FileResponse(archivo)
        return FileResponse(_FRONTEND_DIR / "index.html")

    print(f"[{settings.APP_NAME}] Sirviendo frontend desde {_FRONTEND_DIR.resolve()}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
