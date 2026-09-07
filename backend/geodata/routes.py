"""Routes para GeoData Engine — endpoints de datos geofísicos."""
from __future__ import annotations

from fastapi import APIRouter, Query

from geodata.adapters.effis_adapter import get_fire_danger, get_fire_danger_for_point
from geodata.adapters.ibtracs_adapter import fetch_cyclones
from geodata.adapters.smithsonian_adapter import fetch_volcanoes
from geodata.adapters.usgs_adapter import fetch_earthquakes
from geodata.services.exposure import calculate_exposure, calculate_impact
from geodata.services.risk_engine import calculate_risk_score
from geodata.services.spatial import compute_h3_aggregation, latlon_to_h3

router = APIRouter(prefix="/api/geodata", tags=["geodata"])


@router.get("/earthquakes")
def get_earthquakes(
    feed: str = Query("week", pattern=r"^(hour|day|week|month)$"),
    max_events: int | None = Query(None, ge=1, le=10000),
):
    events = fetch_earthquakes(feed=feed, max_events=max_events)
    return {"source": "usgs", "count": len(events), "events": events}


@router.get("/cyclones")
def get_cyclones(
    max_events: int | None = Query(None, ge=1, le=5000),
    max_rows: int = Query(5000, ge=100, le=20000),
):
    events = fetch_cyclones(max_events=max_events, max_rows=max_rows)
    return {"source": "ibtracs", "count": len(events), "events": events}


@router.get("/volcanoes")
def get_volcanoes(max_events: int | None = Query(None, ge=1, le=2000)):
    events = fetch_volcanoes(max_events=max_events)
    return {"source": "smithsonian", "count": len(events), "events": events}


@router.get("/h3/aggregate")
def aggregate_h3(
    feed: str = Query("week", pattern=r"^(hour|day|week|month)$"),
    resolution: int = Query(7, ge=0, le=15),
):
    events_usgs = fetch_earthquakes(feed=feed, max_events=5000)
    events_volc = fetch_volcanoes(max_events=500)
    all_events = events_usgs + events_volc

    cells = compute_h3_aggregation(all_events, resolution=resolution)

    result = []
    for h3_idx, cell in cells.items():
        centroid = None
        try:
            from geodata.services.spatial import h3_to_latlon
            centroid = h3_to_latlon(h3_idx)
        except Exception:
            pass
        result.append({
            "h3_index": h3_idx,
            "resolution": cell["resolution"],
            "event_count": cell["event_count"],
            "avg_severity": round(cell["avg_severity"], 3),
            "centroid_lat": centroid[0] if centroid else None,
            "centroid_lon": centroid[1] if centroid else None,
        })

    result.sort(key=lambda x: x["avg_severity"], reverse=True)
    return {"resolution": resolution, "cell_count": len(result), "cells": result}


@router.get("/exposure")
def get_exposure(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    severity: float = Query(0.5, ge=0, le=1),
    radius_km: float = Query(50.0, gt=0, le=200),
):
    event = {"latitud": lat, "longitud": lon, "severity": severity, "magnitude": 0}
    exposure = calculate_exposure(event, needs=[], resources=[], radius_km=radius_km)
    impact = calculate_impact(event, exposure)
    return {
        "event": {"lat": lat, "lon": lon, "severity": severity},
        "exposure": exposure,
        "impact": impact,
    }


@router.get("/risk")
def get_risk(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    severity: float = Query(0.5, ge=0, le=1),
    weather: float = Query(0.0, ge=0, le=1),
    event_density: float = Query(0.0, ge=0, le=1),
    needs_open: int = Query(0, ge=0),
):
    event = {"latitud": lat, "longitud": lon, "severity": severity, "magnitude": 0}
    exposure = calculate_exposure(event, needs=[], resources=[])
    risk = calculate_risk_score(
        severity=severity,
        exposure=exposure.get("exposure_score", 0),
        weather=weather,
        event_density=event_density,
        needs_open=needs_open,
    )
    return risk


@router.get("/h3/{h3_index}")
def get_h3_cell(h3_index: str):
    import re
    from fastapi import HTTPException
    from geodata.services.spatial import h3_to_latlon, get_h3_neighbors

    if not re.match(r"^[0-9a-f]{15,16}$", h3_index):
        raise HTTPException(status_code=400, detail="Formato de índice H3 no válido")
    try:
        latlon = h3_to_latlon(h3_index)
        if latlon is None:
            raise HTTPException(status_code=404, detail="Celda H3 no encontrada")
        neighbors = get_h3_neighbors(h3_index, k=1)
        return {
            "h3_index": h3_index,
            "centroid": {"lat": latlon[0], "lon": latlon[1]},
            "neighbor_count": len(neighbors),
            "neighbors": neighbors[:10],
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Error al procesar índice H3")


@router.get("/effis")
def get_effis_layers(date: str | None = Query(None, description="Fecha YYYY-MM-DD")):
    """Retorna URLs de capas EFFIS (fire danger, hotspots, burnt areas)."""
    return get_fire_danger(date=date)


@router.get("/effis/point")
def get_effis_for_point(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    date: str | None = Query(None),
):
    """Retorna URLs de capas EFFIS para un punto específico."""
    return get_fire_danger_for_point(lat, lon, date=date)
