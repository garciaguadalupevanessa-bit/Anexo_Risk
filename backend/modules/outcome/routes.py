"""Outcome API — records and queries operational outcomes."""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from models.feedback import (
    get_feedback_entries,
    get_feedback_stats,
    record_outcome,
    record_prediction,
)
from modules.outcome.schemas import OutcomeCreate, OutcomeUpdate

router = APIRouter(prefix="/api/outcomes", tags=["outcomes"])


@router.post("/prediction", status_code=201)
def create_prediction(outcome: OutcomeCreate):
    """Record a prediction for later outcome tracking."""
    result = record_prediction(
        prediction_source=outcome.prediction_source,
        model_version=outcome.model_version,
        predicted_level=outcome.predicted_level or "desconocido",
        predicted_score=outcome.predicted_score or 0.0,
        prediction_time=datetime.now(timezone.utc).isoformat(),
        h3_index=outcome.h3_index,
        lat=outcome.lat,
        lon=outcome.lon,
        needs_open=outcome.needs_open_at_prediction,
        resources_available=outcome.resources_available_at_prediction,
        incident_id=str(outcome.incident_id),
        metadata=outcome.metadata,
    )
    return result


@router.patch("/{feedback_id}/record")
def record_operational_outcome(feedback_id: int, outcome: OutcomeUpdate):
    """Record the operational outcome for a prediction."""
    result = record_outcome(
        feedback_id=feedback_id,
        incident_closed=outcome.incident_closed,
        needs_created=outcome.needs_created,
        needs_resolved=outcome.needs_resolved,
        resource_gap=outcome.resource_gap,
        response_duration_hours=outcome.response_duration_hours,
        escalation_occurred=outcome.escalation_occurred,
        metadata=outcome.metadata,
    )
    if not result or result.get("status") != "outcome_recorded":
        raise HTTPException(status_code=404, detail="Feedback entry not found")
    return result


@router.get("")
def list_outcomes(
    h3_index: Optional[str] = Query(None),
    prediction_source: Optional[str] = Query(None),
    has_outcome: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
):
    """List feedback/outcome entries."""
    return get_feedback_entries(
        h3_index=h3_index,
        prediction_source=prediction_source,
        has_outcome=has_outcome,
        limit=limit,
    )


@router.get("/stats")
def outcome_stats():
    """Get aggregate outcome statistics."""
    return get_feedback_stats()
