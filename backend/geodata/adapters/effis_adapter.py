"""Adaptador para Copernicus EFFIS — European Forest Fire Information System.

Fuente: https://maps.effis.emergency.copernicus.eu/effis
WMS público y gratuito bajo licencia CC-BY.

Capas disponibles:
- ecmwf.fwi: Fire Weather Index (ECMWF 8km, 1-9 días forecast)
- ecmwf.isi: Initial Spread Index
- ecmwf.bui: Build Up Index
- viirs.hs: VIIRS hotspots (últimas 24h)
- modis.hs: MODIS hotspots (últimos 7 días)
- modis.ba: MODIS burnt areas
- fuel_map: Mapa de combustible
- effis_clc_2020: CORINE Land Cover 2020
"""
from __future__ import annotations

import time
from datetime import datetime, timezone, timedelta

import requests

_WMS_BASE = "https://maps.effis.emergency.copernicus.eu/effis"
_GWIS_BASE = "https://maps.effis.emergency.copernicus.eu/gwis"

_CACHE_TTL = 3600  # 1 hour
_cache: dict = {}


def get_wms_url(
    layer: str,
    bbox: str = "-24.75,27,45,72",
    width: int = 1024,
    height: int = 768,
    srs: str = "EPSG:4326",
    date: str | None = None,
    format: str = "image/png",
) -> str:
    """Genera URL WMS para una capa de EFFIS.

    Parameters
    ----------
    layer : str
        Nombre de la capa (ej: 'ecmwf.fwi', 'viirs.hs').
    bbox : str
        Bounding box en formato 'minx,miny,maxx,maxy'.
    width, height : int
        Dimensiones de la imagen.
    srs : str
        Sistema de coordenadas.
    date : str or None
        Fecha en formato YYYY-MM-DD. Si None, usa la fecha actual.
    format : str
        Formato de respuesta.

    Returns
    -------
    str
        URL completa del WMS GetMap.
    """
    if date is None:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    base = _GWIS_BASE if layer.startswith("ecmwf.") else _WMS_BASE

    params = {
        "LAYERS": layer,
        "FORMAT": format,
        "TRANSPARENT": "true",
        "SINGLETILE": "false",
        "SERVICE": "wms",
        "VERSION": "1.1.1",
        "REQUEST": "GetMap",
        "STYLES": "",
        "SRS": srs,
        "BBOX": bbox,
        "WIDTH": str(width),
        "HEIGHT": str(height),
        "TIME": date,
    }

    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{base}?{query}"


def get_fire_danger(
    lat: float | None = None,
    lon: float | None = None,
    date: str | None = None,
) -> dict:
    """Obtiene información de peligro de incendio desde EFFIS.

    Parameters
    ----------
    lat, lon : float or None
        Coordenadas del punto de interés.
    date : str or None
        Fecha (YYYY-MM-DD). Default: hoy.

    Returns
    -------
    dict
        Información de peligro de incendio con URLs de capas y metadata.
    """
    if date is None:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    cache_key = f"effis_{date}_{lat}_{lon}"
    cached = _cache.get(cache_key)
    if cached is not None:
        ts, data = cached
        if time.time() - ts < _CACHE_TTL:
            return data

    bbox = "-12,34,45,45"  # España + Mediterráneo
    if lat is not None and lon is not None:
        pad = 2.0
        bbox = f"{lon - pad},{lat - pad},{lon + pad},{lat + pad}"

    layers = {
        "fwi": {
            "name": "Fire Weather Index",
            "description": "Índice de peligro meteorológico de incendio (ECMWF 8km)",
            "url": get_wms_url("ecmwf.fwi", bbox=bbox, date=date),
            "classes": {
                "low": "< 11.2",
                "moderate": "11.2 - 21.3",
                "high": "21.3 - 38.0",
                "very_high": "38.0 - 50.0",
                "extreme": "50.0 - 70.0",
                "very_extreme": "> 70.0",
            },
        },
        "isi": {
            "name": "Initial Spread Index",
            "description": "Índice de propagación inicial",
            "url": get_wms_url("ecmwf.isi", bbox=bbox, date=date),
        },
        "bui": {
            "name": "Build Up Index",
            "description": "Índice de acumulación de combustible",
            "url": get_wms_url("ecmwf.bui", bbox=bbox, date=date),
        },
        "hotspots_viirs": {
            "name": "VIIRS Hotspots (24h)",
            "description": "Puntos calientes detectados por VIIRS en las últimas 24h",
            "url": get_wms_url("viirs.hs", bbox=bbox, date=date),
        },
        "hotspots_modis": {
            "name": "MODIS Hotspots (7 días)",
            "description": "Puntos calientes detectados por MODIS en los últimos 7 días",
            "url": get_wms_url("modis.hs", bbox=bbox, date=date),
        },
        "burnt_areas": {
            "name": "Burnt Areas",
            "description": "Áreas quemadas (MODIS)",
            "url": get_wms_url("modis.ba", bbox=bbox, date=date),
        },
        "fuel_map": {
            "name": "Fuel Map",
            "description": "Mapa de combustible forestal",
            "url": get_wms_url("fuel_map", bbox=bbox),
        },
    }

    result = {
        "source": "copernicus_effis",
        "date": date,
        "bbox": bbox,
        "layers": layers,
        "wms_base": _WMS_BASE,
        "license": "CC-BY - Copernicus Emergency Management Service",
        "documentation": "https://forest-fire.emergency.copernicus.eu/applications/data-and-services",
    }

    _cache[cache_key] = (time.time(), result)
    return result


def get_fire_danger_for_point(
    lat: float, lon: float, date: str | None = None
) -> dict:
    """Obtiene URLs de capas EFFIS para un punto específico.

    Útil para mostrar en el mapa cuando el usuario selecciona una ubicación.
    """
    data = get_fire_danger(lat=lat, lon=lon, date=date)

    point_layers = {}
    for key, layer in data["layers"].items():
        point_layers[key] = {
            "name": layer["name"],
            "description": layer.get("description", ""),
            "wms_url": layer["url"],
            "overlay_options": {
                "opacity": 0.6,
                "tiled": False,
            },
        }

    return {
        "source": "copernicus_effis",
        "point": {"lat": lat, "lon": lon},
        "date": data["date"],
        "layers": point_layers,
    }
