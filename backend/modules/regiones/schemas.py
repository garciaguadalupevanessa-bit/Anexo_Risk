"""Region/AOI Pydantic schemas."""
from pydantic import BaseModel, Field
from typing import Optional, Any
from enum import Enum


class RegionLevel(str, Enum):
    world = "world"
    country = "country"
    region = "region"
    province = "province"
    municipality = "municipality"
    locality = "locality"
    point = "point"
    custom = "custom"


class RegionCreate(BaseModel):
    id: str = Field(..., min_length=1, max_length=50, examples=["ES-MD"])
    name: str = Field(..., min_length=1, max_length=200, examples=["Comunidad de Madrid"])
    level: RegionLevel = RegionLevel.municipality
    parent_id: Optional[str] = None
    country_code: Optional[str] = Field(None, max_length=2, examples=["ES"])
    h3_resolution: int = Field(3, ge=0, le=15)
    geometry_type: Optional[str] = None
    geometry: Optional[Any] = None
    bbox_min_lat: Optional[float] = Field(None, ge=-90, le=90)
    bbox_min_lon: Optional[float] = Field(None, ge=-180, le=180)
    bbox_max_lat: Optional[float] = Field(None, ge=-90, le=90)
    bbox_max_lon: Optional[float] = Field(None, ge=-180, le=180)
    center_lat: Optional[float] = Field(None, ge=-90, le=90)
    center_lon: Optional[float] = Field(None, ge=-180, le=180)
    radius_km: Optional[float] = Field(None, gt=0)
    is_active: bool = True
    source: str = "manual"
    metadata: Optional[Any] = None


class RegionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    level: Optional[RegionLevel] = None
    parent_id: Optional[str] = None
    country_code: Optional[str] = Field(None, max_length=2)
    h3_resolution: Optional[int] = Field(None, ge=0, le=15)
    geometry_type: Optional[str] = None
    geometry: Optional[Any] = None
    bbox_min_lat: Optional[float] = Field(None, ge=-90, le=90)
    bbox_min_lon: Optional[float] = Field(None, ge=-180, le=180)
    bbox_max_lat: Optional[float] = Field(None, ge=-90, le=90)
    bbox_max_lon: Optional[float] = Field(None, ge=-180, le=180)
    center_lat: Optional[float] = Field(None, ge=-90, le=90)
    center_lon: Optional[float] = Field(None, ge=-180, le=180)
    radius_km: Optional[float] = Field(None, gt=0)
    is_active: Optional[bool] = None
    source: Optional[str] = None
    metadata: Optional[Any] = None


class RegionResponse(BaseModel):
    id: str
    name: str
    level: str
    parent_id: Optional[str] = None
    country_code: Optional[str] = None
    h3_resolution: int = 3
    geometry_type: Optional[str] = None
    geometry: Optional[Any] = None
    bbox_min_lat: Optional[float] = None
    bbox_min_lon: Optional[float] = None
    bbox_max_lat: Optional[float] = None
    bbox_max_lon: Optional[float] = None
    center_lat: Optional[float] = None
    center_lon: Optional[float] = None
    radius_km: Optional[float] = None
    is_active: bool = True
    source: str = "manual"
    metadata: Optional[Any] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class RegionSourceCreate(BaseModel):
    source_id: str = Field(..., min_length=1, max_length=50)
    is_enabled: bool = True
    priority: int = 0
    config: Optional[Any] = None


class RegionSourceResponse(BaseModel):
    id: Optional[int] = None
    region_id: str
    source_id: str
    is_enabled: bool = True
    priority: int = 0
    config: Optional[Any] = None
    created_at: Optional[str] = None
