"""H3 Operational Mesh API endpoints."""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from services.h3_mesh import (
    operational_coverage,
    cells_in_bbox,
    cells_in_radius,
    aggregate_cell,
    region_to_h3_cells,
)
from modules.regiones import models as region_models

router = APIRouter(prefix="/api/h3", tags=["h3-mesh"])


@router.get("/cells")
def get_cells_in_bbox(
    min_lat: float = Query(..., description="South boundary"),
    min_lon: float = Query(..., description="West boundary"),
    max_lat: float = Query(..., description="North boundary"),
    max_lon: float = Query(..., description="East boundary"),
    resolution: int = Query(3, ge=0, le=15),
):
    """Get aggregated H3 cells within a bounding box."""
    cells = cells_in_bbox(min_lat, min_lon, max_lat, max_lon, resolution)
    return {
        "bbox": {"min_lat": min_lat, "min_lon": min_lon, "max_lat": max_lat, "max_lon": max_lon},
        "resolution": resolution,
        "cells_with_data": len(cells),
        "cells": cells,
    }


@router.get("/cells/radius")
def get_cells_in_radius(
    center_lat: float = Query(..., description="Center latitude"),
    center_lon: float = Query(..., description="Center longitude"),
    radius_km: float = Query(..., ge=0.1, le=500, description="Radius in km"),
    resolution: int = Query(3, ge=0, le=15),
):
    """Get aggregated H3 cells within a radius from center."""
    cells = cells_in_radius(center_lat, center_lon, radius_km, resolution)
    return {
        "center": {"lat": center_lat, "lon": center_lon},
        "radius_km": radius_km,
        "resolution": resolution,
        "cells_with_data": len(cells),
        "cells": cells,
    }


@router.get("/cells/{h3_index}")
def get_cell_detail(h3_index: str):
    """Get detail for a single H3 cell."""
    cell = aggregate_cell(h3_index)
    if cell["event_count"] == 0:
        raise HTTPException(status_code=404, detail=f"No data for cell {h3_index}")
    return cell


@router.get("/region/{region_id}")
def get_region_cells(region_id: str):
    """Get all H3 cells covering a region."""
    region = region_models.get_region(region_id)
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    bbox = None
    if region.get("bbox_min_lat") is not None:
        bbox = {
            "min_lat": region["bbox_min_lat"],
            "min_lon": region["bbox_min_lon"],
            "max_lat": region["bbox_max_lat"],
            "max_lon": region["bbox_max_lon"],
        }
    cells = region_to_h3_cells(
        bbox=bbox,
        center_lat=region.get("center_lat"),
        center_lon=region.get("center_lon"),
        radius_km=region.get("radius_km"),
        resolution=region.get("h3_resolution", 3),
    )
    return {
        "region_id": region_id,
        "region_name": region.get("name"),
        "resolution": region.get("h3_resolution", 3),
        "total_cells": len(cells),
        "cells": cells,
    }


@router.get("/coverage")
def get_coverage(
    min_lat: Optional[float] = Query(None),
    min_lon: Optional[float] = Query(None),
    max_lat: Optional[float] = Query(None),
    max_lon: Optional[float] = Query(None),
    center_lat: Optional[float] = Query(None),
    center_lon: Optional[float] = Query(None),
    radius_km: Optional[float] = Query(None, ge=0.1, le=500),
    resolution: int = Query(3, ge=0, le=15),
):
    """Calculate operational coverage for a bbox or center+radius region."""
    bbox = None
    if None not in (min_lat, min_lon, max_lat, max_lon):
        bbox = {"min_lat": min_lat, "min_lon": min_lon, "max_lat": max_lat, "max_lon": max_lon}
    elif center_lat is None or center_lon is None:
        raise HTTPException(
            status_code=400,
            detail="Provide either bbox (min_lat,min_lon,max_lat,max_lon) or center+radius",
        )
    return operational_coverage(
        region_bbox=bbox,
        center_lat=center_lat,
        center_lon=center_lon,
        radius_km=radius_km,
        resolution=resolution,
    )
