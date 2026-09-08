"""Dynamic Action Area service.

Computes affected zones around incidents based on hazard type,
intensity, and risk level. Uses H3 grid disk for spatial representation.
"""
from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from db.database import get_cursor
from geodata.services.h3_resolver import latlon_to_h3, get_h3_neighbors, H3_RESOLUTION

logger = logging.getLogger(__name__)

# Default buffer radii by hazard type (km)
HAZARD_RADIUS_KM = {
    "earthquake": 100.0,
    "fire": 25.0,
    "flood": 15.0,
    "cyclone": 200.0,
    "volcano": 50.0,
    "weather": 30.0,
    "alert": 10.0,
    "hotspot": 5.0,
    "risk": 10.0,
    "other": 10.0,
}

# Severity multiplier
SEVERITY_MULTIPLIER = {
    "verde": 0.5,
    "amarilla": 0.75,
    "naranja": 1.0,
    "roja": 1.5,
}


def compute_action_area(
    lat: float,
    lon: float,
    hazard_type: str = "other",
    severity: str | None = None,
    severity_float: float | None = None,
    custom_radius_km: float | None = None,
) -> dict[str, Any]:
    """Compute action area for a point based on hazard type and severity.

    Returns the center, radius, and H3 cells covering the action area.
    """
    base_radius = custom_radius_km or HAZARD_RADIUS_KM.get(hazard_type, 10.0)

    # Apply severity multiplier
    multiplier = 1.0
    if severity and severity in SEVERITY_MULTIPLIER:
        multiplier = SEVERITY_MULTIPLIER[severity]
    elif severity_float is not None:
        multiplier = 0.5 + severity_float  # 0.5 to 1.5

    radius_km = round(base_radius * multiplier, 2)

    # Get H3 cells covering the area
    center_h3 = latlon_to_h3(lat, lon, H3_RESOLUTION)
    if not center_h3:
        return {
            "center_lat": lat,
            "center_lon": lon,
            "hazard_type": hazard_type,
            "radius_km": radius_km,
            "h3_cells": [],
            "h3_center": None,
        }

    # Estimate k rings from radius
    km_per_ring = _approx_km_per_ring(H3_RESOLUTION)
    k = max(1, int(radius_km / km_per_ring))
    h3_cells = get_h3_neighbors(center_h3, k) or [center_h3]

    return {
        "center_lat": lat,
        "center_lon": lon,
        "hazard_type": hazard_type,
        "radius_km": radius_km,
        "h3_cells": h3_cells,
        "h3_center": center_h3,
        "severity": severity,
        "severity_float": severity_float,
    }


def store_action_area(
    incident_id: str | None = None,
    event_id: str | None = None,
    lat: float = 0.0,
    lon: float = 0.0,
    hazard_type: str = "other",
    severity: str | None = None,
    severity_float: float | None = None,
    custom_radius_km: float | None = None,
) -> dict[str, Any]:
    """Compute and store an action area."""
    area = compute_action_area(lat, lon, hazard_type, severity, severity_float, custom_radius_km)
    area_id = f"aa_{uuid.uuid4().hex[:12]}"

    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO action_areas
            (id, incident_id, event_id, area_type, hazard_type,
             radius_km, h3_cells_json, risk_level, severity_float, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                area_id,
                incident_id,
                event_id,
                f"buffer_{hazard_type}",
                hazard_type,
                area["radius_km"],
                json.dumps(area["h3_cells"]),
                severity,
                severity_float,
                json.dumps({"center_lat": lat, "center_lon": lon}),
            ),
        )

    area["id"] = area_id
    return area


def get_action_areas_for_incident(incident_id: str) -> list[dict[str, Any]]:
    """Get all action areas for an incident."""
    with get_cursor() as cur:
        rows = cur.execute(
            "SELECT * FROM action_areas WHERE incident_id = ? AND is_active = 1",
            (incident_id,),
        ).fetchall()
        return [_row_to_response(r) for r in rows]


def get_action_areas_in_h3(h3_index: str) -> list[dict[str, Any]]:
    """Get all action areas that cover a given H3 cell."""
    with get_cursor() as cur:
        rows = cur.execute(
            "SELECT * FROM action_areas WHERE is_active = 1"
        ).fetchall()
        results = []
        for row in rows:
            d = _row_to_response(row)
            cells = d.get("h3_cells", [])
            if h3_index in cells:
                results.append(d)
        return results


def deactivate_action_area(area_id: str):
    """Soft-deactivate an action area."""
    with get_cursor() as cur:
        cur.execute(
            "UPDATE action_areas SET is_active = 0 WHERE id = ?",
            (area_id,),
        )


def _row_to_response(row):
    """Convert sqlite3.Row to dict."""
    d = dict(row)
    for key in ("h3_cells_json", "metadata_json"):
        if key in d and d[key]:
            try:
                d[key] = json.loads(d[key])
            except (json.JSONDecodeError, TypeError):
                pass
    if "h3_cells_json" in d:
        d["h3_cells"] = d.pop("h3_cells_json")
    if "metadata_json" in d:
        d["metadata"] = d.pop("metadata_json")
    if "is_active" in d:
        d["is_active"] = bool(d["is_active"])
    return d


def _approx_km_per_ring(resolution: int) -> float:
    """Approximate km per H3 grid_disk ring."""
    approx_edge_km = {
        0: 1107.7, 1: 418.7, 2: 158.2, 3: 59.8, 4: 22.6,
        5: 8.5, 6: 3.2, 7: 1.2, 8: 0.46, 9: 0.17,
    }
    return approx_edge_km.get(resolution, 60.0)
