"""
geofence.py — Lógica de geocercas (circular / polígono) y detección de
entrada/salida.
"""
from __future__ import annotations

import math

EARTH_R = 6_371_000.0  # m


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Distancia Haversine en metros."""
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    )
    return 2 * EARTH_R * math.asin(math.sqrt(a))


def point_in_circle(lat: float, lng: float, c_lat: float, c_lng: float, radio_m: float) -> bool:
    return haversine_m(lat, lng, c_lat, c_lng) <= radio_m


def point_in_polygon(lat: float, lng: float, poligono: list[dict]) -> bool:
    """Ray casting. `poligono` = [{'lat':..,'lng':..}, ...]."""
    inside = False
    n = len(poligono)
    j = n - 1
    for i in range(n):
        xi, yi = poligono[i]["lng"], poligono[i]["lat"]
        xj, yj = poligono[j]["lng"], poligono[j]["lat"]
        if ((yi > lat) != (yj > lat)) and (lng < (xj - xi) * (lat - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def is_inside(lat: float, lng: float, geofence) -> bool:
    """
    ¿La posición está dentro de la geocerca? Acepta un modelo Geofence o
    un dict con las mismas claves.
    """
    if isinstance(geofence, dict):
        get = geofence.get
    else:
        # getattr es seguro aunque el objeto SQLAlchemy esté "expired" tras un commit.
        get = lambda k, default=None: getattr(geofence, k, default)  # noqa: E731
    tipo = get("tipo")
    if tipo == "circular":
        return point_in_circle(lat, lng, get("centro_lat"), get("centro_lng"), get("radio_m"))
    if tipo == "poligono" and get("poligono"):
        return point_in_polygon(lat, lng, get("poligono"))
    return False


def circle_to_wkt(c_lat: float, c_lng: float, radio_m: float) -> str:
    """Formato WKT de Traccar para un círculo."""
    return f"CIRCLE ({c_lat} {c_lng}, {radio_m})"


def polygon_to_wkt(poligono: list[dict]) -> str:
    pts = ", ".join(f"{p['lat']} {p['lng']}" for p in poligono)
    if poligono:
        first = poligono[0]
        pts += f", {first['lat']} {first['lng']}"  # cerrar el anillo
    return f"POLYGON (({pts}))"
