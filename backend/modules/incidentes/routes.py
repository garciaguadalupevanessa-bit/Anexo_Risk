"""Incidents API — CRUD + lifecycle management."""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from modules.incidentes.models import (
    create_incident,
    get_active_incident_count,
    get_incident,
    list_incidents,
    update_incident_scores,
    update_incident_status,
)
from modules.incidentes.schemas import (
    IncidentCreate,
    IncidentResponse,
    IncidentStatusUpdate,
)
from modules.timeline.models import record_event, get_incident_timeline
from modules.necesidades.schemas import NeedCreate
from modules.necesidades.models import create_need
from models.feedback import get_feedback_entries

router = APIRouter(prefix="/api/incidents", tags=["incidents"])

SEVERITY_TO_FLOAT = {
    "verde": 0.25,
    "amarilla": 0.5,
    "naranja": 0.75,
    "roja": 1.0,
}


@router.get("", response_model=list[IncidentResponse])
def list_all_incidents(
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
):
    """List incidents with optional filters."""
    return list_incidents(
        status=status,
        severity=severity,
        event_type=event_type,
        is_active=is_active,
        limit=limit,
    )


@router.get("/count")
def count_active_incidents():
    """Count active incidents."""
    return {"active_count": get_active_incident_count()}


@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident_by_id(incident_id: int):
    """Get a single incident."""
    incident = get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.post("", response_model=IncidentResponse, status_code=201)
def create_new_incident(incident: IncidentCreate):
    """Create a new incident and record the detection in the timeline."""
    created = create_incident(
        title=incident.title,
        lat=incident.lat,
        lon=incident.lon,
        event_type=incident.event_type.value,
        source=incident.source,
        external_id=incident.external_id,
        severity=incident.severity.value,
        magnitude=incident.magnitude,
        description=incident.description,
        direccion=incident.direccion,
        metadata=incident.metadata,
    )
    incident_id = created.get("id")
    if incident_id:
        try:
            record_event(
                incident_id=incident_id,
                event_type="detected",
                description=f"Incidente detectado: {incident.title}",
                priority_score=None,
                severity=incident.severity.value,
                status_snapshot="detectado",
            )
        except Exception:
            pass
    return created


@router.patch("/{incident_id}", response_model=IncidentResponse)
def update_incident(incident_id: int, update: IncidentStatusUpdate):
    """Update incident status."""
    existing = get_incident(incident_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Incident not found")

    updated = update_incident_status(incident_id, update.status.value)
    if not updated:
        raise HTTPException(status_code=400, detail="Status update failed")
    return updated


@router.patch("/{incident_id}/scores", response_model=IncidentResponse)
def update_scores(
    incident_id: int,
    priority_score: Optional[float] = Query(None),
    exposure_score: Optional[float] = Query(None),
):
    """Update incident computed scores."""
    existing = get_incident(incident_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Incident not found")
    updated = update_incident_scores(incident_id, priority_score, exposure_score)
    return updated


@router.get("/{incident_id}/timeline")
def get_timeline(incident_id: int, limit: int = Query(100, ge=1, le=500)):
    """Get the timeline of events for an incident."""
    existing = get_incident(incident_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Incident not found")
    events = get_incident_timeline(incident_id, limit=limit)
    return {"incident_id": incident_id, "events": events}


@router.post("/{incident_id}/analyze")
def analyze_incident(incident_id: int):
    """Build decision context, update scores, and record analysis in timeline.

    This is the vertical slice entry point:
    incident → decision context → risk scores → timeline
    """
    existing = get_incident(incident_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Incident not found")

    from modules.decision_center.service import build_decision_context
    from modules.necesidades.models import list_needs as db_list_needs
    from modules.recursos.models import list_resources

    needs = []
    try:
        needs = db_list_needs()
    except Exception:
        pass

    resources = []
    try:
        resources = list_resources()
    except Exception:
        pass

    incident_for_context = dict(existing)
    incident_for_context["severity"] = SEVERITY_TO_FLOAT.get(existing.get("severity", ""), 0.5)
    if incident_for_context.get("magnitude") is None:
        incident_for_context["magnitude"] = 0.0

    context = build_decision_context(incident_for_context, needs=needs, resources=resources)

    risk = context.get("risk", {})
    operation = context.get("operation", {})
    updated = update_incident_scores(
        incident_id,
        priority_score=risk.get("combined_score"),
        exposure_score=context.get("impact", {}).get("exposure_score"),
    )

    try:
        record_event(
            incident_id=incident_id,
            event_type="evaluated",
            description=f"Evaluación completada. Riesgo: {risk.get('priority_level', 'informativo')} ({risk.get('combined_score', 0):.1f}/100)",
            priority_score=risk.get("combined_score"),
            severity=existing.get("severity"),
            status_snapshot="evaluado",
        )
    except Exception:
        pass

    # Auto-record prediction for feedback loop
    try:
        from models.feedback import record_prediction
        record_prediction(
            prediction_source="anexo_risk",
            model_version=risk.get("methodology_version", "rules-v1"),
            predicted_level=risk.get("priority_level", "informativo"),
            predicted_score=risk.get("combined_score", 0),
            prediction_time=datetime.now(timezone.utc).isoformat(),
            h3_index=existing.get("h3_index"),
            lat=existing.get("lat"),
            lon=existing.get("lon"),
            needs_open=operation.get("needs_open"),
            resources_available=operation.get("resources_available"),
            incident_id=str(incident_id),
            metadata={"risk_source": risk.get("source"), "event_type": existing.get("event_type")},
        )
    except Exception:
        pass

    return {
        "incident_id": incident_id,
        "decision_context": context,
        "scores_updated": updated is not None,
    }


@router.post("/{incident_id}/resolve")
def resolve_incident(incident_id: int):
    """Mark incident as resolved and record outcome for feedback loop."""
    existing = get_incident(incident_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Incident not found")

    updated = update_incident_status(incident_id, "resuelto")
    if not updated:
        raise HTTPException(status_code=400, detail="Status update failed")

    try:
        record_event(
            incident_id=incident_id,
            event_type="resolved",
            description="Incidente resuelto",
            severity=existing.get("severity"),
            status_snapshot="resuelto",
        )
    except Exception:
        pass

    # Record outcome for feedback loop
    try:
        from models.feedback import record_outcome
        entries = get_feedback_entries(incident_id=str(incident_id), limit=1)
        if entries:
            record_outcome(
                feedback_id=entries[0].get("id"),
                incident_closed=True,
                metadata={"resolved_at": datetime.now(timezone.utc).isoformat()},
            )
    except Exception:
        pass

    return {"incident_id": incident_id, "status": "resuelto"}


@router.post("/{incident_id}/needs", status_code=201)
def create_need_for_incident(incident_id: int, need: NeedCreate):
    """Create a need linked to this incident and record in timeline."""
    existing = get_incident(incident_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Incident not found")

    created = create_need(need)

    try:
        record_event(
            incident_id=incident_id,
            event_type="need_created",
            description=f"Necesidad #{created.get('id')} creada: {created.get('tipo')}",
            need_id=created.get("id"),
            priority_score=None,
            severity=existing.get("severity"),
            status_snapshot="en_respuesta",
        )
        update_incident_status(incident_id, "en_respuesta")
    except Exception:
        pass

    return created
