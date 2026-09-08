"""Módulo de Asignaciones — Gestión operacional de asignación de recursos a necesidades.

Flujo:
    need (abierta) + resource (disponible) -> assignment (asignado)
    -> en_curso -> completado | cancelado
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class AssignmentStatus(str, Enum):
    ASIGNADO = "asignado"
    EN_CURSO = "en_curso"
    COMPLETADO = "completado"
    CANCELADO = "cancelado"


# Transiciones válidas de estado
ASSIGNMENT_TRANSITIONS = {
    AssignmentStatus.ASIGNADO: {AssignmentStatus.EN_CURSO, AssignmentStatus.CANCELADO},
    AssignmentStatus.EN_CURSO: {AssignmentStatus.COMPLETADO, AssignmentStatus.CANCELADO},
    AssignmentStatus.COMPLETADO: set(),
    AssignmentStatus.CANCELADO: set(),
}


class AssignmentCreate(BaseModel):
    need_id: int = Field(..., gt=0)
    resource_id: int = Field(..., gt=0)
    quantity_assigned: int = Field(default=1, ge=1, le=999)
    assigned_by: int | None = Field(None, gt=0)
    notes: str | None = Field(None, max_length=500)


class AssignmentResponse(BaseModel):
    id: int
    need_id: int
    resource_id: int
    quantity_assigned: int
    assigned_by: int | None
    assigned_at: str
    status: str
    notes: str | None


class AssignmentUpdate(BaseModel):
    status: AssignmentStatus | None = None
    notes: str | None = Field(None, max_length=500)
