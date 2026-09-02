"""Servicio de alertas meteorológicas con fallback.

Prioridad:
1. AEMET (Agencia Estatal de Meteorología) — datos oficiales España
2. Open-Meteo — fallback internacional sin auth
"""
import time
from datetime import datetime
from typing import Optional

import requests

from config import AEMET_API_KEY

AEMET_AVISOS_URL = "https://www.aemet.es/es/api/avisos_cap/llamame_api"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

# Bounding box España para Open-Meteo
SPAIN_LAT = 40.4168
SPAIN_LON = -3.7038

_CACHE: Optional[dict] = None
_CACHE_TIME: float = 0
CACHE_TTL = 1800  # 30 minutos


def _is_cache_valid() -> bool:
    return _CACHE is not None and (time.time() - _CACHE_TIME) < CACHE_TTL


def _fetch_aemet() -> Optional[list]:
    """Intenta obtener avisos de AEMET. Retorna None si falla."""
    if not AEMET_API_KEY:
        return None
    try:
        headers = {
            "api_key": AEMET_API_KEY,
            "Accept": "application/json",
        }
        # 1) Obtener listado de avisos
        resp = requests.get(
            f"{AEMET_AVISOS_URL}?aemet_aviso_cap=false",
            headers=headers,
            timeout=8,
        )
        if not resp.ok:
            return None
        # La API de AEMET suele devolver URLs a documentos individuales.
        # Estructura típica: lista de {id, fecha, ambito, tipo, ...}
        data = resp.json()
        if not isinstance(data, list):
            return None
        # Por simplicidad, devolvemos los primeros 10.
        return data[:10] if data else None
    except (requests.RequestException, ValueError):
        return None


def _fetch_open_meteo() -> Optional[list]:
    """Fallback: Open-Meteo (sin auth, gratis).

    Genera alertas derivadas de condiciones meteorológicas
    potencialmente peligrosas (viento extremo, calor, lluvia fuerte).
    """
    try:
        url = (
            f"{OPEN_METEO_URL}"
            f"?latitude={SPAIN_LAT}&longitude={SPAIN_LON}"
            "&current=temperature_2m,wind_speed_10m,precipitation,wind_gusts_10m"
            "&hourly=temperature_2m,precipitation_probability,wind_speed_10m"
            "&forecast_days=1"
        )
        resp = requests.get(url, timeout=8)
        resp.raise_for_status()
        data = resp.json()

        current = data.get("current", {})
        alertas = []
        ahora = datetime.now().strftime("%Y-%m-%dT%H:%M")

        temp = current.get("temperature_2m", 0)
        viento = current.get("wind_speed_10m", 0)
        rafaga = current.get("wind_gusts_10m", 0)
        lluvia = current.get("precipitation", 0)

        if temp >= 38:
            alertas.append({
                "id": f"om-heat-{ahora}",
                "tipo": "calor",
                "nivel": "rojo" if temp >= 42 else "naranja",
                "titulo": f"Temperatura extrema: {temp}°C",
                "descripcion": "Riesgo alto para la salud. Evite exposición prolongada.",
                "region": "España",
                "fecha": ahora,
                "fuente": "Open-Meteo",
            })
        if rafaga >= 70:
            alertas.append({
                "id": f"om-wind-{ahora}",
                "tipo": "viento",
                "nivel": "rojo" if rafaga >= 100 else "naranja",
                "titulo": f"Ráfagas de viento: {rafaga} km/h",
                "descripcion": "Precaución: posible caída de árboles y objetos.",
                "region": "España",
                "fecha": ahora,
                "fuente": "Open-Meteo",
            })
        elif rafaga >= 50:
            alertas.append({
                "id": f"om-wind-{ahora}",
                "tipo": "viento",
                "nivel": "amarillo",
                "titulo": f"Viento fuerte: {rafaga} km/h",
                "descripcion": "Ráfagas moderadas.",
                "region": "España",
                "fecha": ahora,
                "fuente": "Open-Meteo",
            })
        if lluvia >= 20:
            alertas.append({
                "id": f"om-rain-{ahora}",
                "tipo": "lluvia",
                "nivel": "naranja" if lluvia >= 50 else "amarillo",
                "titulo": f"Precipitación intensa: {lluvia} mm",
                "descripcion": "Posibles inundaciones locales.",
                "region": "España",
                "fecha": ahora,
                "fuente": "Open-Meteo",
            })
        return alertas
    except (requests.RequestException, ValueError):
        return None


def _normalize_aemet(items: list) -> list:
    """Normaliza avisos AEMET al esquema interno."""
    result = []
    for item in items:
        nivel_raw = str(item.get("nivel", "amarillo")).lower()
        nivel = nivel_raw if nivel_raw in ("verde", "amarillo", "naranja", "rojo") else "amarillo"
        result.append({
            "id": f"aemet-{item.get('id', len(result))}",
            "tipo": item.get("tipo", "general").lower(),
            "nivel": nivel,
            "titulo": item.get("titulo") or item.get("name") or "Aviso AEMET",
            "descripcion": item.get("descripcion") or item.get("texto") or "",
            "region": item.get("ambito") or item.get("zona") or "España",
            "fecha": item.get("fecha", ""),
            "fuente": "AEMET",
        })
    return result


def fetch_weather(force_refresh: bool = False) -> dict:
    """Obtiene alertas meteorológicas para España.

    Intenta primero AEMET, si falla usa Open-Meteo como fallback.
    """
    global _CACHE, _CACHE_TIME

    if not force_refresh and _is_cache_valid():
        return _CACHE

    aemet_data = _fetch_aemet()
    fallback = False

    if aemet_data:
        alertas = _normalize_aemet(aemet_data)
        fuente = "AEMET (oficial España)"
    else:
        open_meteo = _fetch_open_meteo()
        if open_meteo is None:
            _CACHE = {
                "total": 0,
                "alertas": [],
                "fuente": "AEMET + Open-Meteo",
                "cached_at": datetime.now().isoformat(),
                "fallback_activado": True,
                "error": "Ninguna fuente de clima disponible",
            }
            _CACHE_TIME = time.time()
            return _CACHE
        alertas = open_meteo
        fuente = "Open-Meteo (fallback)"
        fallback = True

    _CACHE = {
        "total": len(alertas),
        "alertas": alertas,
        "fuente": fuente,
        "cached_at": datetime.now().isoformat(),
        "fallback_activado": fallback,
    }
    _CACHE_TIME = time.time()
    return _CACHE
