"""Accessibility API endpoints."""
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import List
from services.accessibility import find_path, check_accessibility, batch_accessibility, get_blocked_routes

router = APIRouter(prefix="/api/accessibility", tags=["accessibility"])


class BatchRequest(BaseModel):
    origin_ids: List[str]
    destination_ids: List[str]
    include_blocked: bool = False


@router.get("/path")
def get_path(
    origin: str = Query(..., description="Origin node ID"),
    destination: str = Query(..., description="Destination node ID"),
    include_blocked: bool = Query(False, description="Include blocked routes"),
):
    """Find shortest path between two nodes."""
    result = find_path(origin, destination, include_blocked)
    return result


@router.post("/check")
def check_route(
    origin: str = Query(..., description="Origin node ID"),
    destination: str = Query(..., description="Destination node ID"),
    include_blocked: bool = Query(False),
):
    """Check accessibility and cache result."""
    return check_accessibility(origin, destination, include_blocked)


@router.post("/batch")
def batch_check(data: BatchRequest):
    """Batch check accessibility for multiple pairs."""
    results = batch_accessibility(data.origin_ids, data.destination_ids, data.include_blocked)
    return {"count": len(results), "results": results}


@router.get("/blocked")
def blocked_routes():
    """Get all currently blocked or restricted routes."""
    routes = get_blocked_routes()
    return {"count": len(routes), "routes": routes}
