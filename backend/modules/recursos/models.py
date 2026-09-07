"""Models para Recursos."""
from __future__ import annotations

from db.database import get_cursor


def _row_to_dict(row) -> dict:
    if row is None:
        return None
    return dict(row)


def list_resources(
    org_id: int | None = None,
    resource_type: str | None = None,
    status: str | None = None,
    lat_min: float | None = None,
    lat_max: float | None = None,
    lon_min: float | None = None,
    lon_max: float | None = None,
) -> list[dict]:
    query = "SELECT * FROM resources WHERE 1=1"
    params: list = []
    if org_id:
        query += " AND organization_id = ?"
        params.append(org_id)
    if resource_type:
        query += " AND type = ?"
        params.append(resource_type)
    if status:
        query += " AND status = ?"
        params.append(status)
    if lat_min is not None and lat_max is not None:
        query += " AND latitud BETWEEN ? AND ?"
        params.extend([lat_min, lat_max])
    if lon_min is not None and lon_max is not None:
        query += " AND longitud BETWEEN ? AND ?"
        params.extend([lon_min, lon_max])
    query += " ORDER BY created_at DESC"
    with get_cursor() as cur:
        cur.execute(query, params)
        return [_row_to_dict(r) for r in cur.fetchall()]


def get_resource(resource_id: int) -> dict | None:
    with get_cursor() as cur:
        cur.execute("SELECT * FROM resources WHERE id = ?", (resource_id,))
        return _row_to_dict(cur.fetchone())


def create_resource(
    org_id: int,
    resource_type: str,
    name: str,
    description: str | None,
    quantity: int,
    latitud: float | None,
    longitud: float | None,
) -> dict:
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO resources
               (organization_id, type, name, description, quantity, available_quantity, latitud, longitud)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (org_id, resource_type, name, description, quantity, quantity, latitud, longitud),
        )
        cur.execute("SELECT * FROM resources WHERE id = last_insert_rowid()")
        return _row_to_dict(cur.fetchone())


def update_resource(resource_id: int, **kwargs) -> dict | None:
    allowed = {"available_quantity", "status", "latitud", "longitud"}
    updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
    if not updates:
        return get_resource(resource_id)
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [resource_id]
    with get_cursor() as cur:
        cur.execute(f"UPDATE resources SET {set_clause}, updated_at = datetime('now') WHERE id = ?", values)
        cur.execute("SELECT * FROM resources WHERE id = ?", (resource_id,))
        return _row_to_dict(cur.fetchone())


def get_nearby_resources(lat: float, lon: float, radius_deg: float = 1.0) -> list[dict]:
    with get_cursor() as cur:
        cur.execute(
            """SELECT *, ABS(latitud - ?) + ABS(longitud - ?) as distance
               FROM resources
               WHERE status = 'disponible'
                 AND latitud IS NOT NULL
                 AND ABS(latitud - ?) <= ?
                 AND ABS(longitud - ?) <= ?
               ORDER BY distance
               LIMIT 20""",
            (lat, lon, lat, radius_deg, lon, radius_deg),
        )
        return [_row_to_dict(r) for r in cur.fetchall()]
