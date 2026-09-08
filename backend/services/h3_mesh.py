"""H3 Operational Mesh — spatial aggregation and cell-based queries.

Uses H3 as the common spatial index to aggregate events, incidents,
risk, exposure, needs, resources, and organizations per cell.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from db.database import get_cursor
from geodata.services.h3_resolver import (
    H3_RESOLUTION,
    h3_to_center,
    latlon_to_h3,
)

try:
    import h3
except ImportError:
    h3 = None

logger = logging.getLogger(__name__)

MAX_CELLS_RETURNED = 500


def index_event(event_id: str, lat: float, lon: float, resolution: int = H3_RESOLUTION) -> str | None:
    """Compute H3 index for an event and update the normalized_events table.

    Returns the H3 index or None if coordinates are invalid.
    """
    h3_idx = latlon_to_h3(lat, lon, resolution)
    if h3_idx is None:
        logger.warning("Cannot index event %s: invalid coordinates", event_id)
        return None
    with get_cursor() as cur:
        cur.execute(
            "UPDATE normalized_events SET h3_index = ? WHERE id = ?",
            (h3_idx, event_id),
        )
    return h3_idx


def region_to_h3_cells(
    bbox: dict | None = None,
    center_lat: float | None = None,
    center_lon: float | None = None,
    radius_km: float | None = None,
    resolution: int = H3_RESOLUTION,
) -> list[str]:
    """Convert a region (bbox or center+radius) to a set of H3 cell indices.

    Uses h3.grid_disk for center+radius or polygonfill for bbox.
    Returns a deduplicated list of H3 indices.
    """
    cells = set()

    if center_lat is not None and center_lon is not None:
        center_h3 = latlon_to_h3(center_lat, center_lon, resolution)
        if center_h3 is None:
            return []
        # Approximate radius in grid_disk k rings: res 3 ≈ 110km/edge
        km_per_ring = _approx_km_per_ring(resolution)
        k = max(1, int(radius_km / km_per_ring)) if radius_km else 1
        try:
            cells.update(h3.grid_disk(center_h3, k))
        except Exception as exc:
            logger.warning("grid_disk failed: %s", exc)
            cells.add(center_h3)
    elif bbox:
        min_lat = bbox.get("min_lat", bbox.get("south"))
        min_lon = bbox.get("min_lon", bbox.get("west"))
        max_lat = bbox.get("max_lat", bbox.get("north"))
        max_lon = bbox.get("max_lon", bbox.get("east"))
        if None in (min_lat, min_lon, max_lat, max_lon):
            return []
        try:
            boundary = [
                (min_lat, min_lon),
                (min_lat, max_lon),
                (max_lat, max_lon),
                (max_lat, min_lon),
                (min_lat, min_lon),
            ]
            poly = h3.LatLngPoly(boundary)
            cells.update(h3.polygon_to_cells(poly, resolution))
        except Exception as exc:
            logger.warning("polygon_to_cells failed: %s", exc)
        # Always sample to ensure coverage at coarser resolutions
        if not cells:
            step = _bbox_sample_step(resolution)
            for lat in _frange(min_lat, max_lat, step):
                for lon in _frange(min_lon, max_lon, step):
                    h3_idx = latlon_to_h3(lat, lon, resolution)
                    if h3_idx:
                        cells.add(h3_idx)

    return sorted(cells)[:MAX_CELLS_RETURNED]


def aggregate_cell(h3_index: str, resolution: int = H3_RESOLUTION) -> dict[str, Any]:
    """Compute aggregation metrics for a single H3 cell from normalized_events."""
    with get_cursor() as cur:
        row = cur.execute(
            """SELECT
                COUNT(*) as event_count,
                AVG(severity_float) as avg_severity,
                MAX(severity_float) as max_severity,
                MAX(timestamp) as last_event_at,
                GROUP_CONCAT(DISTINCT entity_type) as entity_types,
                GROUP_CONCAT(DISTINCT source) as sources
            FROM normalized_events
            WHERE h3_index = ? AND is_active = 1""",
            (h3_index,),
        ).fetchone()

    event_count = row["event_count"] if row else 0
    center = h3_to_center(h3_index)
    return {
        "h3_index": h3_index,
        "resolution": resolution,
        "center_lat": center[0] if center else None,
        "center_lon": center[1] if center else None,
        "event_count": event_count,
        "incident_count": 0,
        "avg_severity": round(row["avg_severity"], 3) if row and row["avg_severity"] is not None else 0.0,
        "max_severity": round(row["max_severity"], 3) if row and row["max_severity"] is not None else 0.0,
        "avg_risk_score": 0.0,
        "entity_types": row["entity_types"].split(",") if row and row["entity_types"] else [],
        "sources": row["sources"].split(",") if row and row["sources"] else [],
        "last_event_at": row["last_event_at"] if row else None,
    }


def aggregate_cells(
    h3_indices: list[str],
    resolution: int = H3_RESOLUTION,
) -> list[dict[str, Any]]:
    """Aggregate metrics for a list of H3 cells."""
    results = []
    for h3_idx in h3_indices[:MAX_CELLS_RETURNED]:
        cell = aggregate_cell(h3_idx, resolution)
        if cell["event_count"] > 0:
            results.append(cell)
    results.sort(key=lambda c: c["event_count"], reverse=True)
    return results


def cells_in_bbox(
    min_lat: float,
    min_lon: float,
    max_lat: float,
    max_lon: float,
    resolution: int = H3_RESOLUTION,
) -> list[dict[str, Any]]:
    """Return aggregated cells within a bounding box, filtered to cells with data."""
    cells = region_to_h3_cells(
        bbox={"min_lat": min_lat, "min_lon": min_lon, "max_lat": max_lat, "max_lon": max_lon},
        resolution=resolution,
    )
    return aggregate_cells(cells, resolution)


def cells_in_radius(
    center_lat: float,
    center_lon: float,
    radius_km: float,
    resolution: int = H3_RESOLUTION,
) -> list[dict[str, Any]]:
    """Return aggregated cells within a radius from center, filtered to cells with data."""
    cells = region_to_h3_cells(
        center_lat=center_lat,
        center_lon=center_lon,
        radius_km=radius_km,
        resolution=resolution,
    )
    return aggregate_cells(cells, resolution)


def operational_coverage(
    region_bbox: dict | None = None,
    center_lat: float | None = None,
    center_lon: float | None = None,
    radius_km: float | None = None,
    resolution: int = H3_RESOLUTION,
) -> dict[str, Any]:
    """Calculate operational coverage: ratio of cells with data to total cells in region."""
    all_cells = region_to_h3_cells(
        bbox=region_bbox,
        center_lat=center_lat,
        center_lon=center_lon,
        radius_km=radius_km,
        resolution=resolution,
    )
    total = len(all_cells)
    if total == 0:
        return {"total_cells": 0, "covered_cells": 0, "coverage_ratio": 0.0}

    with get_cursor() as cur:
        placeholders = ",".join("?" for _ in all_cells)
        row = cur.execute(
            f"""SELECT COUNT(DISTINCT h3_index) as covered
                FROM normalized_events
                WHERE h3_index IN ({placeholders}) AND is_active = 1""",
            all_cells,
        ).fetchone()
        covered = row["covered"] if row else 0

    return {
        "total_cells": total,
        "covered_cells": covered,
        "coverage_ratio": round(covered / total, 4) if total > 0 else 0.0,
        "resolution": resolution,
    }


def _approx_km_per_ring(resolution: int) -> float:
    """Approximate km per H3 grid_disk ring for a given resolution."""
    # Approximate edge length in km for H3 resolutions
    approx_edge_km = {
        0: 1107.7, 1: 418.7, 2: 158.2, 3: 59.8, 4: 22.6,
        5: 8.5, 6: 3.2, 7: 1.2, 8: 0.46, 9: 0.17,
    }
    return approx_edge_km.get(resolution, 60.0)


def _bbox_sample_step(resolution: int) -> float:
    """Approximate degree step for bbox sampling at a given H3 resolution."""
    # Finer resolution needs denser sampling
    steps = {0: 10.0, 1: 5.0, 2: 2.0, 3: 1.0, 4: 0.5, 5: 0.25, 6: 0.1, 7: 0.05}
    return steps.get(resolution, 0.5)


def _frange(start: float, stop: float, step: float) -> list[float]:
    """Generate a range of floats."""
    result = []
    val = start
    while val <= stop:
        result.append(round(val, 6))
        val += step
    return result
