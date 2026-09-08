"""Timeline API — records and queries lifecycle events."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from modules.timeline.models import (
    get_incident_timeline,
    get_recent_events,
    record_event,
)
from modules.timeline.schemas import (
    TimelineEventCreate,
    TimelineEventResponse,
)

router = APIRouter(prefix="/api/timeline", tags=["timeline"])


@router.post("", response_model=TimelineEventResponse, status_code=201)
def create_timeline_event(event: TimelineEventCreate):
    """Record a new timeline event."""
    from modules.incidentes.models import get_incident

    if not get_incident(event.incident_id):
        raise HTTPException(status_code=404, detail="Incident not found")

    recorded = record_event(
        incident_id=event.incident_id,
        event_type=event.event_type.value,
        description=event.description,
        need_id=event.need_id,
        resource_id=event.resource_id,
        assignment_id=event.assignment_id,
        actor=event.actor,
        priority_score=event.priority_score,
        severity=event.severity,
        status_snapshot=event.status_snapshot,
        metadata=event.metadata,
    )
    return recorded


@router.get("/incident/{incident_id}", response_model=list[TimelineEventResponse])
def get_timeline_for_incident(
    incident_id: int,
    limit: int = Query(100, ge=1, le=500),
):
    """Get timeline events for a specific incident."""
    from modules.incidentes.models import get_incident

    if not get_incident(incident_id):
        raise HTTPException(status_code=404, detail="Incident not found")
    return get_incident_timeline(incident_id, limit=limit)


@router.get("/recent", response_model=list[TimelineEventResponse])
def get_recent(
    limit: int = Query(50, ge=1, le=200),
):
    """Get recent timeline events across all incidents."""
    return get_recent_events(limit=limit)
