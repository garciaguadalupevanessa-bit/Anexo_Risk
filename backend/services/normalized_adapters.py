"""Unified adapter that wraps existing source adapters.

Normalizes output from GDACS, USGS, FIRMS, AEMET/Open-Meteo
into the common NormalizedEvent format.
"""
import hashlib
from datetime import datetime, timezone
from typing import List, Optional

from geodata.adapters.base import NormalizedEvent, EntityType, SourceStatus, SourceCapabilities


def normalize_gdacs_event(event: dict) -> NormalizedEvent:
    """Normalize a GDACS alert into NormalizedEvent."""
    severity_map = {"red": 1.0, "orange": 0.75, "yellow": 0.5, "green": 0.25}
    type_map = {
        "Earthquake": EntityType.EARTHQUAKE,
        "Tropical Cyclone": EntityType.CYCLONE,
        "Flood": EntityType.FLOOD,
        "Wildfire": EntityType.FIRE,
        "Volcano": EntityType.VOLCANO,
        "Drought": EntityType.OTHER,
    }
    raw_type = event.get("tipo", "Other")
    entity_type = type_map.get(raw_type, EntityType.OTHER)
    severity_str = event.get("severidad", "green")

    return NormalizedEvent(
        id=f"gdacs_{event.get('id', _hash_event('gdacs', event))}",
        external_id=event.get("id", ""),
        entity_type=entity_type,
        source="gdacs",
        title=event.get("titulo", "GDACS Alert"),
        description=event.get("descripcion", ""),
        timestamp=event.get("fecha"),
        severity=severity_str,
        severity_float=severity_map.get(severity_str, 0.25),
        lat=event.get("lat"),
        lon=event.get("lon"),
        country=event.get("pais"),
        status="active",
        is_active=True,
        raw_metadata=event,
        provenance={"source": "gdacs", "adapter_version": "1.0", "retrieved_at": datetime.now(timezone.utc).isoformat()},
    )


def normalize_usgs_event(event: dict) -> NormalizedEvent:
    """Normalize a USGS earthquake into NormalizedEvent."""
    mag = event.get("magnitude", 0)
    severity = min(mag / 8.0, 1.0) if mag else 0.25

    return NormalizedEvent(
        id=f"usgs_{event.get('external_id', _hash_event('usgs', event))}",
        external_id=event.get("external_id", ""),
        entity_type=EntityType.EARTHQUAKE,
        source="usgs",
        title=event.get("title", "Earthquake"),
        description=event.get("description", ""),
        timestamp=event.get("event_time"),
        severity=_severity_from_float(severity),
        severity_float=severity,
        lat=event.get("latitud"),
        lon=event.get("longitud"),
        magnitude=mag,
        depth=event.get("depth"),
        status="active",
        is_active=True,
        raw_metadata=event.get("raw_data"),
        provenance={"source": "usgs", "adapter_version": "1.0", "retrieved_at": datetime.now(timezone.utc).isoformat()},
    )


def normalize_firms_event(event: dict) -> NormalizedEvent:
    """Normalize a NASA FIRMS fire detection into NormalizedEvent."""
    confidence_map = {"low": 0.25, "nominal": 0.5, "high": 0.75}
    conf = event.get("confidence", "nominal")

    return NormalizedEvent(
        id=f"firms_{event.get('id', _hash_event('firms', event))}",
        external_id=event.get("id", ""),
        entity_type=EntityType.FIRE,
        source="firms",
        title=f"Fire detection ({event.get('satellite', 'VIIRS')})",
        description=f"Brightness: {event.get('brightness', 'N/A')}, FRP: {event.get('frp', 'N/A')}",
        timestamp=_firms_timestamp(event),
        severity=_severity_from_float(confidence_map.get(conf, 0.5)),
        severity_float=confidence_map.get(conf, 0.5),
        lat=event.get("lat"),
        lon=event.get("lon"),
        country=event.get("country"),
        confidence=confidence_map.get(conf, 0.5),
        status="active",
        is_active=True,
        raw_metadata=event,
        provenance={"source": "firms", "adapter_version": "1.0", "retrieved_at": datetime.now(timezone.utc).isoformat()},
    )


def normalize_aemet_event(alert: dict) -> NormalizedEvent:
    """Normalize an AEMET/Open-Meteo weather alert into NormalizedEvent."""
    nivel = alert.get("nivel", "verde")
    severity_map = {"rojo": 1.0, "naranja": 0.75, "amarillo": 0.5, "verde": 0.25}

    return NormalizedEvent(
        id=f"aemet_{alert.get('id', _hash_event('aemet', alert))}",
        external_id=alert.get("id", ""),
        entity_type=EntityType.WEATHER,
        source="aemet",
        title=alert.get("titulo", "Weather alert"),
        description=alert.get("descripcion", ""),
        timestamp=alert.get("fecha"),
        severity=nivel,
        severity_float=severity_map.get(nivel, 0.25),
        lat=alert.get("lat"),
        lon=alert.get("lon"),
        country="ES",
        status="active",
        is_active=True,
        raw_metadata=alert,
        provenance={"source": alert.get("fuente", "aemet"), "adapter_version": "1.0", "retrieved_at": datetime.now(timezone.utc).isoformat()},
    )


def _hash_event(source: str, event: dict) -> str:
    """Generate a deterministic hash for an event."""
    key = f"{source}:{event.get('lat', '')}:{event.get('lon', '')}:{event.get('titulo', '')}"
    return hashlib.md5(key.encode()).hexdigest()[:12]


def _severity_from_float(val: float) -> str:
    """Convert severity float to string."""
    if val >= 0.75:
        return "rojo"
    elif val >= 0.5:
        return "naranja"
    elif val >= 0.25:
        return "amarillo"
    return "verde"


def _firms_timestamp(event: dict) -> Optional[str]:
    """Parse FIRMS acq_date + acq_time into ISO string."""
    date = event.get("acq_date", "")
    time = event.get("acq_time", "0000")
    if date and time:
        try:
            return f"{date}T{time[:2]}:{time[2:]}:00Z"
        except Exception:
            pass
    return date or None
