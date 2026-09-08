"""SQLite CRUD for Incidents."""
from __future__ import annotations

import json
from typing import Optional

from db.database import get_cursor


def list_incidents(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    event_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    limit: int = 100,
) -> list[dict]:
    """List incidents with optional filters."""
    conditions = []
    params = []

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
    sql = f"SELECT * FROM incidents WHERE {where} ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    with get_cursor() as cur:
        cur.execute(sql, params)
        return [_row_to_dict(r) for r in cur.fetchall()]


def get_incident(incident_id: int) -> Optional[dict]:
    """Get a single incident by ID."""
    with get_cursor() as cur:
        cur.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,))
        row = cur.fetchone()
        return _row_to_dict(row) if row else None


def create_incident(
    title: str,
    lat: float,
    lon: float,
    event_type: str = "alerta",
    source: str = "manual",
    external_id: Optional[str] = None,
    severity: str = "amarilla",
    magnitude: Optional[float] = None,
    description: Optional[str] = None,
    direccion: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> dict:
    """Create a new incident."""
    try:
        from geodata.services.h3_resolver import latlon_to_h3
        h3_index = latlon_to_h3(lat, lon)
    except Exception:
        h3_index = None

    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO incidents
               (title, description, event_type, source, external_id,
                severity, magnitude, lat, lon, h3_index, direccion, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                title,
                description,
                event_type,
                source,
                external_id,
                severity,
                magnitude,
                lat,
                lon,
                h3_index,
                direccion,
                json.dumps(metadata) if metadata else None,
            ),
        )
        row_id = cur.lastrowid

    return get_incident(row_id)


def update_incident_status(incident_id: int, status: str) -> Optional[dict]:
    """Update incident status."""
    with get_cursor() as cur:
        cur.execute(
            "UPDATE incidents SET status = ?, updated_at = datetime('now') WHERE id = ?",
            (status, incident_id),
        )
        if cur.rowcount == 0:
            return None
        if status in ("resuelto", "cancelado"):
            cur.execute(
                "UPDATE incidents SET is_active = 0, updated_at = datetime('now') WHERE id = ?",
                (incident_id,),
            )
    return get_incident(incident_id)


def update_incident_scores(
    incident_id: int,
    priority_score: Optional[float] = None,
    exposure_score: Optional[float] = None,
) -> Optional[dict]:
    """Update incident computed scores."""
    with get_cursor() as cur:
        updates = ["updated_at = datetime('now')"]
        params = []
        if priority_score is not None:
            updates.append("priority_score = ?")
            params.append(priority_score)
        if exposure_score is not None:
            updates.append("exposure_score = ?")
            params.append(exposure_score)
        params.append(incident_id)
        cur.execute(
            f"UPDATE incidents SET {', '.join(updates)} WHERE id = ?",
            params,
        )
    return get_incident(incident_id)


def get_incidents_by_h3(h3_index: str) -> list[dict]:
    """Get all incidents in an H3 cell."""
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM incidents WHERE h3_index = ? ORDER BY created_at DESC",
            (h3_index,),
        )
        return [_row_to_dict(r) for r in cur.fetchall()]


def get_active_incident_count() -> int:
    """Count active incidents."""
    with get_cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM incidents WHERE is_active = 1")
        return cur.fetchone()[0]


def _row_to_dict(row) -> dict:
    if row is None:
        return {}
    d = {key: row[key] for key in row.keys()}
    if d.get("metadata") and isinstance(d["metadata"], str):
        try:
            d["metadata"] = json.loads(d["metadata"])
        except (json.JSONDecodeError, TypeError):
            pass
    return d
