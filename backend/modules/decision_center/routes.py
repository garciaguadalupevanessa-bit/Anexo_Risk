"""Routes para Centro de Decisión."""
from __future__ import annotations

from fastapi import APIRouter, Query

from modules.decision_center.service import build_decision_context

router = APIRouter(prefix="/api/decision", tags=["decision-center"])


@router.get("/context")
def get_decision_context(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    severity: float = Query(0.5, ge=0, le=1),
    magnitude: float = Query(0, ge=0),
    event_type: str = Query("otro"),
    source: str = Query("manual"),
):
    """Genera contexto de decisión completo para un incidente en una ubicación."""
    incident = {
        "latitud": lat,
        "longitud": lon,
        "severity": severity,
        "magnitude": magnitude,
        "event_type": event_type,
        "source": source,
        "title": f"{event_type} en ({lat:.2f}, {lon:.2f})",
    }
    return build_decision_context(incident)


@router.get("/explain")
def explain_priority(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    severity: float = Query(0.5, ge=0, le=1),
):
    """Retorna solo la explicación de prioridad para una ubicación."""
    incident = {
        "latitud": lat,
        "longitud": lon,
        "severity": severity,
        "magnitude": 0,
        "event_type": "desconocido",
        "source": "manual",
    }
    context = build_decision_context(incident)
    return {
        "score": context["risk"]["combined_score"],
        "level": context["risk"]["priority_level"],
        "explanation": context["explanation"],
    }
