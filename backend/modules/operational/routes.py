"""Operational Data API — exposes Anexo_Risk operational data for GeoRisk Finder.

Provides read-only endpoints that GeoRisk can consume:
- GET /api/operational/events — active incidents/alerts
- GET /api/operational/needs — open needs
- GET /api/operational/resources — available resources
- GET /api/operational/summary — aggregated operational metrics
- GET /api/operational/h3/{h3_index} — per-cell operational metrics

All endpoints support spatial filters: h3_index, bbox, radius, time period.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Query

from db.database import get_cursor
from geodata.services.h3_resolver import latlon_to_h3

router = APIRouter(prefix="/api/operational", tags=["operational-data"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_bbox(bbox: str | None) -> tuple[float, float, float, float] | None:
    """Parse 'lat_min,lon_min,lat_max,lon_max' into tuple."""
    if not bbox:
        return None
    try:
        parts = [float(x.strip()) for x in bbox.split(",")]
        if len(parts) != 4:
            return None
        lat_min, lon_min, lat_max, lon_max = parts
        if not (-90 <= lat_min <= 90 and -90 <= lat_max <= 90):
            return None
        if not (-180 <= lon_min <= 180 and -180 <= lon_max <= 180):
            return None
        return (lat_min, lon_min, lat_max, lon_max)
    except (ValueError, AttributeError):
        return None


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine distance in km."""
    import math
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _row_to_dict(row) -> dict:
    """Convert sqlite3 Row to dict."""
    if row is None:
        return {}
    return {key: row[key] for key in row.keys()}


def _rows_to_list(rows) -> list[dict]:
    return [_row_to_dict(r) for r in rows]


# ---------------------------------------------------------------------------
# GET /api/operational/events
# ---------------------------------------------------------------------------
@router.get("/events")
def get_operational_events(
    h3_index: Optional[str] = Query(None, description="Filter by H3 cell"),
    bbox: Optional[str] = Query(None, description="Bounding box: lat_min,lon_min,lat_max,lon_max"),
    radius_km: Optional[float] = Query(None, ge=0.1, le=500, description="Radius in km from center"),
    center_lat: Optional[float] = Query(None, ge=-90, le=90),
    center_lon: Optional[float] = Query(None, ge=-180, le=180),
    since: Optional[str] = Query(None, description="ISO 8601 timestamp — only events after this time"),
    limit: int = Query(100, ge=1, le=1000),
):
    """Return operational events (alerts with coordinates).

    Spatial filters (applied in order):
    1. h3_index — exact H3 cell match
    2. bbox — bounding box
    3. radius_km + center_lat/lon — radius search
    """
    with get_cursor() as cur:
        conditions = ["is_active = 1"]
        params: list = []

        if since:
            conditions.append("created_at >= ?")
            params.append(since)

        if h3_index:
            # Filter by H3 cell: compute lat/lon bounds for the cell
            try:
                from geodata.services.h3_resolver import h3_to_center
                center = h3_to_center(h3_index)
                if center:
                    # Approximate H3 res-3 cell bounds (~1.2° radius)
                    clat, clon = center
                    conditions.append("lat BETWEEN ? AND ?")
                    conditions.append("lon BETWEEN ? AND ?")
                    params.extend([clat - 1.5, clat + 1.5, clon - 1.5, clon + 1.5])
                else:
                    return {"events": [], "total": 0, "source": "anexo_risk"}
            except Exception:
                return {"events": [], "total": 0, "source": "anexo_risk"}

        elif bbox:
            bb = _parse_bbox(bbox)
            if bb:
                lat_min, lon_min, lat_max, lon_max = bb
                conditions.append("lat BETWEEN ? AND ?")
                conditions.append("lon BETWEEN ? AND ?")
                params.extend([lat_min, lat_max, lon_min, lon_max])

        elif radius_km and center_lat is not None and center_lon is not None:
            # Approximate bounding box for radius, then refine with haversine
            import math
            dlat = radius_km / 111.0
            dlon = radius_km / (111.0 * math.cos(math.radians(center_lat)))
            conditions.append("lat BETWEEN ? AND ?")
            conditions.append("lon BETWEEN ? AND ?")
            params.extend([center_lat - dlat, center_lat + dlat, center_lon - dlon, center_lon + dlon])

        where = " AND ".join(conditions)
        sql = f"SELECT * FROM alertas WHERE {where} ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cur.execute(sql, params)
        rows = _rows_to_list(cur.fetchall())

    # Post-filter for radius (haversine)
    if radius_km and center_lat is not None and center_lon is not None and not h3_index and not bbox:
        rows = [r for r in rows if r.get("lat") and r.get("lon")
                and _haversine_km(center_lat, center_lon, r["lat"], r["lon"]) <= radius_km]

    # Enrich with h3_index
    for r in rows:
        if r.get("lat") and r.get("lon"):
            r["h3_index"] = latlon_to_h3(r["lat"], r["lon"])

    return {
        "events": rows,
        "total": len(rows),
        "source": "anexo_risk",
        "generated_at": _now_iso(),
    }


# ---------------------------------------------------------------------------
# GET /api/operational/needs
# ---------------------------------------------------------------------------
@router.get("/needs")
def get_operational_needs(
    h3_index: Optional[str] = Query(None),
    bbox: Optional[str] = Query(None),
    radius_km: Optional[float] = Query(None, ge=0.1, le=500),
    center_lat: Optional[float] = Query(None, ge=-90, le=90),
    center_lon: Optional[float] = Query(None, ge=-180, le=180),
    status: Optional[str] = Query(None, description="abierta | cubierta"),
    priority: Optional[str] = Query(None, description="baja | media | alta | critica"),
    since: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
):
    """Return operational needs with spatial filters."""
    with get_cursor() as cur:
        conditions = []
        params: list = []

        if status:
            conditions.append("estado = ?")
            params.append(status)
        else:
            conditions.append("estado = 'abierta'")

        if priority:
            conditions.append("prioridad = ?")
            params.append(priority)

        if since:
            conditions.append("creado_en >= ?")
            params.append(since)

        if h3_index:
            try:
                from geodata.services.h3_resolver import h3_to_center
                center = h3_to_center(h3_index)
                if center:
                    clat, clon = center
                    conditions.append("latitud BETWEEN ? AND ?")
                    conditions.append("longitud BETWEEN ? AND ?")
                    params.extend([clat - 1.5, clat + 1.5, clon - 1.5, clon + 1.5])
                else:
                    return {"needs": [], "total": 0, "source": "anexo_risk"}
            except Exception:
                return {"needs": [], "total": 0, "source": "anexo_risk"}
        elif bbox:
            bb = _parse_bbox(bbox)
            if bb:
                lat_min, lon_min, lat_max, lon_max = bb
                conditions.append("latitud BETWEEN ? AND ?")
                conditions.append("longitud BETWEEN ? AND ?")
                params.extend([lat_min, lat_max, lon_min, lon_max])
        elif radius_km and center_lat is not None and center_lon is not None:
            import math
            dlat = radius_km / 111.0
            dlon = radius_km / (111.0 * math.cos(math.radians(center_lat)))
            conditions.append("latitud BETWEEN ? AND ?")
            conditions.append("longitud BETWEEN ? AND ?")
            params.extend([center_lat - dlat, center_lat + dlat, center_lon - dlon, center_lon + dlon])

        where = " AND ".join(conditions) if conditions else "1=1"
        sql = f"SELECT * FROM necesidades WHERE {where} ORDER BY creado_en DESC LIMIT ?"
        params.append(limit)

        cur.execute(sql, params)
        rows = _rows_to_list(cur.fetchall())

    # Post-filter for radius
    if radius_km and center_lat is not None and center_lon is not None and not h3_index and not bbox:
        rows = [r for r in rows if r.get("latitud") and r.get("longitud")
                and _haversine_km(center_lat, center_lon, r["latitud"], r["longitud"]) <= radius_km]

    for r in rows:
        if r.get("latitud") and r.get("longitud"):
            r["h3_index"] = latlon_to_h3(r["latitud"], r["longitud"])

    return {
        "needs": rows,
        "total": len(rows),
        "source": "anexo_risk",
        "generated_at": _now_iso(),
    }


# ---------------------------------------------------------------------------
# GET /api/operational/resources
# ---------------------------------------------------------------------------
@router.get("/resources")
def get_operational_resources(
    h3_index: Optional[str] = Query(None),
    bbox: Optional[str] = Query(None),
    radius_km: Optional[float] = Query(None, ge=0.1, le=500),
    center_lat: Optional[float] = Query(None, ge=-90, le=90),
    center_lon: Optional[float] = Query(None, ge=-180, le=180),
    resource_status: Optional[str] = Query(None, alias="status", description="disponible | asignado | en_mantenimiento | retirado"),
    since: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
):
    """Return operational resources with spatial filters."""
    with get_cursor() as cur:
        conditions = []
        params: list = []

        if resource_status:
            conditions.append("status = ?")
            params.append(resource_status)

        if since:
            conditions.append("created_at >= ?")
            params.append(since)

        if h3_index:
            try:
                from geodata.services.h3_resolver import h3_to_center
                center = h3_to_center(h3_index)
                if center:
                    clat, clon = center
                    conditions.append("latitud BETWEEN ? AND ?")
                    conditions.append("longitud BETWEEN ? AND ?")
                    params.extend([clat - 1.5, clat + 1.5, clon - 1.5, clon + 1.5])
                else:
                    return {"resources": [], "total": 0, "source": "anexo_risk"}
            except Exception:
                return {"resources": [], "total": 0, "source": "anexo_risk"}
        elif bbox:
            bb = _parse_bbox(bbox)
            if bb:
                lat_min, lon_min, lat_max, lon_max = bb
                conditions.append("latitud BETWEEN ? AND ?")
                conditions.append("longitud BETWEEN ? AND ?")
                params.extend([lat_min, lat_max, lon_min, lon_max])
        elif radius_km and center_lat is not None and center_lon is not None:
            import math
            dlat = radius_km / 111.0
            dlon = radius_km / (111.0 * math.cos(math.radians(center_lat)))
            conditions.append("latitud BETWEEN ? AND ?")
            conditions.append("longitud BETWEEN ? AND ?")
            params.extend([center_lat - dlat, center_lat + dlat, center_lon - dlon, center_lon + dlon])

        where = " AND ".join(conditions) if conditions else "1=1"
        sql = f"SELECT * FROM resources WHERE {where} ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cur.execute(sql, params)
        rows = _rows_to_list(cur.fetchall())

    if radius_km and center_lat is not None and center_lon is not None and not h3_index and not bbox:
        rows = [r for r in rows if r.get("latitud") and r.get("longitud")
                and _haversine_km(center_lat, center_lon, r["latitud"], r["longitud"]) <= radius_km]

    for r in rows:
        if r.get("latitud") and r.get("longitud"):
            r["h3_index"] = latlon_to_h3(r["latitud"], r["longitud"])

    return {
        "resources": rows,
        "total": len(rows),
        "source": "anexo_risk",
        "generated_at": _now_iso(),
    }


# ---------------------------------------------------------------------------
# GET /api/operational/summary
# ---------------------------------------------------------------------------
@router.get("/summary")
def get_operational_summary(
    h3_index: Optional[str] = Query(None),
    bbox: Optional[str] = Query(None),
    radius_km: Optional[float] = Query(None, ge=0.1, le=500),
    center_lat: Optional[float] = Query(None, ge=-90, le=90),
    center_lon: Optional[float] = Query(None, ge=-180, le=180),
):
    """Return aggregated operational summary.

    Provides counts and metrics that GeoRisk can use for feature engineering.
    """
    with get_cursor() as cur:
        # Build spatial condition for needs
        need_conditions = []
        need_params: list = []
        alert_conditions = ["is_active = 1"]
        alert_params: list = []
        res_conditions = []
        res_params: list = []

        if h3_index:
            try:
                from geodata.services.h3_resolver import h3_to_center
                center = h3_to_center(h3_index)
                if center:
                    clat, clon = center
                    spatial = [("latitud BETWEEN ? AND ?", "longitud BETWEEN ? AND ?"),
                               (clat - 1.5, clat + 1.5, clon - 1.5, clon + 1.5)]
                    for cond, val in [("latitud BETWEEN ? AND ?", [clat - 1.5, clat + 1.5]),
                                      ("longitud BETWEEN ? AND ?", [clon - 1.5, clon + 1.5])]:
                        need_conditions.append(cond)
                        need_params.extend(val)
                        res_conditions.append(cond)
                        res_params.extend(val)
                    alert_conditions.append("lat BETWEEN ? AND ?")
                    alert_conditions.append("lon BETWEEN ? AND ?")
                    alert_params.extend([clat - 1.5, clat + 1.5, clon - 1.5, clon + 1.5])
            except Exception:
                pass
        elif bbox:
            bb = _parse_bbox(bbox)
            if bb:
                lat_min, lon_min, lat_max, lon_max = bb
                for cond, vals in [
                    ("latitud BETWEEN ? AND ?", [lat_min, lat_max]),
                    ("longitud BETWEEN ? AND ?", [lon_min, lon_max]),
                ]:
                    need_conditions.append(cond)
                    need_params.extend(vals)
                    res_conditions.append(cond)
                    res_params.extend(vals)
                alert_conditions.append("lat BETWEEN ? AND ?")
                alert_conditions.append("lon BETWEEN ? AND ?")
                alert_params.extend([lat_min, lat_max, lon_min, lon_max])

        nc = " AND ".join(need_conditions) if need_conditions else "1=1"
        ac = " AND ".join(alert_conditions) if alert_conditions else "1=1"
        rc = " AND ".join(res_conditions) if res_conditions else "1=1"

        # Needs metrics
        cur.execute(f"SELECT COUNT(*) as total, "
                    f"SUM(CASE WHEN estado='abierta' THEN 1 ELSE 0 END) as open_count, "
                    f"SUM(CASE WHEN estado='cubierta' THEN 1 ELSE 0 END) as covered_count, "
                    f"SUM(CASE WHEN prioridad='critica' AND estado='abierta' THEN 1 ELSE 0 END) as critical_open, "
                    f"SUM(CASE WHEN prioridad='alta' AND estado='abierta' THEN 1 ELSE 0 END) as high_open, "
                    f"COALESCE(SUM(quantity), 0) as total_quantity, "
                    f"COALESCE(SUM(covered_quantity), 0) as total_covered "
                    f"FROM necesidades WHERE {nc}", need_params)
        need_stats = _row_to_dict(cur.fetchone())

        # Alert metrics
        cur.execute(f"SELECT COUNT(*) as total_active, "
                    f"SUM(CASE WHEN severidad IN ('RED') THEN 1 ELSE 0 END) as critical_alerts, "
                    f"SUM(CASE WHEN severidad IN ('ORANGE') THEN 1 ELSE 0 END) as high_alerts "
                    f"FROM alertas WHERE {ac}", alert_params)
        alert_stats = _row_to_dict(cur.fetchone())

        # Resource metrics
        cur.execute(f"SELECT COUNT(*) as total, "
                    f"SUM(CASE WHEN status='disponible' THEN 1 ELSE 0 END) as available, "
                    f"SUM(CASE WHEN status='asignado' THEN 1 ELSE 0 END) as assigned, "
                    f"COALESCE(SUM(quantity), 0) as total_quantity, "
                    f"COALESCE(SUM(available_quantity), 0) as total_available_qty "
                    f"FROM resources WHERE {rc}", res_params)
        res_stats = _row_to_dict(cur.fetchone())

        # Assignment metrics
        cur.execute("SELECT COUNT(*) as total, "
                    "SUM(CASE WHEN status='asignado' THEN 1 ELSE 0 END) as active, "
                    "SUM(CASE WHEN status='en_curso' THEN 1 ELSE 0 END) as in_progress "
                    "FROM need_assignments")
        assign_stats = _row_to_dict(cur.fetchone())

        # Incident metrics
        inc_conditions = ["is_active = 1"]
        inc_params: list = []
        if h3_index:
            try:
                from geodata.services.h3_resolver import h3_to_center
                center = h3_to_center(h3_index)
                if center:
                    clat, clon = center
                    inc_conditions.append("lat BETWEEN ? AND ?")
                    inc_conditions.append("lon BETWEEN ? AND ?")
                    inc_params.extend([clat - 1.5, clat + 1.5, clon - 1.5, clon + 1.5])
            except Exception:
                pass
        elif bbox:
            bb = _parse_bbox(bbox)
            if bb:
                lat_min, lon_min, lat_max, lon_max = bb
                inc_conditions.append("lat BETWEEN ? AND ?")
                inc_conditions.append("lon BETWEEN ? AND ?")
                inc_params.extend([lat_min, lat_max, lon_min, lon_max])
        inc_where = " AND ".join(inc_conditions)
        cur.execute(
            f"SELECT COUNT(*) as total, "
            f"SUM(CASE WHEN severity='roja' THEN 1 ELSE 0 END) as critical, "
            f"SUM(CASE WHEN severity='naranja' THEN 1 ELSE 0 END) as high, "
            f"SUM(CASE WHEN status='detectado' THEN 1 ELSE 0 END) as detected, "
            f"SUM(CASE WHEN status='evaluado' THEN 1 ELSE 0 END) as evaluated, "
            f"SUM(CASE WHEN status='en_respuesta' THEN 1 ELSE 0 END) as in_response, "
            f"SUM(CASE WHEN status='resuelto' THEN 1 ELSE 0 END) as resolved "
            f"FROM incidents WHERE {inc_where}",
            inc_params,
        )
        inc_stats = _row_to_dict(cur.fetchone())

    needs_open = need_stats.get("open_count") or 0
    needs_total = need_stats.get("total") or 0
    resources_available = res_stats.get("available") or 0
    total_quantity = res_stats.get("total_quantity") or 0
    available_qty = res_stats.get("total_available_qty") or 0

    # Resource gap: uncovered needs
    total_needed = need_stats.get("total_quantity") or 0
    total_covered = need_stats.get("total_covered") or 0
    resource_gap = max(total_needed - total_covered, 0)

    # Operational load: ratio of active assignments to available resources
    active_assignments = (assign_stats.get("active") or 0) + (assign_stats.get("in_progress") or 0)
    operational_load = min(active_assignments / max(resources_available, 1), 1.0)

    return {
        "needs": {
            "total": needs_total,
            "open": needs_open,
            "covered": need_stats.get("covered_count") or 0,
            "critical_open": need_stats.get("critical_open") or 0,
            "high_open": need_stats.get("high_open") or 0,
        },
        "alerts": {
            "total_active": alert_stats.get("total_active") or 0,
            "critical": alert_stats.get("critical_alerts") or 0,
            "high": alert_stats.get("high_alerts") or 0,
        },
        "resources": {
            "total": res_stats.get("total") or 0,
            "available": resources_available,
            "assigned": res_stats.get("assigned") or 0,
            "total_quantity": total_quantity,
            "available_quantity": available_qty,
        },
        "assignments": {
            "total": assign_stats.get("total") or 0,
            "active": active_assignments,
        },
        "incidents": {
            "total": inc_stats.get("total") or 0,
            "critical": inc_stats.get("critical") or 0,
            "high": inc_stats.get("high") or 0,
            "detected": inc_stats.get("detected") or 0,
            "evaluated": inc_stats.get("evaluated") or 0,
            "in_response": inc_stats.get("in_response") or 0,
            "resolved": inc_stats.get("resolved") or 0,
        },
        "metrics": {
            "resource_gap": resource_gap,
            "operational_load": round(operational_load, 3),
            "needs_open": needs_open,
            "needs_uncovered": resource_gap,
            "response_gap": resource_gap,
        },
        "source": "anexo_risk",
        "generated_at": _now_iso(),
    }


# ---------------------------------------------------------------------------
# GET /api/operational/incidents
# ---------------------------------------------------------------------------
@router.get("/incidents")
def get_operational_incidents(
    status: Optional[str] = Query(None, description="detectado | evaluado | en_respuesta | resuelto | cancelado"),
    severity: Optional[str] = Query(None, description="verde | amarilla | naranja | roja"),
    event_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
):
    """Return incidents with optional filters for the frontend list panel."""
    conditions = []
    params: list = []

    if status:
        conditions.append("status = ?")
        params.append(status)
    if severity:
        conditions.append("severity = ?")
        params.append(severity)
    if event_type:
        conditions.append("event_type = ?")
        params.append(event_type)
    if is_active is not None:
        conditions.append("is_active = ?")
        params.append(1 if is_active else 0)

    where = " AND ".join(conditions) if conditions else "1=1"
    sql = f"SELECT id, title, description, event_type, source, severity, magnitude, lat, lon, h3_index, status, is_active, priority_score, exposure_score, created_at, updated_at FROM incidents WHERE {where} ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    with get_cursor() as cur:
        cur.execute(sql, params)
        rows = [_row_to_dict(r) for r in cur.fetchall()]

    return {
        "incidents": rows,
        "total": len(rows),
        "source": "anexo_risk",
        "generated_at": _now_iso(),
    }


# ---------------------------------------------------------------------------
# GET /api/operational/h3/{h3_index}
# ---------------------------------------------------------------------------
@router.get("/h3/{h3_index}")
def get_operational_h3_cell(h3_index: str):
    """Return operational metrics for a specific H3 cell.

    Aggregates needs, resources, alerts, and assignments within the cell.
    """
    try:
        from geodata.services.h3_resolver import h3_to_center
        center = h3_to_center(h3_index)
        if not center:
            return {"error": "invalid_h3_index", "h3_index": h3_index, "source": "anexo_risk"}
        clat, clon = center
    except Exception:
        return {"error": "invalid_h3_index", "h3_index": h3_index, "source": "anexo_risk"}

    # Use approximate cell bounds
    lat_min, lat_max = clat - 1.5, clat + 1.5
    lon_min, lon_max = clon - 1.5, clon + 1.5

    with get_cursor() as cur:
        # Needs in cell
        cur.execute(
            "SELECT COUNT(*) as total, "
            "SUM(CASE WHEN estado='abierta' THEN 1 ELSE 0 END) as open_count, "
            "SUM(CASE WHEN prioridad='critica' AND estado='abierta' THEN 1 ELSE 0 END) as critical, "
            "SUM(CASE WHEN prioridad='alta' AND estado='abierta' THEN 1 ELSE 0 END) as high "
            "FROM necesidades WHERE latitud BETWEEN ? AND ? AND longitud BETWEEN ? AND ?",
            (lat_min, lat_max, lon_min, lon_max),
        )
        needs = _row_to_dict(cur.fetchone())

        # Resources in cell
        cur.execute(
            "SELECT COUNT(*) as total, "
            "SUM(CASE WHEN status='disponible' THEN 1 ELSE 0 END) as available "
            "FROM resources WHERE latitud BETWEEN ? AND ? AND longitud BETWEEN ? AND ?",
            (lat_min, lat_max, lon_min, lon_max),
        )
        resources = _row_to_dict(cur.fetchone())

        # Active alerts in cell
        cur.execute(
            "SELECT COUNT(*) as total, "
            "SUM(CASE WHEN severidad IN ('RED') THEN 1 ELSE 0 END) as critical "
            "FROM alertas WHERE is_active=1 AND lat BETWEEN ? AND ? AND lon BETWEEN ? AND ?",
            (lat_min, lat_max, lon_min, lon_max),
        )
        alerts = _row_to_dict(cur.fetchone())

    needs_open = needs.get("open_count") or 0
    resources_available = resources.get("available") or 0
    needs_critical = needs.get("critical") or 0
    resource_gap = max(needs_open - resources_available, 0)
    operational_load = min(needs_open / max(resources_available, 1), 1.0) if resources_available > 0 else (1.0 if needs_open > 0 else 0.0)

    return {
        "h3_index": h3_index,
        "centroid": {"lat": clat, "lon": clon},
        "needs": {
            "total": needs.get("total") or 0,
            "open": needs_open,
            "critical": needs_critical,
            "high": needs.get("high") or 0,
        },
        "resources": {
            "total": resources.get("total") or 0,
            "available": resources_available,
        },
        "alerts": {
            "total": alerts.get("total") or 0,
            "critical": alerts.get("critical") or 0,
        },
        "metrics": {
            "resource_gap": resource_gap,
            "operational_load": round(operational_load, 3),
            "needs_open": needs_open,
            "needs_uncovered": resource_gap,
        },
        "source": "anexo_risk",
        "generated_at": _now_iso(),
    }
