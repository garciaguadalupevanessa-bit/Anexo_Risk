"""Servicio de incendios NASA FIRMS.

Usa la API pública de NASA FIRMS para detectar incendios activos
vía satélite (VIIRS) en la zona de España.
"""
import csv
import io
import time
from datetime import datetime, timedelta
from typing import Optional

import requests

from config import NASA_FIRMS_API_KEY, NASA_FIRMS_CACHE_TTL_SECONDS

NASA_FIRMS_URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv/{key}/{source}/{bbox}/{days}"

# Bounding box de España peninsular + Baleares + Canarias
# west, south, east, north
SPAIN_BBOX = "-18,27,4,44"

_CACHE: Optional[dict] = None
_CACHE_TIME: float = 0


def _is_cache_valid() -> bool:
    if _CACHE is None:
        return False
    return (time.time() - _CACHE_TIME) < NASA_FIRMS_CACHE_TTL_SECONDS


def fetch_fires(force_refresh: bool = False) -> dict:
    """Obtiene detecciones de incendios en España desde NASA FIRMS.

    Resultados cacheados en memoria por NASA_FIRMS_CACHE_TTL_SECONDS.
    """
    global _CACHE, _CACHE_TIME

    if not force_refresh and _is_cache_valid():
        return _CACHE

    if not NASA_FIRMS_API_KEY:
        return {
            "total": 0,
            "detecciones": [],
            "fuente": "NASA FIRMS (sin API key configurada)",
            "cached_at": datetime.now().isoformat(),
            "error": "Configura NASA_FIRMS_API_KEY en .env",
        }

    url = NASA_FIRMS_URL.format(
        key=NASA_FIRMS_API_KEY,
        source="VIIRS_SNPP_NRT",
        bbox=SPAIN_BBOX,
        days=1,
    )

    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as exc:
        return {
            "total": 0,
            "detecciones": [],
            "fuente": "NASA FIRMS",
            "cached_at": datetime.now().isoformat(),
            "error": f"No se pudo obtener datos de incendios: {exc}",
        }

    reader = csv.DictReader(io.StringIO(resp.text))
    detecciones = []
    for row in reader:
        try:
            lat = float(row.get("latitude", 0))
            lon = float(row.get("longitude", 0))
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                continue
            brillo = float(row.get("bright_ti4", 0) or 0)
            confianza_raw = row.get("confidence", "nominal") or "nominal"
            confianza = str(confianza_raw).lower()
            if confianza not in ("low", "nominal", "high"):
                confianza = "nominal"
            date_str = row.get("acq_date", "") or ""
            t = row.get("acq_time", "") or ""
            fecha = f"{date_str} {t[:2]}:{t[2:]}" if t else date_str
            fire_id = f"VIIRS-{date_str}-{lat:.4f}-{lon:.4f}"
            detecciones.append({
                "id": fire_id,
                "satellite": "VIIRS SNPP",
                "lat": lat,
                "lon": lon,
                "brightness": brillo,
                "confidence": confianza,
                "acq_date": date_str,
                "acq_time": row.get("acq_time", ""),
                "frp": float(row.get("frp", 0) or 0),
                "country": "España",
            })
        except (ValueError, KeyError):
            continue

    _CACHE = {
        "total": len(detecciones),
        "detecciones": detecciones,
        "fuente": "NASA FIRMS — VIIRS SNPP",
        "cached_at": datetime.now().isoformat(),
    }
    _CACHE_TIME = time.time()
    return _CACHE
