"""Módulo de Recursos — Gestión operacional de recursos para emergencias."""
from __future__ import annotations

from pydantic import BaseModel, Field


class ResourceCreate(BaseModel):
    organization_id: int
    type: str = Field(..., pattern=r"^(vehiculo|ambulancia|bombero|equipo_rescate|suministros|personal|refugio|generador|comunicaciones|otro)$")
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    quantity: int = Field(default=1, ge=1)
    latitud: float | None = Field(None, ge=-90, le=90, allow_inf_nan=False)
    longitud: float | None = Field(None, ge=-180, le=180, allow_inf_nan=False)


class ResourceResponse(BaseModel):
    id: int
    organization_id: int
    type: str
    name: str
    description: str | None
    quantity: int
    available_quantity: int
    latitud: float | None
    longitud: float | None
    status: str
    created_at: str
    updated_at: str


class ResourceUpdate(BaseModel):
    available_quantity: int | None = None
    status: str | None = Field(None, pattern=r"^(disponible|asignado|en_mantenimiento|retirado)$")
    latitud: float | None = Field(None, ge=-90, le=90, allow_inf_nan=False)
    longitud: float | None = Field(None, ge=-180, le=180, allow_inf_nan=False)
