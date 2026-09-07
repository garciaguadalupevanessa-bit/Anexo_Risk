"""Servicio de análisis geoespacial con H3.

Proporciona funciones de indexación espacial y agregación usando H3.
"""
from __future__ import annotations

import math

try:
    import h3
except ImportError:
    h3 = None


def latlon_to_h3(lat: float, lon: float, resolution: int = 7) -> str | None:
    """Convierte coordenadas a índice H3."""
    if h3 is None:
        return None
    try:
        return h3.latlng_to_cell(lat, lon, resolution)
    except Exception:
        return None


def h3_to_latlon(h3_index: str) -> tuple[float, float] | None:
    """Convierte índice H3 a coordenadas del centroide."""
    if h3 is None:
        return None
    try:
        lat, lon = h3.cell_to_latlng(h3_index)
        return (lat, lon)
    except Exception:
        return None


def get_h3_neighbors(h3_index: str, k: int = 1) -> list[str]:
    """Retorna vecinos H3 dentro del radio k."""
    if h3 is None:
        return []
    try:
        return list(h3.grid_disk(h3_index, k))
    except Exception:
        return []


def compute_h3_aggregation(events: list[dict], resolution: int = 7) -> dict[str, dict]:
    """Agrega eventos por celda H3.

    Parameters
    ----------
    events : list[dict]
        Lista de eventos con 'latitud' y 'longitud'.
    resolution : int
        Resolución H3 (0-15, default 7 ≈ 5km²).

    Returns
    -------
    dict[str, dict]
        Mapa de h3_index -> {event_count, avg_severity, events}.
    """
    cells: dict[str, dict] = {}

    for event in events:
        lat = event.get("latitud")
        lon = event.get("longitud")
        if lat is None or lon is None:
            continue

        h3_idx = latlon_to_h3(lat, lon, resolution)
        if h3_idx is None:
            continue

        if h3_idx not in cells:
            cells[h3_idx] = {
                "h3_index": h3_idx,
                "resolution": resolution,
                "event_count": 0,
                "total_severity": 0.0,
                "events": [],
            }

        cells[h3_idx]["event_count"] += 1
        cells[h3_idx]["total_severity"] += event.get("severity", 0)
        cells[h3_idx]["events"].append(event)

    for cell in cells.values():
        if cell["event_count"] > 0:
            cell["avg_severity"] = cell["total_severity"] / cell["event_count"]
        else:
            cell["avg_severity"] = 0.0

    return cells


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula distancia Haversine en km entre dos puntos."""
    R = 6371.0
    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def find_nearby(
    lat: float, lon: float, items: list[dict], radius_km: float = 50.0
) -> list[dict]:
    """Encuentra elementos dentro de un radio en km."""
    results = []
    for item in items:
        ilat = item.get("latitud") or item.get("lat")
        ilon = item.get("longitud") or item.get("lon")
        if ilat is None or ilon is None:
            continue
        dist = haversine_distance(lat, lon, ilat, ilon)
        if dist <= radius_km:
            results.append({**item, "_distance_km": round(dist, 2)})
    results.sort(key=lambda x: x["_distance_km"])
    return results
