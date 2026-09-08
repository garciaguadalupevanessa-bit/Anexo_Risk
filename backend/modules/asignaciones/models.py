"""Models para Asignaciones — Persistencia SQLite de need_assignments.

La tabla need_assignments fue creada en la migración 011.
Este módulo implementa CRUD completo sobre esa tabla.
"""
from __future__ import annotations

from sqlite3 import Row
from typing import Any

from db.database import get_cursor
from modules.asignaciones.schemas import AssignmentCreate


class InvalidAssignmentTransition(ValueError):
    """Permite que la capa de rutas traduzca una transición inválida a HTTP 409."""


class InsufficientQuantityError(ValueError):
    """No hay suficiente cantidad disponible en el recurso."""


class AssignmentValidationError(ValueError):
    """Error de validación de asignación."""


def _row_to_dict(row: Row | None) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


def list_assignments(
    need_id: int | None = None,
    resource_id: int | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    conditions: list[str] = []
    params: list = []

    if need_id is not None:
        conditions.append("na.need_id = ?")
        params.append(need_id)
    if resource_id is not None:
        conditions.append("na.resource_id = ?")
        params.append(resource_id)
    if status is not None:
        conditions.append("na.status = ?")
        params.append(status)

    where = " WHERE " + " AND ".join(conditions) if conditions else ""

    query = f"""
        SELECT na.*,
               n.titulo AS need_title, n.tipo AS need_type, n.estado AS need_status,
               n.prioridad AS need_priority,
               r.name AS resource_name, r.type AS resource_type,
               r.organization_id AS resource_org_id,
               r.available_quantity AS resource_available,
               r.status AS resource_status
        FROM need_assignments na
        JOIN necesidades n ON na.need_id = n.id
        JOIN resources r ON na.resource_id = r.id
        {where}
        ORDER BY na.assigned_at DESC
    """

    with get_cursor() as cur:
        cur.execute(query, params)
        return [dict(row) for row in cur.fetchall()]


def get_assignment(assignment_id: int) -> dict[str, Any] | None:
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT na.*,
                   n.titulo AS need_title, n.tipo AS need_type, n.estado AS need_status,
                   n.prioridad AS need_priority,
                   r.name AS resource_name, r.type AS resource_type,
                   r.organization_id AS resource_org_id,
                   r.available_quantity AS resource_available,
                   r.status AS resource_status
            FROM need_assignments na
            JOIN necesidades n ON na.need_id = n.id
            JOIN resources r ON na.resource_id = r.id
            WHERE na.id = ?
            """,
            (assignment_id,),
        )
        return _row_to_dict(cur.fetchone())


def create_assignment(assignment: AssignmentCreate) -> dict[str, Any]:
    """Crea una asignación y retorna el registro con joins."""
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO need_assignments
               (need_id, resource_id, quantity_assigned, assigned_by, status, notes)
               VALUES (?, ?, ?, ?, 'asignado', ?)""",
            (
                assignment.need_id,
                assignment.resource_id,
                assignment.quantity_assigned,
                assignment.assigned_by,
                assignment.notes,
            ),
        )
        assignment_id = cur.lastrowid
        cur.execute("SELECT * FROM need_assignments WHERE id = ?", (assignment_id,))
        return dict(cur.fetchone())


def update_assignment_status(
    assignment_id: int,
    new_status: str,
) -> dict[str, Any] | None:
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM need_assignments WHERE id = ?",
            (assignment_id,),
        )
        current_row = cur.fetchone()
        if current_row is None:
            return None

        current_status = current_row["status"]
        if current_status == new_status:
            return dict(current_row)

        cur.execute(
            "UPDATE need_assignments SET status = ? WHERE id = ?",
            (new_status, assignment_id),
        )
        cur.execute("SELECT * FROM need_assignments WHERE id = ?", (assignment_id,))
        return _row_to_dict(cur.fetchone())


def get_assignments_for_need(need_id: int) -> list[dict[str, Any]]:
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT na.*,
                   r.name AS resource_name, r.type AS resource_type,
                   r.available_quantity AS resource_available
            FROM need_assignments na
            JOIN resources r ON na.resource_id = r.id
            WHERE na.need_id = ?
            ORDER BY na.assigned_at DESC
            """,
            (need_id,),
        )
        return [dict(row) for row in cur.fetchall()]


def get_assignments_for_resource(resource_id: int) -> list[dict[str, Any]]:
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT na.*,
                   n.titulo AS need_title, n.tipo AS need_type
            FROM need_assignments na
            JOIN necesidades n ON na.need_id = n.id
            WHERE na.resource_id = ?
            ORDER BY na.assigned_at DESC
            """,
            (resource_id,),
        )
        return [dict(row) for row in cur.fetchall()]


def get_active_assignments_for_incident(incident_id: str) -> list[dict[str, Any]]:
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT na.*,
                   n.titulo AS need_title, n.tipo AS need_type, n.prioridad AS need_priority,
                   r.name AS resource_name, r.type AS resource_type,
                   r.organization_id AS resource_org_id
            FROM need_assignments na
            JOIN necesidades n ON na.need_id = n.id
            JOIN resources r ON na.resource_id = r.id
            WHERE n.incident_id = ? AND na.status IN ('asignado', 'en_curso')
            ORDER BY na.assigned_at DESC
            """,
            (incident_id,),
        )
        return [dict(row) for row in cur.fetchall()]
