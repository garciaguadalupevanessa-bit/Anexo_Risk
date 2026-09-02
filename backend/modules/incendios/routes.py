"""Endpoints de incendios NASA FIRMS."""
from fastapi import APIRouter, Query

from modules.incendios.models import fetch_fires
from modules.incendios.schemas import FireResponse

router = APIRouter(prefix="/api/incendios", tags=["incendios"])


@router.get("", response_model=FireResponse)
def get_fires(refresh: bool = Query(default=False, alias="refresh")):
    """Detección de incendios activos en España vía satélite (NASA FIRMS).

    Los datos se cachean en memoria. Usa ?refresh=1 para forzar recarga.
    """
    return fetch_fires(force_refresh=refresh)
