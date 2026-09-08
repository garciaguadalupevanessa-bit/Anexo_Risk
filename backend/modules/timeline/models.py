"""SQLite CRUD for Timeline Events."""
from __future__ import annotations

import json
from typing import Optional

from db.database import get_cursor


def record_event(
    incident_id: int,
    event_type: str,
    description: str,
    need_id: Optional[int] = None,
    resource_id: Optional[int] = None,
    assignment_id: Optional[int] = None,
    actor: Optional[str] = None,
    priority_score: Optional[float] = None,
    severity: Optional[str] = None,
    status_snapshot: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> dict:
    """Record a timeline event."""
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO timeline_events
               (incident_id, need_id, resource_id, assignment_id,
                event_type, description, actor,
                priority_score, severity, status_snapshot, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                incident_id,
                need_id,
                resource_id,
                assignment_id,
                event_type,
                description,
                actor,
                priority_score,
                severity,
                status_snapshot,
                json.dumps(metadata) if metadata else None,
            ),
        )
        row_id = cur.lastrowid

    return get_event(row_id)


def get_event(event_id: int) -> Optional[dict]:
    """Get a single timeline event."""
    with get_cursor() as cur:
        cur.execute("SELECT * FROM timeline_events WHERE id = ?", (event_id,))
        row = cur.fetchone()
        return _row_to_dict(row) if row else None


def get_incident_timeline(incident_id: int, limit: int = 100) -> list[dict]:
    """Get all timeline events for an incident, ordered by time."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT * FROM timeline_events
               WHERE incident_id = ?
               ORDER BY created_at ASC
               LIMIT ?""",
            (incident_id, limit),
        )
        return [_row_to_dict(r) for r in cur.fetchall()]


def get_recent_events(limit: int = 50) -> list[dict]:
    """Get recent timeline events across all incidents."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT * FROM timeline_events
               ORDER BY created_at DESC
               LIMIT ?""",
            (limit,),
        )
        return [_row_to_dict(r) for r in cur.fetchall()]


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
