"""Normalized Events data access layer."""
import json
import uuid
from db.database import get_cursor


def store_event(event_data):
    """Store a normalized event."""
    event_id = event_data.get("id") or f"evt_{uuid.uuid4().hex[:12]}"
    with get_cursor() as cur:
        cur.execute(
            """INSERT OR REPLACE INTO normalized_events
            (id, external_id, entity_type, source, title, description,
             timestamp, updated_at, severity, severity_float,
             lat, lon, geometry_type, geometry_json,
             country, region, status, is_active, h3_index,
             magnitude, depth, confidence, raw_metadata_json, provenance_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                event_id,
                event_data.get("external_id"),
                event_data["entity_type"],
                event_data["source"],
                event_data["title"],
                event_data.get("description", ""),
                event_data.get("timestamp"),
                event_data.get("updated_at"),
                event_data.get("severity"),
                event_data.get("severity_float"),
                event_data.get("lat"),
                event_data.get("lon"),
                event_data.get("geometry_type"),
                json.dumps(event_data["geometry"]) if event_data.get("geometry") else None,
                event_data.get("country"),
                event_data.get("region"),
                event_data.get("status", "active"),
                1 if event_data.get("is_active", True) else 0,
                event_data.get("h3_index"),
                event_data.get("magnitude"),
                event_data.get("depth"),
                event_data.get("confidence"),
                json.dumps(event_data["raw_metadata"]) if event_data.get("raw_metadata") else None,
                json.dumps(event_data["provenance"]) if event_data.get("provenance") else None,
            ),
        )
    return get_event(event_id)


def store_events_batch(events):
    """Store multiple normalized events efficiently."""
    stored = []
    for event in events:
        try:
            stored.append(store_event(event))
        except Exception:
            pass
    return stored


def get_event(event_id):
    """Get a single event by ID."""
    with get_cursor() as cur:
        row = cur.execute("SELECT * FROM normalized_events WHERE id = ?", (event_id,)).fetchone()
        if row:
            return _row_to_response(row)
    return None


def list_events(
    entity_type=None, source=None, h3_index=None, severity=None,
    status=None, is_active=True, since=None, until=None,
    limit=100, offset=0,
):
    """List events with optional filters."""
    query = "SELECT * FROM normalized_events WHERE 1=1"
    params = []
    if entity_type:
        query += " AND entity_type = ?"
        params.append(entity_type)
    if source:
        query += " AND source = ?"
        params.append(source)
    if h3_index:
        query += " AND h3_index = ?"
        params.append(h3_index)
    if severity:
        query += " AND severity = ?"
        params.append(severity)
    if status:
        query += " AND status = ?"
        params.append(status)
    if is_active is not None:
        query += " AND is_active = ?"
        params.append(1 if is_active else 0)
    if since:
        query += " AND timestamp >= ?"
        params.append(since)
    if until:
        query += " AND timestamp <= ?"
        params.append(until)
    query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    with get_cursor() as cur:
        rows = cur.execute(query, params).fetchall()
        return [_row_to_response(r) for r in rows]


def deactivate_event(event_id):
    """Soft-deactivate an event."""
    with get_cursor() as cur:
        cur.execute(
            "UPDATE normalized_events SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (event_id,),
        )
    return get_event(event_id)


def get_events_by_source(source):
    """Get all active events from a specific source."""
    return list_events(source=source, is_active=True)


def count_events(entity_type=None, source=None, is_active=True):
    """Count events with optional filters."""
    query = "SELECT COUNT(*) FROM normalized_events WHERE 1=1"
    params = []
    if entity_type:
        query += " AND entity_type = ?"
        params.append(entity_type)
    if source:
        query += " AND source = ?"
        params.append(source)
    if is_active is not None:
        query += " AND is_active = ?"
        params.append(1 if is_active else 0)
    with get_cursor() as cur:
        return cur.execute(query, params).fetchone()[0]


def _row_to_response(row):
    """Convert sqlite3.Row to API response dict."""
    d = dict(row)
    for key in ("geometry_json", "raw_metadata_json", "provenance_json"):
        if key in d and d[key]:
            try:
                d[key] = json.loads(d[key])
            except (json.JSONDecodeError, TypeError):
                pass
    if "geometry_json" in d:
        d["geometry"] = d.pop("geometry_json")
    if "raw_metadata_json" in d:
        d["raw_metadata"] = d.pop("raw_metadata_json")
    if "provenance_json" in d:
        d["provenance"] = d.pop("provenance_json")
    if "is_active" in d:
        d["is_active"] = bool(d["is_active"])
    return d
