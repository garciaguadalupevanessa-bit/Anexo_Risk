"""Endpoints de alertas meteorológicas."""
from fastapi import APIRouter, Query

from modules.clima.models import fetch_weather
from modules.clima.schemas import WeatherResponse

router = APIRouter(prefix="/api/clima", tags=["clima"])


@router.get("", response_model=WeatherResponse)
def get_weather(refresh: bool = Query(default=False, alias="refresh")):
    """Alertas meteorológicas para España con fallback AEMET -> Open-Meteo."""
    return fetch_weather(force_refresh=refresh)
