"""Servicio de cálculo de exposición e impacto.

Calcula la exposición de población, infraestructura y recursos
a eventos geográficos usando análisis espacial.
"""
from __future__ import annotations

from geodata.services.spatial import find_nearby, haversine_distance


def calculate_exposure(
    event: dict,
    needs: list[dict] | None = None,
    resources: list[dict] | None = None,
    radius_km: float = 50.0,
) -> dict:
    """Calcula la exposición de un evento a su alrededor.

    Parameters
    ----------
    event : dict
        Evento con latitud, longitud, severity, magnitude.
    needs : list[dict] or None
        Necesidades abiertas para evaluar afectación.
    resources : list[dict] or None
        Recursos disponibles para evaluar cobertura.
    radius_km : float
        Radio de búsqueda en km.

    Returns
    -------
    dict
        exposición calculada con:
        - needs_affected: necesidades dentro del radio
        - resources_nearby: recursos cercanos
        - min_distance_resource: distancia al recurso más cercano
        - exposure_score: score 0-1 de exposición
        - factors: factores que contribuyen al score
    """
    lat = event.get("latitud") or event.get("lat")
    lon = event.get("longitud") or event.get("lon")
    severity = event.get("severity", 0)

    if lat is None or lon is None:
        return _empty_exposure()

    nearby_needs = find_nearby(lat, lon, needs or [], radius_km) if needs else []
    nearby_resources = find_nearby(lat, lon, resources or [], radius_km) if resources else []

    min_dist_resource = None
    if nearby_resources:
        min_dist_resource = nearby_resources[0].get("_distance_km")

    factors = []
    score = 0.0

    if severity >= 0.8:
        score += 0.3
        factors.append("Severidad alta del evento")
    elif severity >= 0.5:
        score += 0.2
        factors.append("Severidad moderada del evento")
    else:
        score += 0.1

    if len(nearby_needs) >= 5:
        score += 0.3
        factors.append(f"{len(nearby_needs)} necesidades en zona")
    elif len(nearby_needs) >= 2:
        score += 0.2
        factors.append(f"{len(nearby_needs)} necesidades cercanas")
    elif len(nearby_needs) >= 1:
        score += 0.1

    if min_dist_resource is not None and min_dist_resource > radius_km * 0.8:
        score += 0.2
        factors.append(f"Recursos lejanos ({min_dist_resource:.0f} km)")
    elif min_dist_resource is None:
        score += 0.25
        factors.append("Sin recursos disponibles en zona")
    else:
        score += 0.05

    if len(nearby_resources) == 0:
        score += 0.15
        factors.append("Cobertura de recursos nula")

    score = min(score, 1.0)

    return {
        "needs_affected": len(nearby_needs),
        "resources_nearby": len(nearby_resources),
        "min_distance_resource": min_dist_resource,
        "exposure_score": round(score, 3),
        "factors": factors,
    }


def calculate_impact(event: dict, exposure: dict) -> dict:
    """Calcula impacto combinando exposición y características del evento.

    Returns
    -------
    dict
        impacto con priority_score, priority_level, factors.
    """
    severity = event.get("severity", 0)
    magnitude = event.get("magnitude", 0)
    exposure_score = exposure.get("exposure_score", 0)

    priority_score = (severity * 0.4 + exposure_score * 0.4 + min(magnitude / 10, 1.0) * 0.2) * 100
    priority_score = min(round(priority_score, 1), 100)

    if priority_score >= 80:
        priority_level = "critico"
    elif priority_score >= 60:
        priority_level = "alto"
    elif priority_score >= 40:
        priority_level = "medio"
    elif priority_score >= 20:
        priority_level = "bajo"
    else:
        priority_level = "informativo"

    factors = list(exposure.get("factors", []))
    if severity >= 0.8:
        factors.insert(0, "Severidad crítica")
    if magnitude >= 6.0:
        factors.append(f"Magnitud elevada ({magnitude:.1f})")

    return {
        "priority_score": priority_score,
        "priority_level": priority_level,
        "factors": factors,
    }


def _empty_exposure() -> dict:
    return {
        "needs_affected": 0,
        "resources_nearby": 0,
        "min_distance_resource": None,
        "exposure_score": 0.0,
        "factors": ["Sin coordenadas disponibles"],
    }
