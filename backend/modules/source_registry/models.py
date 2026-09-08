"""Source Registry data access layer."""
import json
from db.database import get_cursor


def register_source(source_data):
    """Insert or update a source in the registry."""
    with get_cursor() as cur:
        cur.execute(
            """INSERT OR REPLACE INTO source_registry
            (id, name, scope, source_type, data_types,
             supports_point, supports_bbox, supports_region,
             update_interval_seconds, authentication, license,
             status, cache_ttl_seconds, endpoint_url, metadata_json,
             updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
            (
                source_data["id"],
                source_data["name"],
                source_data.get("scope", "global"),
                source_data.get("source_type", "api"),
                json.dumps(source_data.get("data_types", [])),
                1 if source_data.get("supports_point") else 0,
                1 if source_data.get("supports_bbox") else 0,
                1 if source_data.get("supports_region") else 0,
                source_data.get("update_interval_seconds", 300),
                source_data.get("authentication", "none"),
                source_data.get("license"),
                source_data.get("status", "active"),
                source_data.get("cache_ttl_seconds", 300),
                source_data.get("endpoint_url"),
                json.dumps(source_data.get("metadata")) if source_data.get("metadata") else None,
            ),
        )
    return get_source(source_data["id"])


def get_source(source_id):
    """Get a single source by ID."""
    with get_cursor() as cur:
        row = cur.execute("SELECT * FROM source_registry WHERE id = ?", (source_id,)).fetchone()
        if row:
            return _row_to_response(row)
    return None


def list_sources(scope=None, status=None, source_type=None):
    """List all sources with optional filters."""
    query = "SELECT * FROM source_registry WHERE 1=1"
    params = []
    if scope:
        query += " AND scope = ?"
        params.append(scope)
    if status:
        query += " AND status = ?"
        params.append(status)
    if source_type:
        query += " AND source_type = ?"
        params.append(source_type)
    query += " ORDER BY scope, name"
    with get_cursor() as cur:
        rows = cur.execute(query, params).fetchall()
        return [_row_to_response(r) for r in rows]


def update_source_status(source_id, status, last_fetch=None, error=None, latency_ms=None):
    """Update source health status."""
    with get_cursor() as cur:
        if status == "active" and not error:
            cur.execute(
                """UPDATE source_registry
                SET status = ?, last_successful_fetch = ?, latency_ms = ?,
                    last_failure = NULL, last_error = NULL, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?""",
                (status, last_fetch, latency_ms, source_id),
            )
        else:
            cur.execute(
                """UPDATE source_registry
                SET status = ?, last_failure = CURRENT_TIMESTAMP, last_error = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?""",
                (status, error, source_id),
            )
    return get_source(source_id)


def delete_source(source_id):
    """Remove a source from the registry."""
    with get_cursor() as cur:
        cur.execute("DELETE FROM source_registry WHERE id = ?", (source_id,))
    return True


def get_source_health_summary():
    """Get aggregated health summary of all sources."""
    with get_cursor() as cur:
        rows = cur.execute(
            "SELECT id, name, scope, status, last_successful_fetch, last_failure, latency_ms FROM source_registry ORDER BY scope, name"
        ).fetchall()
        return [_row_to_response(r) for r in rows]


def _row_to_response(row):
    """Convert sqlite3.Row to API response dict."""
    d = dict(row)
    for key in ("data_types", "metadata_json"):
        if key in d and d[key]:
            try:
                d[key] = json.loads(d[key])
            except (json.JSONDecodeError, TypeError):
                pass
    if "metadata_json" in d:
        d["metadata"] = d.pop("metadata_json")
    for bool_key in ("supports_point", "supports_bbox", "supports_region"):
        if bool_key in d:
            d[bool_key] = bool(d[bool_key])
    return d
