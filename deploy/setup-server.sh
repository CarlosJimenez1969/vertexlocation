#!/usr/bin/env bash
# Preparación de un VPS Ubuntu 24.04 para VertexJD: hardening + Docker.
# Ejecutar como root en el servidor recién creado:  bash setup-server.sh
set -euo pipefail

echo "==> Actualizando el sistema"
export DEBIAN_FRONTEND=noninteractive
export NEEDRESTART_MODE=a          # evita el prompt interactivo de needrestart (Ubuntu 24.04)
apt-get update && apt-get -y upgrade
apt-get -y install ufw fail2ban git curl ca-certificates

echo "==> Firewall (UFW)"
ufw default deny incoming
ufw default allow outgoing
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 5015/tcp     # JT808 (collares GPS)
ufw allow 5015/udp
ufw --force enable

echo "==> fail2ban"
systemctl enable --now fail2ban

echo "==> Endurecer SSH (solo llave, sin contraseña)"
sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin prohibit-password/' /etc/ssh/sshd_config
# Los cloud images suelen reactivar password en sshd_config.d/*
if ls /etc/ssh/sshd_config.d/*.conf >/dev/null 2>&1; then
  sed -i 's/^PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config.d/*.conf
fi
systemctl restart ssh 2>/dev/null || systemctl restart sshd

echo "==> Docker"
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sh
fi
systemctl enable --now docker

echo "==> Carpeta del stack"
mkdir -p /opt/vertexjd

echo "==> LISTO. Docker: $(docker --version)"
echo "    Siguiente: clonar el repo, copiar docker-compose.yml/Caddyfile/.env y 'docker compose up -d'."
