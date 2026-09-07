"""Módulo de Organizaciones — Modelo de producto para Anexo Risk.

Gestiona organizaciones (municipios, protección civil, etc.)
y usuarios operacionales con roles.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    type: str = Field(..., pattern=r"^(municipio|proteccion_civil|112|bomberos|policia|ong|hospital|organismo_autonomico|otro)$")
    region: str | None = Field(None, max_length=200)


class OrganizationResponse(BaseModel):
    id: int
    name: str
    type: str
    region: str | None
    active: bool
    created_at: str


class OperationalUserCreate(BaseModel):
    organization_id: int
    username: str = Field(..., min_length=3, max_length=50)
    display_name: str = Field(..., min_length=1, max_length=200)
    role: str = Field(..., pattern=r"^(operador|coordinador_recursos|analista|administrador)$")


class OperationalUserResponse(BaseModel):
    id: int
    organization_id: int
    username: str
    display_name: str
    role: str
    active: bool
    created_at: str
