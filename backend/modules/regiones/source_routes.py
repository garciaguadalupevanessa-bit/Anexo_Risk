"""Region Sources API endpoint."""
from fastapi import APIRouter, HTTPException
from services.region_source_resolution import get_sources_for_region, get_source_health_for_region
from modules.regiones import models as region_models

router = APIRouter(prefix="/api/regions", tags=["region-sources"])


@router.get("/{region_id}/applicable-sources")
def get_applicable_sources(region_id: str):
    """Get all data sources applicable to a region with their configuration."""
    region = region_models.get_region(region_id)
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    return {
        "region_id": region_id,
        "region_name": region["name"],
        "sources": get_sources_for_region(region_id),
    }


@router.get("/{region_id}/source-health")
def get_source_health(region_id: str):
    """Get health status of all sources for a region."""
    region = region_models.get_region(region_id)
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    return {
        "region_id": region_id,
        "region_name": region["name"],
        "sources": get_source_health_for_region(region_id),
    }
