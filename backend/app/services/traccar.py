"""
traccar.py — Cliente de la API REST de Traccar (requests).

El collar C059 reporta por el puerto JT808 (5015) y Traccar lo convierte
en devices / positions / events que consumimos aquí. Autenticación Basic
Auth con el usuario admin de Traccar.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

import requests

from app.core.config import settings


class TraccarClient:
    def __init__(self) -> None:
        self.base = f"{settings.TRACCAR_URL.rstrip('/')}/api"
        self.session = requests.Session()
        self.session.auth = (settings.TRACCAR_USER, settings.TRACCAR_PASSWORD)
        self.session.headers.update({"Accept": "application/json"})
        self.timeout = 10

    # ---------- internos ----------
    def _get(self, path: str, params: dict | None = None) -> Any:
        r = self.session.get(f"{self.base}{path}", params=params, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def _post(self, path: str, json: dict) -> Any:
        r = self.session.post(f"{self.base}{path}", json=json, timeout=self.timeout)
        r.raise_for_status()
        return r.json() if r.content else None

    def _delete(self, path: str) -> None:
        r = self.session.delete(f"{self.base}{path}", timeout=self.timeout)
        r.raise_for_status()

    # ---------- dispositivos ----------
    def get_devices(self) -> list[dict]:
        return self._get("/devices")

    def get_device(self, traccar_device_id: int) -> dict | None:
        data = self._get("/devices", params={"id": traccar_device_id})
        return data[0] if isinstance(data, list) and data else data

    def create_device(
        self, name: str, unique_id: str, phone: str | None = None,
        model: str = "C059 CAT1", category: str = "animal",
    ) -> dict:
        """unique_id = IMEI que el C059 envía por JT808."""
        return self._post(
            "/devices",
            {"name": name, "uniqueId": unique_id, "phone": phone,
             "model": model, "category": category},
        )

    def update_device(self, traccar_device_id: int, name: str | None = None,
                      unique_id: str | None = None) -> dict | None:
        """Actualiza nombre/uniqueId de un device existente en Traccar (PUT)."""
        dev = self.get_device(traccar_device_id)
        if not dev:
            return None
        if name is not None:
            dev["name"] = name
        if unique_id is not None:
            dev["uniqueId"] = unique_id
        r = self.session.put(f"{self.base}/devices/{traccar_device_id}", json=dev, timeout=self.timeout)
        r.raise_for_status()
        return r.json() if r.content else dev

    def delete_device(self, traccar_device_id: int) -> None:
        self._delete(f"/devices/{traccar_device_id}")

    # ---------- posiciones ----------
    def get_latest_positions(self, device_ids: list[int] | None = None) -> list[dict]:
        """
        Última posición de cada dispositivo. Traccar `/positions` sin parámetros
        devuelve la última posición por dispositivo; filtramos por deviceId.
        (El parámetro `id` de Traccar es el id de la posición, NO del dispositivo.)
        """
        data = self._get("/positions")
        if device_ids:
            ids = set(device_ids)
            return [p for p in data if p.get("deviceId") in ids]
        return data

    def get_positions_history(
        self, traccar_device_id: int, dt_from: datetime, dt_to: datetime
    ) -> list[dict]:
        return self._get(
            "/positions",
            params={
                "deviceId": traccar_device_id,
                "from": dt_from.isoformat(),
                "to": dt_to.isoformat(),
            },
        )

    # ---------- eventos ----------
    def get_events(self, traccar_device_id: int, dt_from: datetime, dt_to: datetime) -> list[dict]:
        return self._get(
            "/reports/events",
            params={
                "deviceId": traccar_device_id,
                "from": dt_from.isoformat(),
                "to": dt_to.isoformat(),
            },
        )

    # ---------- geocercas ----------
    def create_geofence(self, name: str, area_wkt: str, description: str = "") -> dict:
        """area_wkt p.ej. 'CIRCLE (-0.18 -78.46, 120)'."""
        return self._post("/geofences", {"name": name, "area": area_wkt, "description": description})

    def delete_geofence(self, geofence_id: int) -> None:
        self._delete(f"/geofences/{geofence_id}")

    def link_geofence(self, traccar_device_id: int, geofence_id: int) -> None:
        self._post("/permissions", {"deviceId": traccar_device_id, "geofenceId": geofence_id})

    # ---------- comandos ----------
    def send_command(self, traccar_device_id: int, ctype: str, attributes: dict | None = None) -> Any:
        return self._post(
            "/commands/send",
            {"deviceId": traccar_device_id, "type": ctype, "attributes": attributes or {}},
        )

    # ---------- salud ----------
    def ping(self) -> bool:
        try:
            self._get("/server")
            return True
        except Exception:
            return False


def normalize_position(traccar_pos: dict) -> dict:
    """
    Convierte una posición cruda de Traccar al formato del modelo Position,
    extrayendo la telemetría del acelerómetro de `attributes`.
    """
    attrs = traccar_pos.get("attributes", {}) or {}
    ax = attrs.get("accelX") or attrs.get("ax")
    ay = attrs.get("accelY") or attrs.get("ay")
    az = attrs.get("accelZ") or attrs.get("az")
    return {
        "traccar_pos_id": traccar_pos.get("id"),
        "fija_en": traccar_pos.get("fixTime") or traccar_pos.get("deviceTime"),
        "latitud": traccar_pos.get("latitude"),
        "longitud": traccar_pos.get("longitude"),
        "altitud": traccar_pos.get("altitude"),
        "velocidad": _knots_to_kmh(traccar_pos.get("speed")),
        "rumbo": traccar_pos.get("course"),
        "precision_m": attrs.get("accuracy"),
        "satelites": attrs.get("sat"),
        "bateria": attrs.get("batteryLevel") or attrs.get("battery"),
        "accel_x": ax,
        "accel_y": ay,
        "accel_z": az,
        "magnitud_accel": attrs.get("totalAccel") or attrs.get("magnitude"),
        "motion": attrs.get("motion"),
        "attributes": attrs,
    }


def _knots_to_kmh(speed_knots: float | None) -> float | None:
    """Traccar reporta la velocidad en nudos por defecto."""
    if speed_knots is None:
        return None
    return round(speed_knots * 1.852, 2)


# Instancia compartida
traccar = TraccarClient()
