"""Endpoints de incendios NASA FIRMS."""
from fastapi import APIRouter, Query

from modules.incendios.models import fetch_fires, FIRE_ZONES
from modules.incendios.schemas import FireResponse

router = APIRouter(prefix="/api/incendios", tags=["incendios"])


@router.get("", response_model=FireResponse)
def get_fires(
    refresh: bool = Query(default=False, alias="refresh"),
    zone: str = Query(default="spain", alias="zone"),
):
    """Detección de incendios activos vía satélite (NASA FIRMS).

    Zones: spain, europa, mediterraneo, global.
    Los datos se cachean en memoria. Usa ?refresh=1 para forzar recarga.
    """
    return fetch_fires(force_refresh=refresh, zone=zone)
