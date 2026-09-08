"""Rutas de Asignaciones — API para gestión de asignación de recursos a necesidades.

Endpoints:
- POST /api/assignments — Crear asignación (valida reglas de negocio)
- GET /api/assignments — Listar (filtro: need_id, resource_id, status)
- GET /api/assignments/{id} — Detalle de asignación
- PATCH /api/assignments/{id} — Cambiar estado (transiciones válidas)
- GET /api/assignments/need/{need_id} — Resumen de asignaciones de una necesidad
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from modules.asignaciones.models import (
    AssignmentValidationError,
    InsufficientQuantityError,
    get_assignment,
    list_assignments,
)
from modules.asignaciones.schemas import AssignmentCreate, AssignmentUpdate
from modules.asignaciones.services import (
    assign_resource_to_need,
    get_assignment_summary,
    transition_assignment_status,
)

router = APIRouter(prefix="/api/assignments", tags=["assignments"])


@router.post("", status_code=201)
def create_assignment_endpoint(assignment: AssignmentCreate):
    """Crea una asignación de recurso a necesidad.

    Valida:
    - Necesidad existe y está abierta
    - Recurso existe y está disponible
    - quantity_assigned <= available_quantity
    - Decrementa disponibilidad del recurso
    - Actualiza covered_quantity de la necesidad
    - Si covered >= quantity, cierra la necesidad
    """
    try:
        result = assign_resource_to_need(
            need_id=assignment.need_id,
            resource_id=assignment.resource_id,
            quantity_assigned=assignment.quantity_assigned,
            assigned_by=assignment.assigned_by,
            notes=assignment.notes,
        )
        return {
            "ok": True,
            "message": "Asignación creada correctamente",
            "assignment": result,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InsufficientQuantityError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except AssignmentValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("")
def list_assignments_endpoint(
    need_id: int | None = None,
    resource_id: int | None = None,
    status: str | None = None,
):
    """Lista asignaciones con filtros opcionales."""
    results = list_assignments(need_id=need_id, resource_id=resource_id, status=status)
    return {"ok": True, "count": len(results), "assignments": results}


@router.get("/need/{need_id}")
def get_assignment_summary_endpoint(need_id: int):
    """Retorna el resumen de asignaciones de una necesidad."""
    summary = get_assignment_summary(need_id)
    return {"ok": True, "summary": summary}


@router.get("/{assignment_id}")
def get_assignment_endpoint(assignment_id: int):
    """Detalle de una asignación."""
    assignment = get_assignment(assignment_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail=f"Asignación {assignment_id} no encontrada")
    return {"ok": True, "assignment": assignment}


@router.patch("/{assignment_id}")
def update_assignment_endpoint(assignment_id: int, update: AssignmentUpdate):
    """Cambia el estado de una asignación.

    Transiciones válidas:
    - asignado -> en_curso
    - en_curso -> completado
    - asignado/en_curso -> cancelado
    """
    try:
        result = transition_assignment_status(
            assignment_id=assignment_id,
            new_status=update.status.value,
            notes=update.notes,
        )
        if result is None:
            raise HTTPException(status_code=404, detail=f"Asignación {assignment_id} no encontrada")
        return {"ok": True, "assignment": result}
    except AssignmentValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
