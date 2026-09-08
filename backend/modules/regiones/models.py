"""Region/AOI data access layer."""
import json
from db.database import get_connection, get_cursor


def create_region(region_data):
    """Insert a new region and return it."""
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO regions
            (id, name, level, parent_id, country_code, h3_resolution,
             geometry_type, geometry_json, bbox_min_lat, bbox_min_lon,
             bbox_max_lat, bbox_max_lon, center_lat, center_lon,
             radius_km, is_active, source, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                region_data["id"],
                region_data["name"],
                region_data.get("level", "municipality"),
                region_data.get("parent_id"),
                region_data.get("country_code"),
                region_data.get("h3_resolution", 3),
                region_data.get("geometry_type"),
                json.dumps(region_data.get("geometry")) if region_data.get("geometry") else None,
                region_data.get("bbox_min_lat"),
                region_data.get("bbox_min_lon"),
                region_data.get("bbox_max_lat"),
                region_data.get("bbox_max_lon"),
                region_data.get("center_lat"),
                region_data.get("center_lon"),
                region_data.get("radius_km"),
                1 if region_data.get("is_active", True) else 0,
                region_data.get("source", "manual"),
                json.dumps(region_data.get("metadata")) if region_data.get("metadata") else None,
            ),
        )
    return get_region(region_data["id"])


def get_region(region_id):
    """Get a single region by ID."""
    with get_cursor() as cur:
        row = cur.execute("SELECT * FROM regions WHERE id = ?", (region_id,)).fetchone()
        if row:
            return _row_to_response(row)
    return None


def list_regions(level=None, country_code=None, parent_id=None, is_active=True):
    """List regions with optional filters."""
    query = "SELECT * FROM regions WHERE 1=1"
    params = []
    if level:
        query += " AND level = ?"
        params.append(level)
    if country_code:
        query += " AND country_code = ?"
        params.append(country_code)
    if parent_id:
        query += " AND parent_id = ?"
        params.append(parent_id)
    if is_active is not None:
        query += " AND is_active = ?"
        params.append(1 if is_active else 0)
    query += " ORDER BY level, name"
    with get_cursor() as cur:
        rows = cur.execute(query, params).fetchall()
        return [_row_to_response(r) for r in rows]


def update_region(region_id, updates):
    """Update region fields."""
    allowed = {
        "name", "level", "parent_id", "country_code", "h3_resolution",
        "geometry_type", "geometry_json", "bbox_min_lat", "bbox_min_lon",
        "bbox_max_lat", "bbox_max_lon", "center_lat", "center_lon",
        "radius_km", "is_active", "source", "metadata_json",
    }
    fields = []
    values = []
    for k, v in updates.items():
        if k in allowed:
            if k == "geometry_json" and isinstance(v, (dict, list)):
                v = json.dumps(v)
            if k == "metadata_json" and isinstance(v, (dict, list)):
                v = json.dumps(v)
            fields.append(f"{k} = ?")
            values.append(v)
    if not fields:
        return get_region(region_id)
    fields.append("updated_at = CURRENT_TIMESTAMP")
    values.append(region_id)
    with get_cursor() as cur:
        cur.execute(f"UPDATE regions SET {', '.join(fields)} WHERE id = ?", values)
    return get_region(region_id)


def delete_region(region_id):
    """Soft-delete a region (set is_active=0)."""
    with get_cursor() as cur:
        cur.execute("UPDATE regions SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (region_id,))
    return get_region(region_id)


def add_region_source(region_id, source_id, is_enabled=True, priority=0, config=None):
    """Link a source to a region."""
    with get_cursor() as cur:
        cur.execute(
            """INSERT OR REPLACE INTO region_sources
            (region_id, source_id, is_enabled, priority, config_json)
            VALUES (?, ?, ?, ?, ?)""",
            (region_id, source_id, 1 if is_enabled else 0, priority,
             json.dumps(config) if config else None),
        )
    return get_region_sources(region_id)


def get_region_sources(region_id):
    """Get all sources linked to a region."""
    with get_cursor() as cur:
        rows = cur.execute(
            "SELECT * FROM region_sources WHERE region_id = ? ORDER BY priority DESC",
            (region_id,),
        ).fetchall()
        return [_row_to_response(r) for r in rows]


def remove_region_source(region_id, source_id):
    """Remove a source from a region."""
    with get_cursor() as cur:
        cur.execute(
            "DELETE FROM region_sources WHERE region_id = ? AND source_id = ?",
            (region_id, source_id),
        )


def get_region_children(region_id):
    """Get all child regions of a region."""
    with get_cursor() as cur:
        rows = cur.execute(
            "SELECT * FROM regions WHERE parent_id = ? AND is_active = 1 ORDER BY name",
            (region_id,),
        ).fetchall()
        return [_row_to_response(r) for r in rows]


def get_active_region():
    """Get the currently active region (first active one)."""
    with get_cursor() as cur:
        row = cur.execute(
            "SELECT * FROM regions WHERE is_active = 1 ORDER BY level, name LIMIT 1"
        ).fetchone()
        if row:
            return _row_to_dict(row)
    return None


def _row_to_dict(row):
    """Convert sqlite3.Row to dict with JSON parsing and field mapping."""
    d = dict(row)
    for key in ("geometry_json", "metadata_json", "config_json"):
        if key in d and d[key]:
            try:
                d[key] = json.loads(d[key])
            except (json.JSONDecodeError, TypeError):
                pass
    if "is_active" in d:
        d["is_active"] = bool(d["is_active"])
    if "is_enabled" in d:
        d["is_enabled"] = bool(d["is_enabled"])
    return d


def _row_to_response(row):
    """Convert sqlite3.Row to API response dict (geometry_json -> geometry)."""
    d = _row_to_dict(row)
    if "geometry_json" in d:
        d["geometry"] = d.pop("geometry_json")
    if "metadata_json" in d:
        d["metadata"] = d.pop("metadata_json")
    return d
