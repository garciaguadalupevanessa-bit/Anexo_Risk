"""Pydantic schemas for Outcome recording."""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class OutcomeCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    incident_id: int
    prediction_source: str = Field("anexo_risk", max_length=50)
    model_version: Optional[str] = None
    predicted_level: Optional[str] = None
    predicted_score: Optional[float] = None
    h3_index: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    needs_open_at_prediction: Optional[int] = None
    resources_available_at_prediction: Optional[int] = None
    metadata: Optional[dict] = None


class OutcomeUpdate(BaseModel):
    incident_closed: bool = False
    needs_created: int = 0
    needs_resolved: int = 0
    resource_gap: int = 0
    response_duration_hours: Optional[float] = None
    escalation_occurred: bool = False
    metadata: Optional[dict] = None


class OutcomeResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    id: int
    created_at: str
    prediction_source: str
    model_version: Optional[str]
    predicted_level: Optional[str]
    predicted_score: Optional[float]
    prediction_time: str
    h3_index: Optional[str]
    lat: Optional[float]
    lon: Optional[float]
    needs_open_at_prediction: Optional[int]
    resources_available_at_prediction: Optional[int]
    incident_id: Optional[str]
    outcome_time: Optional[str]
    incident_closed: Optional[int]
    needs_created: Optional[int]
    needs_resolved: Optional[int]
    resource_gap_at_outcome: Optional[int]
    response_duration_hours: Optional[float]
    escalation_occurred: Optional[int]
    metadata: Optional[dict]


class OutcomeStats(BaseModel):
    total_predictions: int
    with_outcome: int
    incidents_closed: int
    escalations: int
    avg_response_hours: Optional[float]
    avg_resource_gap: Optional[float]
