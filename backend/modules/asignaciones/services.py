"""Servicio de Asignaciones — Lógica de negocio para asignación de recursos a necesidades.

Reglas:
1. quantity_assigned <= resource.available_quantity
2. need must be OPEN (abierta)
3. resource must be AVAILABLE (disponible)
4. status transitions: asignado -> en_curso -> completado | cancelado
5. On complete: update covered_quantity, potentially close need
6. On cancel: restore available_quantity
"""
from __future__ import annotations

from typing import Any

from modules.asignaciones.models import (
    AssignmentValidationError,
    InsufficientQuantityError,
    create_assignment,
    get_assignment,
    get_assignments_for_need,
    list_assignments,
    update_assignment_status,
)
from modules.necesidades import models as need_models
from modules.necesidades.schemas import NeedStatus
from modules.recursos import models as resource_models


ASSIGNMENT_STATUS_TRANSITIONS = {
    "asignado": "en_curso",
    "en_curso": "completado",
}


def assign_resource_to_need(
    need_id: int,
    resource_id: int,
    quantity_assigned: int = 1,
    assigned_by: int | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """Asigna un recurso a una necesidad validando todas las reglas de negocio.

    Raises
    ------
    ValueError
        Si la necesidad o recurso no existe.
    AssignmentValidationError
        Si la necesidad no está abierta o el recurso no está disponible.
    InsufficientQuantityError
        Si no hay suficiente cantidad disponible.
    """
    # 1. Validar necesidad
    need = need_models.get_need(need_id)
    if need is None:
        raise ValueError(f"Necesidad {need_id} no encontrada")
    if need["estado"] != "abierta":
        raise AssignmentValidationError(
            f"La necesidad {need_id} tiene estado '{need['estado']}', "
            "solo se pueden asignar recursos a necesidades abiertas"
        )

    # 2. Validar recurso
    resource = resource_models.get_resource(resource_id)
    if resource is None:
        raise ValueError(f"Recurso {resource_id} no encontrado")
    if resource["status"] != "disponible":
        raise AssignmentValidationError(
            f"El recurso {resource_id} tiene estado '{resource['status']}', "
            "solo se pueden asignar recursos disponibles"
        )

    # 3. Validar cantidad
    if quantity_assigned > resource["available_quantity"]:
        raise InsufficientQuantityError(
            f"Recurso {resource_id} tiene {resource['available_quantity']} "
            f"disponibles, se solicitaron {quantity_assigned}"
        )

    # 4. Crear asignación
    from modules.asignaciones.schemas import AssignmentCreate

    assignment = create_assignment(
        AssignmentCreate(
            need_id=need_id,
            resource_id=resource_id,
            quantity_assigned=quantity_assigned,
            assigned_by=assigned_by,
            notes=notes,
        )
    )

    # 5. Decrementar disponibilidad del recurso
    new_available = resource["available_quantity"] - quantity_assigned
    resource_models.update_resource(
        resource_id,
        available_quantity=new_available,
        status="asignado" if new_available == 0 else resource["status"],
    )

    # 6. Actualizar covered_quantity en la necesidad
    current_covered = need.get("covered_quantity") or 0
    new_covered = current_covered + quantity_assigned
    need_quantity = need.get("quantity") or 0
    with need_models.get_cursor() as cur:
        cur.execute(
            "UPDATE necesidades SET covered_quantity = ?, updated_at = datetime('now') "
            "WHERE id = ?",
            (new_covered, need_id),
        )

        # 7. Si se cubrió toda la cantidad, marcar como cubierta
        if need_quantity > 0 and new_covered >= need_quantity:
            cur.execute(
                "UPDATE necesidades SET estado = 'cubierta', updated_at = datetime('now') "
                "WHERE id = ? AND estado = 'abierta'",
                (need_id,),
            )

    # 8. Enriquecer respuesta con datos de necesidad y recurso
    assignment["need_title"] = need.get("titulo", "")
    assignment["need_type"] = need.get("tipo", "")
    assignment["need_status"] = need.get("estado", "")
    assignment["need_priority"] = need.get("prioridad", "")
    assignment["resource_name"] = resource.get("name", "")
    assignment["resource_type"] = resource.get("type", "")
    assignment["resource_org_id"] = resource.get("organization_id")

    return assignment


def transition_assignment_status(
    assignment_id: int,
    new_status: str,
    notes: str | None = None,
) -> dict[str, Any]:
    """Transiciona el estado de una asignación.

    Reglas:
    - asignado -> en_curso
    - en_curso -> completado (restaura disponibilidad parcial)
    - asignado | en_curso -> cancelado (restaura toda la disponibilidad)

    Raises
    ------
    ValueError
        Si la asignación no existe.
    AssignmentValidationError
        Si la transición no es válida.
    """
    assignment = get_assignment(assignment_id)
    if assignment is None:
        raise ValueError(f"Asignación {assignment_id} no encontrada")

    current_status = assignment["status"]

    # Transiciones válidas
    valid_next = {
        "asignado": {"en_curso", "cancelado"},
        "en_curso": {"completado", "cancelado"},
    }

    if new_status not in valid_next.get(current_status, set()):
        raise AssignmentValidationError(
            f"No se puede transicionar de '{current_status}' a '{new_status}'"
        )

    resource_id = assignment["resource_id"]
    quantity = assignment["quantity_assigned"]
    resource = resource_models.get_resource(resource_id)

    # Completar: restaurar disponibilidad
    if new_status == "completado" and resource:
        new_available = resource["available_quantity"] + quantity
        resource_models.update_resource(
            resource_id,
            available_quantity=new_available,
            status="disponible",
        )

    # Cancelar: restaurar toda la disponibilidad
    if new_status == "cancelado" and resource:
        new_available = resource["available_quantity"] + quantity
        resource_models.update_resource(
            resource_id,
            available_quantity=new_available,
            status="disponible",
        )

    updated = update_assignment_status(assignment_id, new_status)

    if notes:
        with need_models.get_cursor() as cur:
            cur.execute(
                "UPDATE need_assignments SET notes = ? WHERE id = ?",
                (notes, assignment_id),
            )

    return updated


def get_assignment_summary(need_id: int) -> dict[str, Any]:
    """Retorna el resumen de asignaciones de una necesidad."""
    assignments = get_assignments_for_need(need_id)
    total_assigned = sum(a["quantity_assigned"] for a in assignments)
    by_status = {}
    for a in assignments:
        s = a["status"]
        by_status[s] = by_status.get(s, 0) + a["quantity_assigned"]

    return {
        "need_id": need_id,
        "total_assigned": total_assigned,
        "by_status": by_status,
        "assignments_count": len(assignments),
        "assignments": assignments,
    }
