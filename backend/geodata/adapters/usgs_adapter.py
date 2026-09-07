"""Adaptador para USGS Earthquake Catalog — sismos globales.

Fuente: https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_month.csv
Formato: CSV con ~20,000 eventos del último mes.
"""
from __future__ import annotations

import csv
import io
import time
from datetime import datetime, timezone

import requests

_BASE_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary"

_FEEDS = {
    "hour": f"{_BASE_URL}/all_hour.csv",
    "day": f"{_BASE_URL}/all_day.csv",
    "week": f"{_BASE_URL}/all_week.csv",
    "month": f"{_BASE_URL}/all_month.csv",
}

_cache: dict = {}
_CACHE_TTL = 900  # 15 minutes


def fetch_earthquakes(feed: str = "week", max_events: int | None = None) -> list[dict]:
    """Descarga terremotos desde USGS y devuelve eventos normalizados.

    Parameters
    ----------
    feed : str
        Periodo: 'hour', 'day', 'week', 'month'. Default: 'week'.
    max_events : int or None
        Límite máximo de eventos a retornar. None = todos.

    Returns
    -------
    list[dict]
        Lista de eventos normalizados con: source, event_type, external_id,
        title, magnitude, depth, latitud, longitud, event_time, raw_data.
    """
    url = _FEEDS.get(feed, _FEEDS["week"])
    cache_key = f"usgs_{feed}"

    cached = _cache.get(cache_key)
    if cached is not None:
        ts, data = cached
        if time.time() - ts < _CACHE_TTL:
            return data[:max_events] if max_events else data

    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
    except requests.RequestException:
        return cached[1] if cached else []

    reader = csv.DictReader(io.StringIO(resp.text))
    events = []

    for row in reader:
        try:
            mag = float(row.get("mag") or 0)
            depth = float(row.get("depth") or 0)
            lat = float(row.get("latitude") or 0)
            lon = float(row.get("longitude") or 0)
        except (ValueError, TypeError):
            continue

        if lat == 0 and lon == 0:
            continue

        event_id = row.get("id", "")
        place = row.get("place", "")
        event_time_ms = row.get("time")

        event_time = None
        if event_time_ms:
            try:
                event_time = datetime.fromtimestamp(
                    int(event_time_ms) / 1000, tz=timezone.utc
                ).isoformat()
            except (ValueError, TypeError):
                pass

        events.append({
            "source": "usgs",
            "event_type": "terremoto",
            "external_id": event_id,
            "title": f"M{mag:.1f} - {place}" if place else f"M{mag:.1f}",
            "description": place,
            "severity": _mag_to_severity(mag),
            "magnitude": mag,
            "depth": depth,
            "latitud": lat,
            "longitud": lon,
            "event_time": event_time,
            "raw_data": row,
        })

    _cache[cache_key] = (time.time(), events)
    return events[:max_events] if max_events else events


def _mag_to_severity(mag: float) -> float:
    """Convierte magnitud Richter a score 0-1."""
    if mag >= 7.0:
        return 1.0
    if mag >= 6.0:
        return 0.8
    if mag >= 5.0:
        return 0.6
    if mag >= 4.0:
        return 0.4
    if mag >= 3.0:
        return 0.2
    return 0.1
