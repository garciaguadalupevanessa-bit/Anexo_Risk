"""Normalized Events API endpoints."""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from modules.normalized_events.schemas import (
    NormalizedEventCreate, NormalizedEventResponse,
    EventBatchCreate, EventBatchResponse,
)
from modules.normalized_events import models

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("", response_model=list[NormalizedEventResponse])
def list_events(
    entity_type: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    h3_index: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    since: Optional[str] = Query(None),
    until: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """List normalized events with filters."""
    return models.list_events(
        entity_type=entity_type, source=source, h3_index=h3_index,
        severity=severity, status=status, is_active=is_active,
        since=since, until=until, limit=limit, offset=offset,
    )


@router.get("/count")
def count_events(
    entity_type: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
):
    """Count events."""
    return {"count": models.count_events(entity_type, source, is_active)}


@router.get("/{event_id}", response_model=NormalizedEventResponse)
def get_event(event_id: str):
    """Get a single event."""
    event = models.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.post("", response_model=NormalizedEventResponse, status_code=201)
def create_event(data: NormalizedEventCreate):
    """Store a normalized event."""
    return models.store_event(data.model_dump())


@router.post("/batch", response_model=EventBatchResponse, status_code=201)
def create_events_batch(data: EventBatchCreate):
    """Store multiple events."""
    events = [e.model_dump() for e in data.events]
    stored = models.store_events_batch(events)
    return EventBatchResponse(stored=len(stored), total=len(events))


@router.delete("/{event_id}")
def deactivate_event(event_id: str):
    """Soft-deactivate an event."""
    event = models.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    models.deactivate_event(event_id)
    return {"detail": "Event deactivated"}
