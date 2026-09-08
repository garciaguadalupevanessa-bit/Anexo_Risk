"""Pydantic schemas for Timeline Events."""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TimelineEventType(str, Enum):
    detected = "detected"
    evaluated = "evaluated"
    risk_updated = "risk_updated"
    need_created = "need_created"
    resource_assigned = "resource_assigned"
    in_transit = "in_transit"
    delivered = "delivered"
    resolved = "resolved"
    escalated = "escalated"
    outcome_recorded = "outcome_recorded"


class TimelineEventCreate(BaseModel):
    incident_id: int
    need_id: Optional[int] = None
    resource_id: Optional[int] = None
    assignment_id: Optional[int] = None
    event_type: TimelineEventType
    description: str = Field(..., min_length=1, max_length=1000)
    actor: Optional[str] = Field(None, max_length=100)
    priority_score: Optional[float] = None
    severity: Optional[str] = None
    status_snapshot: Optional[str] = None
    metadata: Optional[dict] = None


class TimelineEventResponse(BaseModel):
    id: int
    created_at: str
    incident_id: int
    need_id: Optional[int]
    resource_id: Optional[int]
    assignment_id: Optional[int]
    event_type: str
    description: str
    actor: Optional[str]
    priority_score: Optional[float]
    severity: Optional[str]
    status_snapshot: Optional[str]
    metadata: Optional[dict]
