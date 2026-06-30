#!/bin/bash
# Se ejecuta UNA vez al inicializar PostgreSQL (carpeta docker-entrypoint-initdb.d).
# Crea el usuario y la base de VertexLocation. Añadir más apps abajo.
set -e

psql -v ON_ERROR_STOP=1 --username "postgres" <<-EOSQL
  CREATE USER vertexlocation WITH PASSWORD '${VXL_DB_PASSWORD}';
  CREATE DATABASE vertexlocation OWNER vertexlocation;
EOSQL

# Para futuras apps (ejemplo):
# psql -v ON_ERROR_STOP=1 --username "postgres" <<-EOSQL
#   CREATE USER vertexsalud WITH PASSWORD '${SALUD_DB_PASSWORD}';
#   CREATE DATABASE vertexsalud OWNER vertexsalud;
# EOSQL
