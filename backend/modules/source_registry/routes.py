"""Source Registry API endpoints."""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from modules.source_registry.schemas import (
    SourceCreate, SourceUpdate, SourceResponse, SourceHealthResponse,
)
from modules.source_registry import models

router = APIRouter(prefix="/api/sources", tags=["source-registry"])


@router.get("", response_model=list[SourceResponse])
def list_sources(
    scope: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    source_type: Optional[str] = Query(None),
):
    """List all registered data sources."""
    return models.list_sources(scope=scope, status=status, source_type=source_type)


@router.get("/health", response_model=list[SourceHealthResponse])
def get_source_health():
    """Get health status of all sources."""
    return models.get_source_health_summary()


@router.get("/{source_id}", response_model=SourceResponse)
def get_source(source_id: str):
    """Get a single source by ID."""
    source = models.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return source


@router.post("", response_model=SourceResponse, status_code=201)
def register_source(data: SourceCreate):
    """Register a new data source."""
    existing = models.get_source(data.id)
    if existing:
        raise HTTPException(status_code=409, detail="Source ID already exists")
    return models.register_source(data.model_dump())


@router.patch("/{source_id}", response_model=SourceResponse)
def update_source(source_id: str, data: SourceUpdate):
    """Update source registry entry."""
    existing = models.get_source(source_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Source not found")
    updates = data.model_dump(exclude_unset=True)
    if "data_types" in updates:
        updates["data_types"] = json.dumps(updates["data_types"]) if updates["data_types"] else None
    if "metadata" in updates:
        updates["metadata_json"] = updates.pop("metadata")
    return models.register_source({**existing, **updates})


@router.delete("/{source_id}")
def delete_source(source_id: str):
    """Remove a source from the registry."""
    existing = models.get_source(source_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Source not found")
    models.delete_source(source_id)
    return {"detail": "Source removed"}


@router.post("/{source_id}/status", response_model=SourceResponse)
def update_source_status(
    source_id: str,
    status: str = Query(...),
    error: Optional[str] = Query(None),
    latency_ms: Optional[float] = Query(None),
):
    """Update source health status."""
    existing = models.get_source(source_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Source not found")
    from datetime import datetime, timezone
    last_fetch = datetime.now(timezone.utc).isoformat() if status == "active" and not error else None
    return models.update_source_status(source_id, status, last_fetch, error, latency_ms)


import json
