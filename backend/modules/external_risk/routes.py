"""External Risk API — exposes GeoRisk scientific risk data.

Provides endpoints for:
- Anexo_Risk internal consumption (Decision Center)
- External clients wanting scientific risk analysis

All data comes from GeoRisk Finder via the integration client.
"""
from __future__ import annotations

from fastapi import APIRouter, Query

from integrations.georisk_client import (
    get_cell_risk,
    get_cell_events,
    get_ranking,
    is_georisk_available,
    get_circuit_status,
)

router = APIRouter(prefix="/api/external-risk", tags=["external-risk"])


@router.get("/cell/{h3_index}")
def get_external_risk(h3_index: str):
    """Get scientific risk profile for an H3 cell from GeoRisk.

    Returns the GeoRisk analysis if available, or a fallback indicating
    GeoRisk is unavailable.
    """
    if not is_georisk_available():
        return {
            "status": "unavailable",
            "message": "GeoRisk no disponible — usando riesgo operacional local",
            "h3_index": h3_index,
            "source": "georisk",
            "circuit": get_circuit_status(),
        }

    data = get_cell_risk(h3_index)
    if data is None:
        return {
            "status": "not_found",
            "message": f"Celda H3 {h3_index} no encontrada en GeoRisk",
            "h3_index": h3_index,
            "source": "georisk",
        }

    return {
        "status": "ok",
        "data": data,
        "source": "georisk",
    }


@router.get("/cell/{h3_index}/events")
def get_external_events(h3_index: str):
    """Get nearby hazard events for an H3 cell from GeoRisk."""
    if not is_georisk_available():
        return {
            "status": "unavailable",
            "message": "GeoRisk no disponible",
            "h3_index": h3_index,
            "source": "georisk",
            "circuit": get_circuit_status(),
        }

    data = get_cell_events(h3_index)
    if data is None:
        return {
            "status": "not_found",
            "message": f"Sin eventos para celda {h3_index}",
            "h3_index": h3_index,
            "source": "georisk",
        }

    return {
        "status": "ok",
        "data": data,
        "source": "georisk",
    }


@router.get("/ranking")
def get_external_ranking(limit: int = Query(10, ge=1, le=100)):
    """Get top risk cells from GeoRisk."""
    if not is_georisk_available():
        return {
            "status": "unavailable",
            "message": "GeoRisk no disponible",
            "source": "georisk",
            "circuit": get_circuit_status(),
            "cells": [],
        }

    data = get_ranking(limit)
    if data is None:
        return {
            "status": "error",
            "message": "No se pudo obtener ranking de GeoRisk",
            "source": "georisk",
            "cells": [],
        }

    return {
        "status": "ok",
        "source": "georisk",
        "cells": data,
    }


@router.get("/status")
def get_integration_status():
    """Get GeoRisk integration status (circuit breaker, availability)."""
    circuit = get_circuit_status()
    available = is_georisk_available()
    return {
        "georisk_available": available,
        "circuit_breaker": circuit,
        "source": "anexo_risk",
    }
