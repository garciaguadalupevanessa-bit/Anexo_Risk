"""Live Ingestion API endpoints."""
from fastapi import APIRouter, Query
from typing import Optional
from services.live_ingestion import ingestion_service
from services.source_health import get_source_freshness_summary, classify_freshness

router = APIRouter(prefix="/api/live", tags=["live-data"])


@router.post("/ingest")
def trigger_ingestion(
    sources: Optional[str] = Query(None, description="Comma-separated source IDs"),
    timeout: int = Query(30, ge=5, le=120),
):
    """Trigger ingestion from specified or all sources."""
    source_list = sources.split(",") if sources else None
    return ingestion_service.ingest_all(sources=source_list, timeout_per_source=timeout)


@router.get("/ingest/{source_id}")
def ingest_single_source(
    source_id: str,
    timeout: int = Query(30, ge=5, le=120),
):
    """Ingest from a single source."""
    return ingestion_service.fetch_source(source_id, timeout)


@router.get("/freshness")
def get_freshness():
    """Get freshness summary for all sources."""
    summary = get_source_freshness_summary()
    for s in summary:
        s["freshness_class"] = classify_freshness(
            s.get("freshness_seconds"), s.get("status", "unknown")
        )
    return {"sources": summary}


@router.get("/circuit-breaker")
def get_circuit_breaker_state():
    """Get circuit breaker state for all sources."""
    sources = ["gdacs", "usgs", "firms", "aemet", "open-meteo", "effis", "georisk"]
    return {
        "breakers": {
            s: ingestion_service.circuit_breaker.get_state(s)
            for s in sources
        }
    }
