"""Source Registry Pydantic schemas."""
from pydantic import BaseModel, Field
from typing import Optional, Any, List
from enum import Enum


class SourceScope(str, Enum):
    global_ = "global"
    country = "country"
    regional = "regional"
    local = "local"


class SourceStatus(str, Enum):
    active = "active"
    degraded = "degraded"
    unavailable = "unavailable"
    disabled = "disabled"


class SourceCreate(BaseModel):
    id: str = Field(..., min_length=1, max_length=50, examples=["usgs"])
    name: str = Field(..., min_length=1, max_length=200, examples=["USGS Earthquakes"])
    scope: SourceScope = SourceScope.global_
    source_type: str = Field("api", max_length=50)
    data_types: List[str] = Field(default_factory=list)
    supports_point: bool = False
    supports_bbox: bool = False
    supports_region: bool = False
    update_interval_seconds: int = Field(300, gt=0)
    authentication: str = Field("none", max_length=50)
    license: Optional[str] = None
    status: SourceStatus = SourceStatus.active
    cache_ttl_seconds: int = Field(300, gt=0)
    endpoint_url: Optional[str] = None
    metadata: Optional[Any] = None


class SourceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    scope: Optional[SourceScope] = None
    source_type: Optional[str] = Field(None, max_length=50)
    data_types: Optional[List[str]] = None
    supports_point: Optional[bool] = None
    supports_bbox: Optional[bool] = None
    supports_region: Optional[bool] = None
    update_interval_seconds: Optional[int] = Field(None, gt=0)
    authentication: Optional[str] = Field(None, max_length=50)
    license: Optional[str] = None
    status: Optional[SourceStatus] = None
    cache_ttl_seconds: Optional[int] = Field(None, gt=0)
    endpoint_url: Optional[str] = None
    metadata: Optional[Any] = None


class SourceResponse(BaseModel):
    id: str
    name: str
    scope: str = "global"
    source_type: str = "api"
    data_types: List[str] = Field(default_factory=list)
    supports_point: bool = False
    supports_bbox: bool = False
    supports_region: bool = False
    update_interval_seconds: int = 300
    authentication: str = "none"
    license: Optional[str] = None
    status: str = "active"
    last_successful_fetch: Optional[str] = None
    last_failure: Optional[str] = None
    last_error: Optional[str] = None
    latency_ms: Optional[float] = None
    freshness_seconds: Optional[float] = None
    cache_ttl_seconds: int = 300
    endpoint_url: Optional[str] = None
    metadata: Optional[Any] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class SourceHealthResponse(BaseModel):
    id: str
    name: str
    scope: str
    status: str
    last_successful_fetch: Optional[str] = None
    last_failure: Optional[str] = None
    latency_ms: Optional[float] = None
