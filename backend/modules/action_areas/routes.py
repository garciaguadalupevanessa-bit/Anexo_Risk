"""Action Area API endpoints."""
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import Optional
from services.action_area import (
    compute_action_area, store_action_area,
    get_action_areas_for_incident, get_action_areas_in_h3,
)

router = APIRouter(prefix="/api/action-areas", tags=["action-areas"])


class ActionAreaCreate(BaseModel):
    incident_id: Optional[str] = None
    event_id: Optional[str] = None
    lat: float
    lon: float
    hazard_type: str = "other"
    severity: Optional[str] = None
    severity_float: Optional[float] = None
    custom_radius_km: Optional[float] = None


@router.post("", status_code=201)
def create_action_area(data: ActionAreaCreate):
    """Compute and store an action area."""
    return store_action_area(
        incident_id=data.incident_id,
        event_id=data.event_id,
        lat=data.lat,
        lon=data.lon,
        hazard_type=data.hazard_type,
        severity=data.severity,
        severity_float=data.severity_float,
        custom_radius_km=data.custom_radius_km,
    )


@router.post("/compute")
def compute_area(data: ActionAreaCreate):
    """Compute action area without storing."""
    return compute_action_area(
        lat=data.lat,
        lon=data.lon,
        hazard_type=data.hazard_type,
        severity=data.severity,
        severity_float=data.severity_float,
        custom_radius_km=data.custom_radius_km,
    )


@router.get("/incident/{incident_id}")
def for_incident(incident_id: str):
    """Get action areas for an incident."""
    areas = get_action_areas_for_incident(incident_id)
    return {"incident_id": incident_id, "count": len(areas), "areas": areas}


@router.get("/h3/{h3_index}")
def for_h3_cell(h3_index: str):
    """Get action areas covering an H3 cell."""
    areas = get_action_areas_in_h3(h3_index)
    return {"h3_index": h3_index, "count": len(areas), "areas": areas}
