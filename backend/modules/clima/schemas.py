"""Esquemas del módulo de clima.

Combina AEMET (oficial España) con Open-Meteo como fallback.
"""
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class WeatherAlert(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    tipo: str = Field(description="lluvia, viento, calor, nieve, tormenta, etc.")
    nivel: str = Field(description="verde, amarillo, naranja, rojo")
    titulo: str
    descripcion: str = ""
    region: str = "España"
    fecha: str = ""
    fuente: str = Field(description="AEMET u Open-Meteo")


class WeatherResponse(BaseModel):
    total: int
    alertas: list[WeatherAlert]
    fuente: str
    cached_at: Optional[str] = None
    fallback_activado: bool = False
