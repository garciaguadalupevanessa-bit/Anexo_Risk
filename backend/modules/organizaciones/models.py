"""Models para Organizaciones y Usuarios Operacionales."""
from __future__ import annotations

from db.database import get_cursor


def _row_to_dict(row) -> dict:
    if row is None:
        return None
    return dict(row)


def list_organizations(org_type: str | None = None, region: str | None = None) -> list[dict]:
    query = "SELECT * FROM organizations WHERE active = 1"
    params: list = []
    if org_type:
        query += " AND type = ?"
        params.append(org_type)
    if region:
        query += " AND region LIKE ?"
        params.append(f"%{region}%")
    query += " ORDER BY name"
    with get_cursor() as cur:
        cur.execute(query, params)
        return [_row_to_dict(r) for r in cur.fetchall()]


def get_organization(org_id: int) -> dict | None:
    with get_cursor() as cur:
        cur.execute("SELECT * FROM organizations WHERE id = ?", (org_id,))
        return _row_to_dict(cur.fetchone())


def create_organization(name: str, org_type: str, region: str | None = None) -> dict:
    with get_cursor() as cur:
        cur.execute(
            "INSERT INTO organizations (name, type, region) VALUES (?, ?, ?)",
            (name, org_type, region),
        )
        cur.execute("SELECT * FROM organizations WHERE id = last_insert_rowid()")
        return _row_to_dict(cur.fetchone())


def list_operational_users(org_id: int | None = None, role: str | None = None) -> list[dict]:
    query = "SELECT * FROM operational_users WHERE active = 1"
    params: list = []
    if org_id:
        query += " AND organization_id = ?"
        params.append(org_id)
    if role:
        query += " AND role = ?"
        params.append(role)
    query += " ORDER BY display_name"
    with get_cursor() as cur:
        cur.execute(query, params)
        return [_row_to_dict(r) for r in cur.fetchall()]


def create_operational_user(
    org_id: int, username: str, display_name: str, role: str
) -> dict:
    with get_cursor() as cur:
        cur.execute(
            "INSERT INTO operational_users (organization_id, username, display_name, role) VALUES (?, ?, ?, ?)",
            (org_id, username, display_name, role),
        )
        cur.execute("SELECT * FROM operational_users WHERE id = last_insert_rowid()")
        return _row_to_dict(cur.fetchone())
