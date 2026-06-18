# =====================================================================
#  VertexLocation — Imagen única para Render (Fase 1: solo app web)
#  Construye el frontend (Vite) y lo sirve desde el backend (FastAPI).
# =====================================================================

# ----- Stage 1: build del frontend (React/Vite) -----
FROM node:20-slim AS frontend
WORKDIR /fe
COPY frontend-web/package.json frontend-web/package-lock.json ./
RUN npm ci
COPY frontend-web/ ./
RUN npm run build          # genera /fe/dist

# ----- Stage 2: backend (FastAPI) que sirve el frontend -----
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

# Dependencias del sistema para psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
# El build del frontend se copia donde el backend lo sirve (settings.FRONTEND_DIST)
COPY --from=frontend /fe/dist ./frontend_dist

EXPOSE 8000
# Render inyecta el puerto en $PORT; shell form para expandir la variable.
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
