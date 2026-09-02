from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class DonationType(str, Enum):
    RESOURCES = "recursos"
    SERVICES = "servicios"
    TIME = "tiempo"
    # Opciones heredadas por compatibilidad
    OFFERED = "ofrecida"
    REQUESTED = "solicitada"


class DonationStatus(str, Enum):
    ACTIVE = "activa"
    DELIVERED = "entregada"


class DonationResource(str, Enum):
    WATER = "Agua"
    FOOD = "Comida"
    BLANKETS = "Mantas"
    CHILDREN_CLOTHING = "Ropa infantil"
    ADULT_CLOTHING = "Ropa de adultos"
    HYGIENE_PRODUCTS = "Productos de higiene"
    TEMPORARY_SHELTER = "Alojamiento temporal"
    FUEL_OR_BATTERIES = "Combustible y/o baterías"
    COMMUNICATION_SERVICES = "Servicios de comunicación"
    MEDICATIONS = "Medicamentos"
    FIRST_AID_SUPPLIES = "Material de primeros auxilios"
    BABY_ITEMS = "Artículos para bebés"
    TOOLS = "Herramientas"
    TRANSPORT = "Transporte"
    LOGISTIC_SUPPORT = "Apoyo logistico"
    BEVERAGES = "Bebidas"
    OTHER = "Otros"


class DonationBase(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    donation_type: DonationType = Field(alias="tipo")
    resource: DonationResource = Field(alias="recurso")
    quantity: str = Field(default="", max_length=100, alias="cantidad")
    description: str = Field(default="", max_length=1000, alias="descripcion")
    contact: str = Field(min_length=3, max_length=200, alias="contacto")
    dni: Optional[str] = Field(default=None, max_length=20, alias="dni")

    @field_validator("contact", "dni", mode="before")
    @classmethod
    def normalize_text(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @model_validator(mode="after")
    def validate_dni_for_time_type(self) -> "DonationBase":
        if self.donation_type == DonationType.TIME:
            if not self.dni or not self.dni.strip():
                raise ValueError("El DNI es obligatorio cuando el tipo de ayuda es 'tiempo'.")
        return self


class DonationCreate(DonationBase):
    latitud: Optional[float] = Field(default=None, alias="latitud")
    longitud: Optional[float] = Field(default=None, alias="longitud")
    necesidad_id: Optional[int] = Field(default=None, alias="necesidad_id")


class DonationStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    status: DonationStatus = Field(alias="estado")


class DonationResponse(DonationBase):
    id: int = Field(gt=0)
    status: DonationStatus = Field(alias="estado")
    created_at: datetime = Field(alias="creado_en")
    latitud: float | None = Field(default=None, ge=-90, le=90)
    longitud: float | None = Field(default=None, ge=-180, le=180)
