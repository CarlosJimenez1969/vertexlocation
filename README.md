# 📍 VertexLocation

**Plataforma de rastreo GPS multi-activo (mascotas y vehículos) en Ecuador**, construida sobre rastreadores GPS (p. ej. collar **C059 CAT1 IP67**) y la plataforma **Traccar**, con un backend en **Python + FastAPI**, dashboard web en **React** y app móvil en **React Native**.

> Estilo oscuro y tecnológico · Tiempo real con WebSockets · Estado de ánimo basado en el acelerómetro del collar.

---

## 📋 Tabla de contenido

1. [Arquitectura](#-arquitectura)
2. [Stack tecnológico](#-stack-tecnológico)
3. [Estructura del proyecto](#-estructura-del-proyecto)
4. [Requisitos previos](#-requisitos-previos)
5. [Instalación rápida con Docker](#-instalación-rápida-con-docker)
6. [Instalación manual (desarrollo)](#-instalación-manual-desarrollo)
7. [Configuración del collar C059](#-configuración-del-collar-c059)
8. [Algoritmo de estado de ánimo](#-algoritmo-de-estado-de-ánimo)
9. [Planes de suscripción](#-planes-de-suscripción)
10. [API REST](#-api-rest)
11. [Modelo de negocio](#-modelo-de-negocio)

---

## 🏗 Arquitectura

```
┌────────────┐   JT808/4G    ┌────────────┐   REST + WS   ┌──────────────┐
│ Collar C059│ ────────────▶ │  Traccar   │ ◀──────────── │   Backend    │
│  (mascota) │   puerto 5015 │ :8082 / API│               │   FastAPI    │
└────────────┘               └────────────┘               │   :8000      │
                                                           └──────┬───────┘
                              ┌──────────────┐                    │
                              │  PostgreSQL  │ ◀──────────────────┤
                              └──────────────┘   SQLAlchemy       │
                              ┌──────────────┐                    │
                              │ Redis+Celery │ ◀──── tareas ──────┤
                              └──────────────┘                    │
                                              REST / WebSocket     │
                       ┌──────────────────────────────────────────┤
                       ▼                                           ▼
              ┌─────────────────┐                        ┌──────────────────┐
              │ Dashboard React │                        │  App React Native│
              │  (Leaflet)      │                        │  (Android / iOS) │
              └─────────────────┘                        └──────────────────┘
```

El collar reporta por **JT808** al puerto **5015** de Traccar. El backend FastAPI consume la **API REST** y el **WebSocket** de Traccar, persiste posiciones en PostgreSQL, calcula el estado de ánimo con NumPy/Pandas, verifica geocercas y reenvía todo en tiempo real a los clientes.

---

## 🧰 Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend | Python 3.12 · FastAPI · Uvicorn (ASGI) |
| ORM / DB | SQLAlchemy 2 · PostgreSQL 16 |
| Tiempo real | WebSockets (`websockets` + FastAPI WebSocket) |
| Ánimo | NumPy · Pandas |
| Traccar | `requests` (REST) |
| Auth | PyJWT · passlib/bcrypt |
| Tareas | Celery · Redis |
| WhatsApp | Twilio |
| PDF | ReportLab |
| Tests | Pytest |
| Dashboard | React · Vite · Tailwind CSS · Leaflet · Recharts |
| Móvil | React Native (Expo) · react-native-maps |

---

## 📁 Estructura del proyecto

```
vertexmascota/
├── backend/                      # Python + FastAPI
│   ├── main.py                   # App FastAPI + arranque del puente Traccar
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .env.example
│   ├── app/
│   │   ├── core/                 # config, security (JWT), database
│   │   ├── models/               # SQLAlchemy (usuarios, mascotas, posiciones…)
│   │   ├── schemas/              # Pydantic
│   │   ├── api/
│   │   │   ├── deps.py           # usuario autenticado
│   │   │   └── routes/           # auth, pets, positions, geofences, mood, alerts, reports
│   │   ├── services/
│   │   │   ├── traccar.py        # cliente REST de Traccar
│   │   │   ├── mood_algorithm.py # algoritmo de ánimo (NumPy/Pandas)
│   │   │   ├── mood_service.py   # puente DB ↔ algoritmo
│   │   │   ├── geofence.py       # geocercas (círculo/polígono)
│   │   │   ├── alerts.py         # alertas + Twilio (WhatsApp)
│   │   │   ├── report_generator.py # PDF veterinario (ReportLab)
│   │   │   └── sync_service.py   # sincronización con Traccar
│   │   ├── realtime/             # WebSocket: manager, ws_routes, traccar_bridge
│   │   └── tasks/                # Celery (celery_app, jobs)
│   └── tests/                    # Pytest
├── frontend-web/                 # Dashboard React (Vite + Tailwind)
│   └── src/
│       ├── components/{Map,Sidebar,MoodCard,AlertPanel}/
│       ├── pages/{Login,Dashboard}.jsx
│       ├── api/  context/  hooks/
├── mobile/                       # React Native (Expo)
│   └── src/screens/{LoginScreen,MapScreen,ProfileScreen}.js
└── docker-compose.yml            # PostgreSQL, Redis, Traccar, backend, Celery
```

---

## ✅ Requisitos previos

- **Docker** y **Docker Compose** (vía rápida), o bien:
- **Python 3.12+**, **Node.js 18+**, **PostgreSQL 16**, **Redis 7**
- **Traccar** (incluido en docker-compose; o instalado en `localhost:8082`)
- Cuenta **Twilio** (opcional, para WhatsApp)

---

## 🚀 Instalación rápida con Docker

```bash
# 1. Clonar y entrar al proyecto
cd vertexmascota

# 2. Crear el archivo de entorno del backend
cp backend/.env.example backend/.env
#    Edita backend/.env y ajusta JWT_SECRET, credenciales de Traccar y Twilio.

# 3. Levantar todo (PostgreSQL, Redis, Traccar, Backend, Celery worker + beat)
docker compose up --build
```

Servicios disponibles:

| Servicio | URL |
|----------|-----|
| Backend API (Swagger) | http://localhost:8000/docs |
| Healthcheck | http://localhost:8000/health |
| Traccar (panel web) | http://localhost:8082 |
| PostgreSQL | localhost:5432 |
| Puerto del collar (JT808) | **5015** |

> Las tablas se crean automáticamente al arrancar el backend (y se siembran los 3 planes).

### Dashboard web

```bash
cd frontend-web
npm install
npm run dev          # http://localhost:5173 (proxy a :8000)
```

### App móvil

```bash
cd mobile
npm install
npm start            # abre Expo; usa 'a' para Android o 'i' para iOS
```
> Edita `mobile/src/api/client.js` → `API_BASE` con la IP de tu backend (emulador Android: `http://10.0.2.2:8000`).

---

## 🛠 Instalación manual (desarrollo)

### Backend

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env          # ajusta variables

# Asegúrate de tener PostgreSQL y Redis corriendo
uvicorn main:app --reload --port 8000
```

### Celery (en dos terminales aparte)

```bash
# Worker
celery -A app.tasks.celery_app worker --loglevel=info

# Beat (tareas programadas)
celery -A app.tasks.celery_app beat --loglevel=info
```

### Tests

```bash
cd backend
pytest
```

---

## 📡 Configuración del collar C059

El **C059 CAT1** (Shenzhen Uniwoay Technology) usa el protocolo **JT808** y se configura por **SMS**. Inserta una SIM 4G de **Claro** o **Movistar Ecuador** (bandas compatibles: B2/B3/B4/B5/B7/B8/B28/B66).

### 1. Apuntar el collar a tu servidor

Envía estos SMS al número de la SIM del collar (los comandos pueden variar según el firmware; consulta el manual del fabricante):

```
# Configurar IP/dominio y puerto del servidor (Traccar JT808 = 5015)
SERVER,1,TU_DOMINIO_O_IP,5015,0#

# Configurar APN del operador
# Claro Ecuador:
APN,internet.claro.com.ec#
# Movistar Ecuador:
APN,internet.movistar.com.ec#

# Intervalo de reporte de posición (cada 30 s, por ejemplo)
TIMER,30#

# Reiniciar para aplicar
RESET#
```

> Reemplaza `TU_DOMINIO_O_IP` por el dominio/IP pública donde corre Traccar. El collar abrirá una conexión **TCP/IP** permanente al puerto **5015**.

### 2. Registrar el dispositivo en Traccar

1. Entra a **http://localhost:8082** (usuario por defecto: `admin` / `admin`).
2. **Settings → Devices → +** y registra el collar con su **IMEI** como `Identifier` (el `uniqueId` que envía por JT808).

### 3. Registrar el collar en VertexLocation

Desde la app o vía API:

```bash
curl -X POST http://localhost:8000/api/pets/devices \
  -H "Authorization: Bearer <TU_JWT>" \
  -H "Content-Type: application/json" \
  -d '{"imei":"123456789012345","nombre":"Collar de Firulais","sim_operador":"Claro"}'
```

Esto crea el dispositivo en Traccar **y** en VertexLocation, y queda listo para asignarse a una mascota.

### Especificaciones del C059

| Característica | Valor |
|---------------|-------|
| Protocolo | JT808 |
| Puerto Traccar | 5015 (TCP/IP) |
| Red | 4G LTE B2/B3/B4/B5/B7/B8/B28/B66 |
| GPS | AT6558R |
| Sensor | Acelerómetro de 3 ejes |
| Batería | 700 mAh · carga magnética |
| Resistencia | IP67 |
| Peso | 34 g |

---

## 🧠 Algoritmo de estado de ánimo

Implementado en [`backend/app/services/mood_algorithm.py`](backend/app/services/mood_algorithm.py) con **NumPy + Pandas**. Combina el **acelerómetro de 3 ejes**, la **velocidad GPS** y la **varianza de ubicación**, comparados contra una **línea base histórica de 7 días**.

| Estado | Regla | Color |
|--------|-------|-------|
| 😄 **Feliz** | Actividad **> 120 %** del promedio histórico | `#10B981` |
| 😌 **Tranquilo** | Reposo **> 70 %** sin movimiento brusco | `#3B82F6` |
| 😰 **Ansioso** | Movimiento errático + alta varianza de ubicación | `#F59E0B` |
| 😱 **Asustado** | Velocidad alta repentina **+** salida de geocerca | `#EF4444` |
| 🤒 **Posiblemente enfermo** | Actividad **< 40 %** por **2+ días** consecutivos | `#A855F7` |

El cálculo corre automáticamente cada 30 min (Celery beat) y bajo demanda vía `POST /api/mood/{pet_id}/recalculate`. Los estados críticos (enfermo, asustado, ansioso) disparan **alertas automáticas** por app y WhatsApp.

---

## 💳 Planes de suscripción

| | **Básico** $20/mes | **Estándar** $25/mes | **Premium** $30/mes |
|--|--|--|--|
| GPS tiempo real | ✅ | ✅ | ✅ |
| Historial | 7 días | 30 días | **180 días** |
| Geocercas | 1 | Ilimitadas | Ilimitadas |
| Estado de ánimo | — | ✅ | ✅ |
| Alertas WhatsApp | — | ✅ | ✅ |
| Reporte veterinario PDF | — | — | ✅ |
| Máx. mascotas | 1 | 1 | **3** |

---

## 🔌 API REST

Documentación interactiva en **http://localhost:8000/docs**.

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/auth/register` | Registro de usuario |
| `POST` | `/api/auth/login-json` | Login (JSON) → JWT |
| `GET`  | `/api/auth/me` | Perfil actual |
| `GET/POST` | `/api/pets` | Listar / crear mascotas |
| `POST` | `/api/pets/devices` | Registrar collar C059 |
| `GET`  | `/api/positions/latest/{pet_id}` | Última posición |
| `GET`  | `/api/positions/history/{pet_id}?dias=` | Historial de rutas |
| `GET/POST` | `/api/geofences` | Geocercas |
| `GET`  | `/api/mood/{pet_id}/current` | Estado de ánimo actual |
| `POST` | `/api/mood/{pet_id}/recalculate` | Recalcular ánimo |
| `GET`  | `/api/mood/{pet_id}/activity?dias=` | Actividad semanal |
| `GET`  | `/api/alerts` | Alertas |
| `GET`  | `/api/reports/vet/{pet_id}` | Reporte veterinario PDF (Premium) |
| `WS`   | `/ws?token=<JWT>` | Posiciones / eventos en tiempo real |

---

## 💰 Modelo de negocio

- **Venta del collar C059** al cliente: **$65**
- **Costo de operación** por collar: **$4.20/mes** (SIM $3 + servidor $1.20)
- **Margen de suscripción**: **79 – 86 %**

| Plan | Precio | Costo | Margen |
|------|--------|-------|--------|
| Básico | $20 | $4.20 | 79 % |
| Estándar | $25 | $4.20 | 83 % |
| Premium | $30 | $4.20 | 86 % |

---

## 🎨 Paleta de diseño VertexLocation

| Uso | Color |
|-----|-------|
| Fondo principal | `#0A0E1A` |
| Azul principal | `#3B82F6` |
| Azul claro | `#60A5FA` |
| Texto secundario | `#4A6B9A` |
| Bordes | `#1E3A6B` |
| Éxito | `#10B981` |

---

## 📄 Licencia

MIT © VertexLocation — Ecuador 🇪🇨
