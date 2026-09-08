"""Event Correlation API endpoints."""
from fastapi import APIRouter, Query
from typing import Optional
from services.correlation import correlate_events, create_incident_from_cluster
from modules.normalized_events import models as event_models

router = APIRouter(prefix="/api/correlation", tags=["correlation"])


@router.post("/run")
def run_correlation(
    source: Optional[str] = Query(None, description="Filter by source"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    max_distance_km: float = Query(50.0, ge=1, le=500),
    max_time_hours: float = Query(2.0, ge=0.1, le=48),
    create_incidents: bool = Query(False, description="Auto-create incidents from clusters"),
):
    """Run correlation on active events."""
    events = event_models.list_events(
        source=source, entity_type=entity_type, is_active=True, limit=1000
    )

    clusters = correlate_events(events, max_distance_km, max_time_hours)

    incidents_created = []
    if create_incidents:
        for cluster in clusters:
            if cluster["count"] >= 2:  # Only create incidents for multi-event clusters
                incident = create_incident_from_cluster(cluster)
                if incident:
                    incidents_created.append(incident["id"])

    return {
        "events_processed": len(events),
        "clusters_found": len(clusters),
        "multi_event_clusters": sum(1 for c in clusters if c["count"] >= 2),
        "incidents_created": len(incidents_created),
        "clusters": [
            {
                "count": c["count"],
                "entity_type": c["entity_type"],
                "sources": c["sources"],
                "avg_confidence": round(c["avg_confidence"], 3),
            }
            for c in clusters
        ],
    }


@router.get("/clusters")
def get_clusters(
    source: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    max_distance_km: float = Query(50.0, ge=1, le=500),
    max_time_hours: float = Query(2.0, ge=0.1, le=48),
):
    """Get correlation clusters without creating incidents."""
    events = event_models.list_events(
        source=source, entity_type=entity_type, is_active=True, limit=1000
    )
    clusters = correlate_events(events, max_distance_km, max_time_hours)
    return {
        "events_processed": len(events),
        "clusters": [
            {
                "count": c["count"],
                "entity_type": c["entity_type"],
                "sources": c["sources"],
                "avg_confidence": round(c["avg_confidence"], 3),
                "event_ids": [e.get("id") for e in c["events"]],
            }
            for c in clusters
        ],
    }
