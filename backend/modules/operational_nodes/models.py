"""Operational Nodes data access layer."""
import json
import uuid
from db.database import get_cursor


def create_node(node_data):
    """Insert a new operational node."""
    node_id = node_data.get("id") or f"node_{uuid.uuid4().hex[:12]}"
    with get_cursor() as cur:
        cur.execute(
            """INSERT OR REPLACE INTO operational_nodes
            (id, external_id, node_type, name, description,
             lat, lon, h3_index, address, city, province, country_code,
             capacity, current_occupancy, capabilities_json,
             status, is_active, source, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                node_id,
                node_data.get("external_id"),
                node_data["node_type"],
                node_data["name"],
                node_data.get("description", ""),
                node_data["lat"],
                node_data["lon"],
                node_data.get("h3_index"),
                node_data.get("address"),
                node_data.get("city"),
                node_data.get("province"),
                node_data.get("country_code"),
                node_data.get("capacity"),
                node_data.get("current_occupancy", 0),
                json.dumps(node_data.get("capabilities")) if node_data.get("capabilities") else None,
                node_data.get("status", "active"),
                1 if node_data.get("is_active", True) else 0,
                node_data.get("source", "manual"),
                json.dumps(node_data.get("metadata")) if node_data.get("metadata") else None,
            ),
        )
    return get_node(node_id)


def get_node(node_id):
    """Get a single node by ID."""
    with get_cursor() as cur:
        row = cur.execute("SELECT * FROM operational_nodes WHERE id = ?", (node_id,)).fetchone()
        if row:
            return _row_to_response(row)
    return None


def list_nodes(
    node_type=None, status=None, country_code=None, is_active=True,
    h3_index=None, limit=100, offset=0,
):
    """List nodes with optional filters."""
    query = "SELECT * FROM operational_nodes WHERE 1=1"
    params = []
    if node_type:
        query += " AND node_type = ?"
        params.append(node_type)
    if status:
        query += " AND status = ?"
        params.append(status)
    if country_code:
        query += " AND country_code = ?"
        params.append(country_code)
    if is_active is not None:
        query += " AND is_active = ?"
        params.append(1 if is_active else 0)
    if h3_index:
        query += " AND h3_index = ?"
        params.append(h3_index)
    query += " ORDER BY name LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    with get_cursor() as cur:
        rows = cur.execute(query, params).fetchall()
        return [_row_to_response(r) for r in rows]


def update_node(node_id, updates):
    """Update node fields."""
    allowed = {
        "external_id", "node_type", "name", "description", "lat", "lon",
        "h3_index", "address", "city", "province", "country_code",
        "capacity", "current_occupancy", "capabilities_json", "status",
        "is_active", "source", "metadata_json",
    }
    fields = []
    values = []
    for k, v in updates.items():
        if k in allowed:
            if k in ("capabilities_json", "metadata_json") and isinstance(v, (dict, list)):
                v = json.dumps(v)
            fields.append(f"{k} = ?")
            values.append(v)
    if not fields:
        return get_node(node_id)
    fields.append("updated_at = CURRENT_TIMESTAMP")
    values.append(node_id)
    with get_cursor() as cur:
        cur.execute(f"UPDATE operational_nodes SET {', '.join(fields)} WHERE id = ?", values)
    return get_node(node_id)


def delete_node(node_id):
    """Soft-delete a node."""
    with get_cursor() as cur:
        cur.execute(
            "UPDATE operational_nodes SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (node_id,),
        )
    return get_node(node_id)


def count_nodes(node_type=None, is_active=True):
    """Count nodes with optional filters."""
    query = "SELECT COUNT(*) FROM operational_nodes WHERE 1=1"
    params = []
    if node_type:
        query += " AND node_type = ?"
        params.append(node_type)
    if is_active is not None:
        query += " AND is_active = ?"
        params.append(1 if is_active else 0)
    with get_cursor() as cur:
        return cur.execute(query, params).fetchone()[0]


def _row_to_response(row):
    """Convert sqlite3.Row to API response dict."""
    d = dict(row)
    for key in ("capabilities_json", "metadata_json"):
        if key in d and d[key]:
            try:
                d[key] = json.loads(d[key])
            except (json.JSONDecodeError, TypeError):
                pass
    if "capabilities_json" in d:
        d["capabilities"] = d.pop("capabilities_json")
    if "metadata_json" in d:
        d["metadata"] = d.pop("metadata_json")
    if "is_active" in d:
        d["is_active"] = bool(d["is_active"])
    return d
