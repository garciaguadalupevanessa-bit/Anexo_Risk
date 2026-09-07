"""Adaptador para Smithsonian Institution — volcanes globales.

Fuente: Global Volcanism Program (GVP) — WFS
Formato: CSV vía WFS request.
"""
from __future__ import annotations

import csv
import io
import time

import requests

_WFS_URL = "https://webservices.volcano.si.edu/geoserver/GVP-VOTW/ows"
_WFS_PARAMS = {
    "service": "WFS",
    "version": "1.0.0",
    "request": "GetFeature",
    "typeName": "GVP-VOTW:Smithsonian_VOTW_Holocene_Volcanoes",
    "outputFormat": "csv",
    "maxFeatures": 2000,
}

_CACHE_TTL = 86400  # 24 hours (volcano data changes slowly)
_cache: dict = {}


def fetch_volcanoes(max_events: int | None = None) -> list[dict]:
    """Descarga volcanes del Holoceno desde Smithsonian GVP.

    Parameters
    ----------
    max_events : int or None
        Límite de volcanes retornados.

    Returns
    -------
    list[dict]
        Volcanes normalizados con: source, event_type, external_id,
        title, severity, magnitude (elevación), latitud, longitud.
    """
    cache_key = "smithsonian"
    cached = _cache.get(cache_key)
    if cached is not None:
        ts, data = cached
        if time.time() - ts < _CACHE_TTL:
            return data[:max_events] if max_events else data

    try:
        resp = requests.get(_WFS_URL, params=_WFS_PARAMS, timeout=60)
        resp.raise_for_status()
    except requests.RequestException:
        return cached[1] if cached else []

    reader = csv.DictReader(io.StringIO(resp.text))
    events = []

    for row in reader:
        try:
            lat = float(row.get("Latitude") or 0)
            lon = float(row.get("Longitude") or 0)
            elevation = float(row.get("Elevation") or 0)
        except (ValueError, TypeError):
            continue

        if lat == 0 and lon == 0:
            continue

        name = (row.get("VolcanoName") or "").strip()
        v_type = (row.get("VolcanoType") or "").strip()
        country = (row.get("Country") or "").strip()
        last_eruption = (row.get("LastEruptionYear") or "").strip()
        volcano_number = (row.get("VolcanoNumber") or "").strip()

        events.append({
            "source": "smithsonian",
            "event_type": "volcan",
            "external_id": volcano_number,
            "title": name,
            "description": f"Type: {v_type}. Elevation: {elevation}m. Country: {country}",
            "severity": _elevation_to_severity(elevation),
            "magnitude": elevation,
            "depth": None,
            "latitud": lat,
            "longitud": lon,
            "event_time": None,
            "raw_data": {
                "volcano_name": name,
                "volcano_type": v_type,
                "elevation": elevation,
                "country": country,
                "last_eruption": last_eruption,
            },
        })

    _cache[cache_key] = (time.time(), events)
    return events[:max_events] if max_events else events


def _elevation_to_severity(elevation: float) -> float:
    """Convierte elevación a score de riesgo 0-1."""
    if elevation >= 4000:
        return 0.9
    if elevation >= 3000:
        return 0.7
    if elevation >= 2000:
        return 0.5
    if elevation >= 1000:
        return 0.3
    return 0.2
