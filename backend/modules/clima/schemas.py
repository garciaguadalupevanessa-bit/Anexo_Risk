"""Esquemas del módulo de clima.

Combina AEMET (oficial España) con Open-Meteo como fallback.
"""
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class WeatherAlert(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(max_length=100)
    tipo: str = Field(description="lluvia, viento, calor, nieve, tormenta, etc.", max_length=50)
    nivel: str = Field(description="verde, amarillo, naranja, rojo", max_length=20)
    titulo: str = Field(max_length=300)
    descripcion: str = Field(default="", max_length=2000)
    region: str = Field(default="España", max_length=200)
    fecha: str = Field(default="", max_length=30)
    fuente: str = Field(description="AEMET u Open-Meteo", max_length=50)


class WeatherResponse(BaseModel):
    total: int = 0
    alertas: list[WeatherAlert] = []
    fuente: str = "Open-Meteo"
    cached_at: Optional[str] = None
    fallback_activado: bool = False
    error: Optional[str] = None
