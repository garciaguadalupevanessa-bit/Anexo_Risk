"""Network Links Pydantic schemas."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class LinkType(str, Enum):
    road = "road"
    corridor = "corridor"
    route = "route"
    bridge = "bridge"
    tunnel = "tunnel"
    evacuation = "evacuation"


class LinkStatus(str, Enum):
    open = "open"
    blocked = "blocked"
    restricted = "restricted"
    closed = "closed"


class LinkCreate(BaseModel):
    id: Optional[str] = Field(None, max_length=50)
    external_id: Optional[str] = None
    link_type: LinkType
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = ""
    start_node_id: Optional[str] = None
    end_node_id: Optional[str] = None
    start_lat: Optional[float] = Field(None, ge=-90, le=90)
    start_lon: Optional[float] = Field(None, ge=-180, le=180)
    end_lat: Optional[float] = Field(None, ge=-90, le=90)
    end_lon: Optional[float] = Field(None, ge=-180, le=180)
    distance_km: Optional[float] = Field(None, ge=0)
    estimated_time_min: Optional[float] = Field(None, ge=0)
    status: LinkStatus = LinkStatus.open
    capacity: Optional[int] = Field(None, ge=0)
    restrictions: Optional[List[str]] = None
    source: str = "manual"
    metadata: Optional[Dict[str, Any]] = None


class LinkUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    status: Optional[LinkStatus] = None
    distance_km: Optional[float] = Field(None, ge=0)
    estimated_time_min: Optional[float] = Field(None, ge=0)
    capacity: Optional[int] = Field(None, ge=0)
    restrictions: Optional[List[str]] = None


class LinkResponse(BaseModel):
    id: str
    external_id: Optional[str] = None
    link_type: str
    name: str
    description: Optional[str] = ""
    start_node_id: Optional[str] = None
    end_node_id: Optional[str] = None
    start_lat: Optional[float] = None
    start_lon: Optional[float] = None
    end_lat: Optional[float] = None
    end_lon: Optional[float] = None
    h3_start: Optional[str] = None
    h3_end: Optional[str] = None
    distance_km: Optional[float] = None
    estimated_time_min: Optional[float] = None
    status: str = "open"
    capacity: Optional[int] = None
    restrictions: Optional[List[str]] = None
    source: str = "manual"
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
