"""Operational Nodes Pydantic schemas."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class NodeType(str, Enum):
    hospital = "hospital"
    fire_station = "fire_station"
    shelter = "shelter"
    logistics_base = "logistics_base"
    warehouse = "warehouse"
    command_post = "command_post"


class NodeCreate(BaseModel):
    id: Optional[str] = Field(None, max_length=50)
    external_id: Optional[str] = None
    node_type: NodeType
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = ""
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    h3_index: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    country_code: Optional[str] = None
    capacity: Optional[int] = Field(None, ge=0)
    current_occupancy: Optional[int] = Field(0, ge=0)
    capabilities: Optional[List[str]] = None
    status: str = "active"
    is_active: bool = True
    source: str = "manual"
    metadata: Optional[Dict[str, Any]] = None


class NodeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    lat: Optional[float] = Field(None, ge=-90, le=90)
    lon: Optional[float] = Field(None, ge=-180, le=180)
    capacity: Optional[int] = Field(None, ge=0)
    current_occupancy: Optional[int] = Field(None, ge=0)
    capabilities: Optional[List[str]] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None


class NodeResponse(BaseModel):
    id: str
    external_id: Optional[str] = None
    node_type: str
    name: str
    description: Optional[str] = ""
    lat: float
    lon: float
    h3_index: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    country_code: Optional[str] = None
    capacity: Optional[int] = None
    current_occupancy: Optional[int] = None
    capabilities: Optional[List[str]] = None
    status: str = "active"
    is_active: bool = True
    source: str = "manual"
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
