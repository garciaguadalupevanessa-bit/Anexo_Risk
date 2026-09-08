"""Normalized Events Pydantic schemas."""
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, List
from enum import Enum


class NormalizedEventType(str, Enum):
    earthquake = "earthquake"
    fire = "fire"
    flood = "flood"
    cyclone = "cyclone"
    volcano = "volcano"
    weather = "weather"
    alert = "alert"
    hotspot = "hotspot"
    risk = "risk"
    other = "other"


class NormalizedEventCreate(BaseModel):
    id: Optional[str] = Field(None, max_length=50)
    external_id: Optional[str] = None
    entity_type: NormalizedEventType
    source: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=500)
    description: str = ""
    timestamp: Optional[str] = None
    updated_at: Optional[str] = None
    severity: Optional[str] = None
    severity_float: Optional[float] = Field(None, ge=0, le=1)
    lat: Optional[float] = Field(None, ge=-90, le=90)
    lon: Optional[float] = Field(None, ge=-180, le=180)
    geometry: Optional[Dict[str, Any]] = None
    country: Optional[str] = None
    region: Optional[str] = None
    status: str = "active"
    is_active: bool = True
    h3_index: Optional[str] = None
    magnitude: Optional[float] = None
    depth: Optional[float] = None
    confidence: Optional[float] = Field(None, ge=0, le=1)
    raw_metadata: Optional[Dict[str, Any]] = None
    provenance: Optional[Dict[str, Any]] = None


class NormalizedEventResponse(BaseModel):
    id: str
    external_id: Optional[str] = None
    entity_type: str
    source: str
    title: str
    description: str = ""
    timestamp: Optional[str] = None
    updated_at: Optional[str] = None
    severity: Optional[str] = None
    severity_float: Optional[float] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    geometry: Optional[Dict[str, Any]] = None
    country: Optional[str] = None
    region: Optional[str] = None
    status: str = "active"
    is_active: bool = True
    h3_index: Optional[str] = None
    magnitude: Optional[float] = None
    depth: Optional[float] = None
    confidence: Optional[float] = None
    raw_metadata: Optional[Dict[str, Any]] = None
    provenance: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None


class EventBatchCreate(BaseModel):
    events: List[NormalizedEventCreate]


class EventBatchResponse(BaseModel):
    stored: int
    total: int
