"""Region/AOI API endpoints."""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from modules.regiones.schemas import (
    RegionCreate, RegionUpdate, RegionResponse,
    RegionSourceCreate, RegionSourceResponse,
)
from modules.regiones import models

router = APIRouter(prefix="/api/regions", tags=["regions"])


@router.get("", response_model=list[RegionResponse])
def list_regions(
    level: Optional[str] = Query(None),
    country_code: Optional[str] = Query(None),
    parent_id: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
):
    """List all regions with optional filters."""
    return models.list_regions(
        level=level, country_code=country_code,
        parent_id=parent_id, is_active=is_active,
    )


@router.get("/active", response_model=Optional[RegionResponse])
def get_active_region():
    """Get the currently active region."""
    region = models.get_active_region()
    if not region:
        raise HTTPException(status_code=404, detail="No active region configured")
    return region


@router.get("/{region_id}", response_model=RegionResponse)
def get_region(region_id: str):
    """Get a single region by ID."""
    region = models.get_region(region_id)
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    return region


@router.post("", response_model=RegionResponse, status_code=201)
def create_region(data: RegionCreate):
    """Create a new region/AOI."""
    existing = models.get_region(data.id)
    if existing:
        raise HTTPException(status_code=409, detail="Region ID already exists")
    return models.create_region(data.model_dump())


@router.patch("/{region_id}", response_model=RegionResponse)
def update_region(region_id: str, data: RegionUpdate):
    """Update a region."""
    existing = models.get_region(region_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Region not found")
    updates = data.model_dump(exclude_unset=True)
    if "geometry" in updates:
        updates["geometry_json"] = updates.pop("geometry")
    if "metadata" in updates:
        updates["metadata_json"] = updates.pop("metadata")
    return models.update_region(region_id, updates)


@router.delete("/{region_id}", response_model=RegionResponse)
def delete_region(region_id: str):
    """Soft-delete a region (set is_active=0)."""
    existing = models.get_region(region_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Region not found")
    return models.delete_region(region_id)


@router.get("/{region_id}/children", response_model=list[RegionResponse])
def get_region_children(region_id: str):
    """Get all child regions."""
    existing = models.get_region(region_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Region not found")
    return models.get_region_children(region_id)


@router.get("/{region_id}/sources", response_model=list[RegionSourceResponse])
def get_region_sources(region_id: str):
    """Get all sources linked to a region."""
    existing = models.get_region(region_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Region not found")
    return models.get_region_sources(region_id)


@router.post("/{region_id}/sources", response_model=list[RegionSourceResponse], status_code=201)
def add_region_source(region_id: str, data: RegionSourceCreate):
    """Link a source to a region."""
    existing = models.get_region(region_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Region not found")
    return models.add_region_source(
        region_id, data.source_id, data.is_enabled, data.priority, data.config,
    )


@router.delete("/{region_id}/sources/{source_id}")
def remove_region_source(region_id: str, source_id: str):
    """Remove a source from a region."""
    existing = models.get_region(region_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Region not found")
    models.remove_region_source(region_id, source_id)
    return {"detail": "Source removed"}
