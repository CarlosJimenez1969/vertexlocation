# Runbook — desplegar VertexJD en el VPS

Pasos que se ejecutan una vez que el servidor existe y tenemos su IPv4.
(La mayoría los corro yo por SSH desde la PC; aquí quedan documentados.)

## 0. Conectarse
```bash
ssh -i ~/.ssh/vertexjd_vps root@IP_DEL_VPS
```

## 1. Preparar el servidor (hardening + Docker)
```bash
# copiar setup-server.sh al VPS y ejecutarlo
bash setup-server.sh
```

## 2. Traer el código y la config
```bash
cd /opt/vertexjd
git clone https://github.com/CarlosJimenez1969/vertexlocation.git vertexlocation
# copiar docker-compose.yml, Caddyfile, initdb/ y .env (rellenado) a /opt/vertexjd
cp .env.example .env && nano .env     # poner contraseñas/secretos reales
```

## 3. DNS en Cloudflare (apuntar a la IP del VPS)
- `location.vertexjd.com` → A → IP   (Proxied / naranja)
- `traccar.vertexjd.com`  → A → IP   (Proxied)
- `gps.vertexjd.com`      → A → IP   (DNS only / gris)  ← collares GPS
- SSL/TLS de Cloudflare en **Full (strict)**.

## 4. Levantar todo
```bash
cd /opt/vertexjd
docker compose up -d --build
docker compose ps
docker compose logs -f vertexlocation
```

## 5. Verificar
- https://location.vertexjd.com  → login de VertexLocation
- https://traccar.vertexjd.com   → panel de Traccar
- Login admin con ADMIN_EMAIL / ADMIN_PASSWORD del .env

## 6. (Opcional) Migrar datos de Render → VPS
```bash
# en la PC (cliente PG 18) o en el VPS:
pg_dump "EXTERNAL_DATABASE_URL_DE_RENDER" --no-owner --no-privileges > vxl.sql
psql "postgresql://vertexlocation:PASS@localhost:5432/vertexlocation" < vxl.sql
```

## 7. GPS (Fase 2): reconfigurar los collares
- SMS al collar, paso 2:  `IP gps.vertexjd.com 5015`   (dirección fija, ya no ngrok)
- Registrar el dispositivo en Traccar con el uniqueId (con cero inicial).

## Operación diaria
- Actualizar VertexLocation:  `cd /opt/vertexjd/vertexlocation && git pull && cd .. && docker compose up -d --build vertexlocation`
- Logs:  `docker compose logs -f <servicio>`
- Backup BD:  `docker compose exec db pg_dump -U vertexlocation vertexlocation > backup.sql`
