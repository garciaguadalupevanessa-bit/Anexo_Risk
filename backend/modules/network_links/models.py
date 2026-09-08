"""Network Links data access layer."""
import json
import uuid
from db.database import get_cursor


def create_link(link_data):
    """Insert a new network link."""
    link_id = link_data.get("id") or f"link_{uuid.uuid4().hex[:12]}"
    with get_cursor() as cur:
        cur.execute(
            """INSERT OR REPLACE INTO network_links
            (id, external_id, link_type, name, description,
             start_node_id, end_node_id,
             start_lat, start_lon, end_lat, end_lon,
             h3_start, h3_end, distance_km, estimated_time_min,
             status, capacity, restrictions_json, source, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                link_id,
                link_data.get("external_id"),
                link_data["link_type"],
                link_data["name"],
                link_data.get("description", ""),
                link_data.get("start_node_id"),
                link_data.get("end_node_id"),
                link_data.get("start_lat"),
                link_data.get("start_lon"),
                link_data.get("end_lat"),
                link_data.get("end_lon"),
                link_data.get("h3_start"),
                link_data.get("h3_end"),
                link_data.get("distance_km"),
                link_data.get("estimated_time_min"),
                link_data.get("status", "open"),
                link_data.get("capacity"),
                json.dumps(link_data.get("restrictions")) if link_data.get("restrictions") else None,
                link_data.get("source", "manual"),
                json.dumps(link_data.get("metadata")) if link_data.get("metadata") else None,
            ),
        )
    return get_link(link_id)


def get_link(link_id):
    """Get a single link by ID."""
    with get_cursor() as cur:
        row = cur.execute("SELECT * FROM network_links WHERE id = ?", (link_id,)).fetchone()
        if row:
            return _row_to_response(row)
    return None


def list_links(
    link_type=None, status=None, start_node_id=None, end_node_id=None,
    limit=100, offset=0,
):
    """List links with optional filters."""
    query = "SELECT * FROM network_links WHERE 1=1"
    params = []
    if link_type:
        query += " AND link_type = ?"
        params.append(link_type)
    if status:
        query += " AND status = ?"
        params.append(status)
    if start_node_id:
        query += " AND start_node_id = ?"
        params.append(start_node_id)
    if end_node_id:
        query += " AND end_node_id = ?"
        params.append(end_node_id)
    query += " ORDER BY name LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    with get_cursor() as cur:
        rows = cur.execute(query, params).fetchall()
        return [_row_to_response(r) for r in rows]


def update_link(link_id, updates):
    """Update link fields."""
    allowed = {
        "external_id", "link_type", "name", "description",
        "start_node_id", "end_node_id", "start_lat", "start_lon",
        "end_lat", "end_lon", "h3_start", "h3_end",
        "distance_km", "estimated_time_min", "status", "capacity",
        "restrictions_json", "source", "metadata_json",
    }
    fields = []
    values = []
    for k, v in updates.items():
        if k in allowed:
            if k in ("restrictions_json", "metadata_json") and isinstance(v, (dict, list)):
                v = json.dumps(v)
            fields.append(f"{k} = ?")
            values.append(v)
    if not fields:
        return get_link(link_id)
    fields.append("updated_at = CURRENT_TIMESTAMP")
    values.append(link_id)
    with get_cursor() as cur:
        cur.execute(f"UPDATE network_links SET {', '.join(fields)} WHERE id = ?", values)
    return get_link(link_id)


def delete_link(link_id):
    """Soft-delete a link (set status to 'closed')."""
    return update_link(link_id, {"status": "closed"})


def count_links(link_type=None, status=None):
    """Count links with optional filters."""
    query = "SELECT COUNT(*) FROM network_links WHERE 1=1"
    params = []
    if link_type:
        query += " AND link_type = ?"
        params.append(link_type)
    if status:
        query += " AND status = ?"
        params.append(status)
    with get_cursor() as cur:
        return cur.execute(query, params).fetchone()[0]


def get_links_for_node(node_id):
    """Get all links connected to a node (as start or end)."""
    with get_cursor() as cur:
        rows = cur.execute(
            """SELECT * FROM network_links
            WHERE (start_node_id = ? OR end_node_id = ?) AND status != 'closed'
            ORDER BY name""",
            (node_id, node_id),
        ).fetchall()
        return [_row_to_response(r) for r in rows]


def _row_to_response(row):
    """Convert sqlite3.Row to API response dict."""
    d = dict(row)
    for key in ("restrictions_json", "metadata_json"):
        if key in d and d[key]:
            try:
                d[key] = json.loads(d[key])
            except (json.JSONDecodeError, TypeError):
                pass
    if "restrictions_json" in d:
        d["restrictions"] = d.pop("restrictions_json")
    if "metadata_json" in d:
        d["metadata"] = d.pop("metadata_json")
    return d
