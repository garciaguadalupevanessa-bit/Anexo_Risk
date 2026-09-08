"""Módulo Centro de Decisión — Conecta todas las capacidades de Anexo Risk.

Proporciona una vista unificada de un incidente con:
- Situación: tipo, severidad, fuente, timestamp, ubicación
- Contexto: fuentes relacionadas, meteorología, eventos cercanos, tendencia
- Impacto: población expuesta, infraestructura, necesidades afectadas, recursos cercanos
- GeoRisk: riesgo científico territorial (cuando GeoRisk Finder está disponible)
- Riesgo: score 0-100, nivel, factores, confianza, source (rules/ml/combined)
- Operación: necesidades abiertas, recursos disponibles, asignaciones, estado
- Explicación: por qué tiene esta prioridad
"""
from __future__ import annotations

from datetime import datetime, timezone

from geodata.adapters.effis_adapter import get_fire_danger_for_point
from geodata.services.exposure import calculate_exposure, calculate_impact
from geodata.services.risk_engine import calculate_risk_score
from geodata.services.spatial import find_nearby, haversine_distance
from geodata.services.h3_resolver import latlon_to_h3
from ml.service import predict_with_explanation
from integrations.georisk_client import get_cell_risk, is_georisk_available, get_circuit_status


def build_decision_context(
    incident: dict,
    all_events: list[dict] | None = None,
    needs: list[dict] | None = None,
    resources: list[dict] | None = None,
    weather: dict | None = None,
) -> dict:
    """Construye el contexto completo de decisión para un incidente.

    Parameters
    ----------
    incident : dict
        Incidente con campos: latitud/lat, longitud/lon, severity, magnitude,
        event_type/title, source, event_time, etc.
    all_events : list[dict] or None
        Todos los eventos conocidos para calcular densidad y tendencia.
    needs : list[dict] or None
        Necesidades abiertas para evaluar afectación.
    resources : list[dict] or None
        Recursos disponibles para evaluar cobertura.
    weather : dict or None
        Datos meteorológicos si disponibles.

    Returns
    -------
    dict
        decision_context con todas las secciones.
    """
    lat = incident.get("latitud") or incident.get("lat")
    lon = incident.get("longitud") or incident.get("lon")
    severity = incident.get("severity", 0)
    magnitude = incident.get("magnitude", 0)
    event_type = incident.get("event_type") or incident.get("tipo", "desconocido")
    title = incident.get("title") or incident.get("titulo", "Sin título")
    source = incident.get("source") or incident.get("fuente", "desconocido")
    event_time = incident.get("event_time") or incident.get("fecha")

    # 1. Situación
    situation = {
        "event_type": event_type,
        "title": title,
        "source": source,
        "severity": severity,
        "magnitude": magnitude,
        "timestamp": event_time,
        "location": {"lat": lat, "lon": lon} if lat and lon else None,
    }

    # 2. Contexto
    nearby_events = []
    event_density = 0.0
    trend = 0.0
    if all_events and lat and lon:
        nearby_events = find_nearby(lat, lon, all_events, radius_km=100)
        nearby_events = [e for e in nearby_events if e.get("external_id") != incident.get("external_id")]
        event_density = min(len(nearby_events) / 10, 1.0)
        if len(nearby_events) > 0:
            recent = sum(1 for e in nearby_events if _is_recent(e.get("event_time"), hours=24))
            trend = (recent / len(nearby_events)) * 2 - 1 if nearby_events else 0

    effis = None
    if lat and lon:
        try:
            effis = get_fire_danger_for_point(lat, lon)
        except Exception:
            effis = None

    context = {
        "nearby_events_count": len(nearby_events),
        "event_density": round(event_density, 3),
        "trend": round(trend, 3),
        "weather": weather,
        "effis": effis,
    }

    # 3. Impacto
    exposure = calculate_exposure(
        incident,
        needs=needs or [],
        resources=resources or [],
        radius_km=50,
    )
    impact = calculate_impact(incident, exposure)

    # 4. ML Prediction (experimental)
    ml_prediction = predict_with_explanation(
        event=incident,
        all_events=all_events,
        needs=needs,
        resources=resources,
    )

    # 5. GeoRisk Scientific Risk (optional — from GeoRisk Finder)
    georisk = None
    h3_index = None
    if lat and lon:
        h3_index = latlon_to_h3(lat, lon)
        if h3_index and is_georisk_available():
            try:
                georisk_data = get_cell_risk(h3_index)
                if georisk_data:
                    georisk = {
                        "status": "ok",
                        "h3_index": h3_index,
                        "risk_score": georisk_data.get("risk_score", 0),
                        "risk_level": georisk_data.get("risk_level", "unknown"),
                        "model_version": georisk_data.get("model_version", ""),
                        "cluster_id": georisk_data.get("cluster_id"),
                        "cluster_label": georisk_data.get("cluster_label", ""),
                        "features": georisk_data.get("features", {}),
                        "explanation": georisk_data.get("explanation", ""),
                        "confidence": georisk_data.get("confidence", 0),
                        "source": "georisk",
                    }
            except Exception:
                georisk = {"status": "error", "message": "Error consultando GeoRisk", "source": "georisk"}
        elif h3_index:
            georisk = {
                "status": "unavailable",
                "h3_index": h3_index,
                "message": "GeoRisk no disponible — usando riesgo operacional local",
                "source": "georisk",
                "circuit": get_circuit_status(),
            }

    # 6. Riesgo (rules + ML si disponible)
    risk = calculate_risk_score(
        severity=severity,
        exposure=exposure.get("exposure_score", 0),
        weather=_weather_to_score(weather) if weather else 0,
        event_density=event_density,
        needs_open=exposure.get("needs_affected", 0),
        trend=trend,
        ml_prediction=ml_prediction,
    )

    # 7. Operación
    nearby_needs = find_nearby(lat, lon, needs or [], radius_km=50) if lat and lon else []
    nearby_resources = find_nearby(lat, lon, resources or [], radius_km=50) if lat and lon else []

    # Asignaciones activas para el incidente
    active_assignments = []
    incident_id = incident.get("incident_id") or incident.get("external_id")
    if incident_id:
        try:
            from modules.asignaciones.models import get_active_assignments_for_incident
            active_assignments = get_active_assignments_for_incident(incident_id)
        except Exception:
            active_assignments = []

    operation = {
        "needs_open": len([n for n in nearby_needs if n.get("estado") == "abierta"]),
        "needs_total": len(nearby_needs),
        "resources_available": len([r for r in nearby_resources if r.get("status") == "disponible"]),
        "resources_total": len(nearby_resources),
        "min_distance_resource": exposure.get("min_distance_resource"),
        "active_assignments": len(active_assignments),
        "assignments": active_assignments,
    }

    # 8. Explicación
    explanation = _build_explanation(situation, context, exposure, risk, operation, georisk, h3_index)

    return {
        "situation": situation,
        "context": context,
        "impact": {
            "exposure_score": exposure.get("exposure_score", 0),
            "needs_affected": exposure.get("needs_affected", 0),
            "resources_nearby": exposure.get("resources_nearby", 0),
            "factors": exposure.get("factors", []),
        },
        "georisk": georisk,
        "h3_index": h3_index,
        "risk": risk,
        "operation": operation,
        "explanation": explanation,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def _build_explanation(
    situation: dict,
    context: dict,
    exposure: dict,
    risk: dict,
    operation: dict,
    georisk: dict | None = None,
    h3_index: str | None = None,
) -> dict:
    """Construye la explicación del por qué de la prioridad."""
    factors = list(risk.get("factors", []))
    score = risk.get("combined_score", 0)
    level = risk.get("priority_level", "informativo")
    source = risk.get("source", "rules")

    why = []
    if score >= 80:
        why.append("La prioridad es CRÍTICA porque:")
    elif score >= 60:
        why.append("La prioridad es ALTA porque:")
    elif score >= 40:
        why.append("La prioridad es MEDIA porque:")
    elif score >= 20:
        why.append("La prioridad es BAJA porque:")
    else:
        why.append("La prioridad es INFORMATIVA porque:")

    for factor in factors:
        why.append(f"  - {factor}")

    if context.get("trend", 0) > 0.3:
        why.append("  - La tendencia es creciente (nuevos eventos aparecen)")

    if operation.get("needs_open", 0) > 0:
        why.append(f"  - Hay {operation['needs_open']} necesidades abiertas en la zona")

    if operation.get("resources_available", 0) == 0:
        why.append("  - No hay recursos disponibles cerca")

    if operation.get("active_assignments", 0) > 0:
        why.append(f"  - Hay {operation['active_assignments']} asignaciones activas en curso")

    return {
        "summary": " ".join(why),
        "factors": factors,
        "score_breakdown": {
            "severity": situation.get("severity", 0),
            "exposure": exposure.get("exposure_score", 0),
            "event_density": context.get("event_density", 0),
            "trend": context.get("trend", 0),
        },
        "methodology": risk.get("methodology_version", "rules-v1"),
        "source": source,
        "georisk_source": "georisk" if georisk and georisk.get("status") == "ok" else None,
        "h3_index": h3_index,
    }


def _weather_to_score(weather: dict) -> float:
    """Convierte datos meteorológicos a score 0-1."""
    if not weather:
        return 0.0
    severity = weather.get("severity", "")
    if severity in ("rojo", "extreme"):
        return 1.0
    if severity in ("naranja", "high"):
        return 0.7
    if severity in ("amarillo", "moderate"):
        return 0.4
    return 0.1


def _is_recent(event_time, hours: int = 24) -> bool:
    """Verifica si un evento es reciente."""
    if not event_time:
        return False
    try:
        if isinstance(event_time, str):
            dt = datetime.fromisoformat(event_time.replace("Z", "+00:00"))
        else:
            dt = event_time
        now = datetime.now(timezone.utc)
        return (now - dt).total_seconds() < hours * 3600
    except (ValueError, TypeError):
        return False
