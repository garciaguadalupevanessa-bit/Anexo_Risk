"""Pydantic schemas for the alerts API module.

Defines enum domain constraints, response data models, and validation contracts
conforming to the GeoRisk standard with full Spanish endpoint compatibility.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class SeverityEnum(str, Enum):
    """Enumeration of valid alert severity levels."""

    RED = "RED"
    ORANGE = "ORANGE"
    GREEN = "GREEN"


class RiskLevelEnum(str, Enum):
    """Enumeration of valid risk levels for GeoRisk alignment."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AlertStatusEnum(str, Enum):
    """Enumeration of valid alert statuses."""

    NORMAL = "normal"
    ACTIVE = "active"
    HIGH_RISK = "high_risk"
    DEACTIVATED = "deactivated"


class EventTypeEnum(str, Enum):
    """Enumeration of standardized disaster event classifications."""

    TERREMOTO = "terremoto"
    CICLON = "ciclon"
    INUNDACION = "inundacion"
    INCENDIO = "incendio"
    VOLCAN = "volcan"
    SEQUIA = "sequia"
    OTRO = "otro"


class AlertCreate(BaseModel):
    """Payload model for manual alert creation."""

    titulo: str = Field(..., alias="title", description="Short descriptive title of the alert")
    descripcion: Optional[str] = Field(default="", alias="description", description="Detailed summary")
    tipo: Optional[EventTypeEnum] = Field(default=EventTypeEnum.OTRO, alias="type", description="Event classification")
    zone: Dict[str, Any] = Field(..., description="GeoJSON Polygon object for spatial coverage")
    nivel_riesgo: Optional[RiskLevelEnum] = Field(default=RiskLevelEnum.LOW, alias="risk_level", description="Initial risk level")
    gestor_token: Optional[str] = Field(default=None, alias="manager_token", description="Authorization token for managers")
    fecha: Optional[datetime] = Field(default=None, alias="date", description="Creation timestamp")

    @model_validator(mode="before")
    @classmethod
    def accept_spanish_or_english_keys(cls, values: Any) -> Any:
        if isinstance(values, dict):
            if "titulo" in values and "title" not in values:
                values["title"] = values["titulo"]
            if "descripcion" in values and "description" not in values:
                values["description"] = values["descripcion"]
            if "tipo" in values and "type" not in values:
                values["type"] = values["tipo"]
            if "nivel_riesgo" in values and "risk_level" not in values:
                values["risk_level"] = values["nivel_riesgo"]
            if "fecha" in values and "date" not in values:
                values["date"] = values["fecha"]
        return values


class AlertResponse(BaseModel):
    """Data model representing a single alert item in API responses."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str = Field(..., description="Unique alert identifier")
    external_id: Optional[str] = Field(default=None, description="External provider identifier (e.g. GDACS_1234)")
    source: str = Field(default="GDACS", description="Data source provider name (GDACS|PROTECCION_CIVIL|MANUAL)")
    tipo: EventTypeEnum = Field(..., alias="tipo", description="Standardized event type classification")
    titulo: str = Field(default="", alias="titulo", description="Short descriptive title of the alert")
    descripcion: str = Field(default="", alias="descripcion", description="Detailed alert summary or description")
    severidad: Optional[SeverityEnum] = Field(default=SeverityEnum.GREEN, alias="severidad", description="GeoRisk severity level tier")
    risk_level: RiskLevelEnum = Field(default=RiskLevelEnum.LOW, description="GeoRisk risk level assessment")
    status: AlertStatusEnum = Field(default=AlertStatusEnum.NORMAL, description="Current operational status")
    is_active: bool = Field(default=True, description="Active status indicator flag")
    zone: Optional[Dict[str, Any]] = Field(default=None, description="GeoJSON Polygon mapping zone")
    pais: Optional[str] = Field(default="", alias="pais", description="Name of affected country")
    lat: Optional[float] = Field(default=None, description="Geographical latitude coordinate")
    lon: Optional[float] = Field(default=None, description="Geographical longitude coordinate")
    fecha: Optional[datetime] = Field(default=None, alias="fecha", description="Publication timestamp in ISO format")
    enlace: Optional[str] = Field(default="", alias="enlace", description="External detailed report URL")

    @model_validator(mode="before")
    @classmethod
    def populate_defaults(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "source" not in data and "fuente" in data:
                data["source"] = data["fuente"]
            if "tipo" not in data and "type" in data:
                data["tipo"] = data["type"]
            if "titulo" not in data and "title" in data:
                data["titulo"] = data["title"]
            if "descripcion" not in data and "description" in data:
                data["descripcion"] = data["description"]
            if "severidad" not in data and "severity" in data:
                data["severidad"] = data["severity"]
            if "pais" not in data and "country" in data:
                data["pais"] = data["country"]
            if "fecha" not in data and "date" in data:
                data["fecha"] = data["date"]
            if "enlace" not in data and "link" in data:
                data["enlace"] = data["link"]

            if "risk_level" not in data and "nivel_riesgo" not in data:
                sev = str(data.get("severidad") or data.get("severity") or "GREEN").upper()
                if sev == "RED":
                    data["risk_level"] = RiskLevelEnum.HIGH
                elif sev == "ORANGE":
                    data["risk_level"] = RiskLevelEnum.MEDIUM
                else:
                    data["risk_level"] = RiskLevelEnum.LOW
        return data