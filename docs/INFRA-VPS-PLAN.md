# Plan de infraestructura VPS — VertexJD (multi-app + GPS)

Objetivo: hospedar **varias apps de VertexJD + Traccar (GPS) + una sola base PostgreSQL**
en **un solo servidor**, detrás de Cloudflare, con HTTPS automático. Un costo fijo
(~$6-12/mes) en lugar de $7 por app en Render.

## 1. Proveedor y tamaño

| Proveedor | Recomendación | Precio | Notas |
|-----------|--------------|--------|-------|
| **Hetzner Cloud** ⭐ | **CX22** (2 vCPU / 4 GB / 40 GB) | ~€4.59/mo | Mejor precio/rendimiento. Ubicación **US (Ashburn)** para menor latencia desde Ecuador. Puede pedir verificación de identidad. |
| **DigitalOcean** | Droplet 4 GB | ~$24/mo | El más fácil de contratar desde Ecuador; buenos tutoriales; a veces $200 de crédito inicial. |
| **Contabo** | VPS S (4 vCPU / 8 GB) | ~$6/mo | El más barato; rendimiento/soporte variables. |

- **Recomendado:** Hetzner **CX22** para empezar (alcanza para 2-3 apps + Traccar + Postgres).
  Si crecen las apps, subir a **CX32** (4 vCPU / 8 GB, ~€10/mo) — el resize es en caliente.
- **SO:** Ubuntu 24.04 LTS.

## 2. Arquitectura

```
Internet
  │
  ├── Cloudflare (DNS + caché + HTTPS + anti-DDoS)  ← ya lo tienes
  │     ├── location.vertexjd.com  ─┐
  │     ├── app2.vertexjd.com       ├─ (proxied / naranja) → Caddy :443
  │     └── traccar.vertexjd.com   ─┘
  │
  └── gps.vertexjd.com (DNS-only / gris) → VPS:5015  ← collares GPS (TCP, sin Cloudflare)
          │
        VPS (Ubuntu + Docker Compose)
          ├── Caddy            (reverse proxy + HTTPS automático)
          ├── PostgreSQL       (1 contenedor, varias bases: vertexlocation, app2, ...)
          ├── VertexLocation   (FastAPI+React, ya dockerizado)
          ├── Traccar          (GPS; puerto 5015 TCP expuesto al host)
          └── (futuras apps)   (cada una un contenedor)
```

Clave GPS: el VPS tiene **IP pública fija** → los collares apuntan a `gps.vertexjd.com:5015`
**para siempre** (se acaba el ngrok temporal). Cloudflare NO proxea TCP crudo en el plan free,
por eso ese subdominio va "DNS-only" (nube gris) apuntando directo a la IP del VPS.

## 3. Pasos de montaje

### 3.1 Crear y asegurar el servidor
1. Crear el VPS (Hetzner → Ubuntu 24.04 → añadir tu **clave SSH**).
2. Hardening inicial:
   ```bash
   adduser deploy && usermod -aG sudo deploy        # usuario no-root
   # copiar la clave SSH a deploy, luego en /etc/ssh/sshd_config:
   #   PermitRootLogin no ; PasswordAuthentication no
   systemctl restart ssh
   apt update && apt -y upgrade
   apt -y install ufw fail2ban
   ufw allow OpenSSH && ufw allow 80 && ufw allow 443
   ufw allow 5015/tcp                                # puerto JT808 de los collares
   ufw enable
   ```

### 3.2 Instalar Docker
```bash
curl -fsSL https://get.docker.com | sh
usermod -aG docker deploy
```

### 3.3 docker-compose (Caddy + Postgres + apps + Traccar)
`/opt/vertexjd/docker-compose.yml` (esquema):
```yaml
services:
  caddy:
    image: caddy:2
    ports: ["80:80", "443:443"]
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
    restart: unless-stopped

  db:
    image: postgres:18-alpine
    environment:
      POSTGRES_PASSWORD: ${PG_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    restart: unless-stopped

  vertexlocation:
    image: ghcr.io/carlosjimenez1969/vertexlocation:latest   # o build desde el repo
    environment:
      DATABASE_URL: postgresql://vertexlocation:${VXL_PASS}@db:5432/vertexlocation
      TRACCAR_ENABLED: "true"
      TRACCAR_URL: http://traccar:8082
      JWT_SECRET: ${JWT_SECRET}
      ADMIN_EMAIL: cijj1969@gmail.com
      ADMIN_PASSWORD: ${ADMIN_PASSWORD}
      SMTP_HOST: smtp.gmail.com
      SMTP_USER: cijj1969@gmail.com
      SMTP_PASSWORD: ${SMTP_PASSWORD}
      FRONTEND_URL: https://location.vertexjd.com
    restart: unless-stopped

  traccar:
    image: traccar/traccar:latest
    ports:
      - "5015:5015"      # JT808 (collar C059) — TCP directo
      - "5015:5015/udp"
    volumes:
      - traccar_data:/opt/traccar/data
    restart: unless-stopped

volumes: { caddy_data: {}, pgdata: {}, traccar_data: {} }
```

### 3.4 Caddyfile (HTTPS automático por subdominio)
```
location.vertexjd.com {
    reverse_proxy vertexlocation:8000
}
traccar.vertexjd.com {
    reverse_proxy traccar:8082
}
# app2.vertexjd.com { reverse_proxy app2:PORT }
```
Caddy saca y renueva los certificados Let's Encrypt solo.
(Con Cloudflare proxied, poner el SSL/TLS de Cloudflare en **Full (strict)**.)

### 3.5 DNS en Cloudflare
- `location.vertexjd.com` → A → IP_DEL_VPS  (**proxied**, naranja)
- `traccar.vertexjd.com`  → A → IP_DEL_VPS  (proxied)
- `gps.vertexjd.com`      → A → IP_DEL_VPS  (**DNS only**, gris)  ← para los collares

### 3.6 Postgres: una base por app
```sql
CREATE USER vertexlocation WITH PASSWORD '...';
CREATE DATABASE vertexlocation OWNER vertexlocation;
-- repetir por cada app
```

### 3.7 Migrar datos actuales (opcional)
- Exportar de Render: `pg_dump <EXTERNAL_URL> > vxl.sql` (con cliente PG 18).
- Importar al VPS: `psql postgresql://vertexlocation:...@VPS/vertexlocation < vxl.sql`.

### 3.8 GPS: reconfigurar los collares
- Por SMS, paso 2: `IP gps.vertexjd.com 5015` (dirección **fija**, ya no ngrok).
- Ver guía de los 3 pasos SMS del collar C059.

## 4. Backups y operación
- **Backups:** activar snapshots de Hetzner (+20%) y/o `pg_dump` diario por cron a almacenamiento externo.
- **Actualizaciones:** `docker compose pull && docker compose up -d` por servicio.
- **Monitoreo:** UptimeRobot (gratis) a cada subdominio.
- **Seguridad:** SSH solo con clave, UFW, fail2ban, Cloudflare al frente (oculta la IP en HTTP).

## 5. Costo total estimado
| Concepto | Mensual |
|----------|---------|
| VPS Hetzner CX22 | ~€4.59 (~$5) |
| Backups (opcional) | ~€1 |
| Cloudflare | $0 (free) |
| **TOTAL (todas las apps + GPS + BD)** | **~$6/mes** |

vs Render: ~$7 **por app** + BD c/u.
