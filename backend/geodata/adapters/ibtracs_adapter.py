"""Adaptador para IBTrACS — ciclones tropicales globales.

Fuente: NOAA International Best Track Archive
Formato: CSV chunked (archivo ~200MB).
"""
from __future__ import annotations

import csv
import io
import time

import requests

_URL = (
    "https://www.ncei.noaa.gov/data/international-best-track-archive-"
    "for-climate-stewardship-ibtracs/v04r00/access/csv/"
    "ibtracs.ALL.list.v04r00.csv"
)

_CACHE_TTL = 3600  # 1 hour
_cache: dict = {}


def fetch_cyclones(max_events: int | None = None, max_rows: int = 5000) -> list[dict]:
    """Descarga ciclones tropicales desde IBTrACS.

    Parameters
    ----------
    max_events : int or None
        Límite de eventos retornados.
    max_rows : int
        Máximo de filas a leer del CSV (default 5000).

    Returns
    -------
    list[dict]
        Eventos normalizados con: source, event_type, external_id,
        title, severity, latitud, longitud, event_time, raw_data.
    """
    cache_key = "ibtracs"
    cached = _cache.get(cache_key)
    if cached is not None:
        ts, data = cached
        if time.time() - ts < _CACHE_TTL:
            return data[:max_events] if max_events else data

    try:
        resp = requests.get(_URL, timeout=60)
        resp.raise_for_status()
    except requests.RequestException:
        return cached[1] if cached else []

    events = []
    reader = csv.DictReader(io.StringIO(resp.text))

    for i, row in enumerate(reader):
        if i >= max_rows:
            break

        try:
            wind_kt = _to_float(row.get("USA_WIND"))
            pres_hpa = _to_float(row.get("USA_PRES"))
            lat = _to_float(row.get("LAT"))
            lon = _to_float(row.get("LON"))
        except (ValueError, TypeError):
            continue

        if lat is None or lon is None:
            continue

        nature = (row.get("NATURE") or "").strip()
        name = (row.get("NAME") or "").strip()
        iso_time = (row.get("ISO_TIME") or "").strip()
        sid = (row.get("SID") or "").strip()
        basin = (row.get("BASIN") or "").strip()

        if not name or name.startswith("UNNAMED"):
            name = f"Cyclone {sid[-6:]}" if sid else f"Event {i}"

        wind_kph = (wind_kt or 0) * 1.852 if wind_kt else None

        events.append({
            "source": "ibtracs",
            "event_type": "ciclon",
            "external_id": sid,
            "title": f"{name} ({basin})" if basin else name,
            "description": f"Nature: {nature}. Wind: {wind_kt} kt" if wind_kt else f"Nature: {nature}",
            "severity": _wind_to_severity(wind_kt) if wind_kt else 0.1,
            "magnitude": wind_kph,
            "depth": pres_hpa,
            "latitud": lat,
            "longitud": lon,
            "event_time": iso_time if iso_time else None,
            "raw_data": {
                "name": name,
                "nature": nature,
                "wind_kt": wind_kt,
                "pres_hpa": pres_hpa,
                "basin": basin,
            },
        })

    _cache[cache_key] = (time.time(), events)
    return events[:max_events] if max_events else events


def _to_float(val: str | None) -> float | None:
    if val is None:
        return None
    try:
        v = float(val)
        return v if v != 0 else None
    except (ValueError, TypeError):
        return None


def _wind_to_severity(wind_kt: float) -> float:
    """Convierte viento en nudos a score 0-1 (escala Saffir-Simpson)."""
    if wind_kt >= 137:
        return 1.0
    if wind_kt >= 113:
        return 0.85
    if wind_kt >= 96:
        return 0.7
    if wind_kt >= 83:
        return 0.55
    if wind_kt >= 64:
        return 0.4
    if wind_kt >= 48:
        return 0.25
    return 0.1
