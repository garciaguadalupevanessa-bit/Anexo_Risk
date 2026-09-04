"""Esquemas del módulo de incendios (NASA FIRMS).

Devuelve detecciones satelitales de incendios activos en España.
No se persisten: se cachean en memoria con TTL corto.
"""
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class FireDetection(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: str = Field(description="ID FIRMS: satélite + fecha + lat/lon", max_length=100)
    satellite: str = Field(default="VIIRS", description="Satélite (VIIRS, MODIS)", max_length=20)
    latitud: float = Field(ge=-90, le=90, alias="lat", allow_inf_nan=False)
    longitud: float = Field(ge=-180, le=180, alias="lon", allow_inf_nan=False)
    brillo: float = Field(default=0, alias="brightness", description="Temperatura de brillo en Kelvin")
    confianza: str = Field(default="nominal", alias="confidence", description="low, nominal, high", max_length=20)
    fecha: str = Field(default="", description="Fecha de detección", max_length=30)
    pais: str = Field(default="España", alias="country", max_length=100)


class FireResponse(BaseModel):
    total: int = 0
    detecciones: list[FireDetection] = []
    fuente: str = "NASA FIRMS"
    cached_at: Optional[str] = None
    error: Optional[str] = None
