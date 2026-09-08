"""Live Dashboard API endpoints."""
from fastapi import APIRouter, Query
from typing import Optional
from services.live_dashboard import get_live_dashboard

router = APIRouter(prefix="/api/live-dashboard", tags=["live-dashboard"])


@router.get("")
def dashboard(region_id: Optional[str] = Query(None)):
    """Get aggregated live dashboard data."""
    return get_live_dashboard(region_id=region_id)
