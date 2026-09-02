"""Esquemas del módulo de incendios (NASA FIRMS).

Devuelve detecciones satelitales de incendios activos en España.
No se persisten: se cachean en memoria con TTL corto.
"""
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class FireDetection(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="ID FIRMS: satélite + fecha + lat/lon")
    satellite: str = Field(default="VIIRS", description="Satélite (VIIRS, MODIS)")
    latitud: float = Field(ge=-90, le=90, alias="lat")
    longitud: float = Field(ge=-180, le=180, alias="lon")
    brillo: float = Field(default=0, description="Temperatura de brillo en Kelvin")
    confianza: str = Field(default="nominal", description="low, nominal, high")
    fecha: str = Field(default="", description="Fecha de detección")
    pais: str = Field(default="España", alias="country")


class FireResponse(BaseModel):
    total: int
    detecciones: list[FireDetection]
    fuente: str = "NASA FIRMS"
    cached_at: Optional[str] = None
