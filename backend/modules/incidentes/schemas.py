"""Pydantic schemas for Incidents."""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class EventType(str, Enum):
    alerta = "alerta"
    incendio = "incendio"
    terremoto = "terremoto"
    ciclon = "ciclon"
    volcan = "volcan"
    inundacion = "inundacion"
    otro = "otro"


class IncidentSeverity(str, Enum):
    verde = "verde"
    amarilla = "amarilla"
    naranja = "naranja"
    roja = "roja"


class IncidentStatus(str, Enum):
    detectado = "detectado"
    evaluado = "evaluado"
    en_respuesta = "en_respuesta"
    resuelto = "resuelto"
    cancelado = "cancelado"


class IncidentCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    event_type: EventType = EventType.alerta
    source: str = Field("manual", max_length=50)
    external_id: Optional[str] = Field(None, max_length=200)
    severity: IncidentSeverity = IncidentSeverity.amarilla
    magnitude: Optional[float] = Field(None, ge=0)
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    direccion: Optional[str] = Field(None, max_length=500)
    metadata: Optional[dict] = None


class IncidentStatusUpdate(BaseModel):
    status: IncidentStatus


class IncidentResponse(BaseModel):
    id: int
    created_at: str
    updated_at: str
    title: str
    description: Optional[str]
    event_type: str
    source: str
    external_id: Optional[str]
    severity: str
    magnitude: Optional[float]
    lat: float
    lon: float
    h3_index: Optional[str]
    direccion: Optional[str]
    status: str
    is_active: int
    priority_score: Optional[float]
    exposure_score: Optional[float]
    metadata: Optional[dict]
