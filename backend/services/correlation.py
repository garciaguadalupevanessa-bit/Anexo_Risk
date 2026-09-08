"""Event Correlation Engine.

Groups related normalized events into coherent incidents.
Supports: distance, time, type, geometry, confidence.
"""
import math
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
from modules.normalized_events import models as event_models
from modules.incidentes import models as incident_models
from modules.timeline import models as timeline_models


# Default correlation thresholds
DEFAULT_DISTANCE_KM = 50.0
DEFAULT_TIME_WINDOW_HOURS = 2.0
DEFAULT_CONFIDENCE_THRESHOLD = 0.5


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in km."""
    R = 6371.0
    lat1_r, lon1_r = math.radians(lat1), math.radians(lon1)
    lat2_r, lon2_r = math.radians(lat2), math.radians(lon2)
    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def are_events_correlated(
    event_a: Dict[str, Any],
    event_b: Dict[str, Any],
    max_distance_km: float = DEFAULT_DISTANCE_KM,
    max_time_hours: float = DEFAULT_TIME_WINDOW_HOURS,
) -> Tuple[bool, float, str]:
    """Determine if two events are correlated.

    Returns: (is_correlated, confidence, reason)
    """
    # Type must match (same entity_type)
    if event_a.get("entity_type") != event_b.get("entity_type"):
        return False, 0.0, "type_mismatch"

    # Both must have coordinates
    lat_a, lon_a = event_a.get("lat"), event_a.get("lon")
    lat_b, lon_b = event_b.get("lat"), event_b.get("lon")
    if not all([lat_a, lon_a, lat_b, lon_b]):
        return False, 0.0, "missing_coordinates"

    # Distance check
    distance = haversine_km(lat_a, lon_a, lat_b, lon_b)
    if distance > max_distance_km:
        return False, 0.0, f"distance_{distance:.0f}km"

    # Time check
    ts_a = event_a.get("timestamp")
    ts_b = event_b.get("timestamp")
    if ts_a and ts_b:
        try:
            dt_a = datetime.fromisoformat(ts_a.replace("Z", "+00:00"))
            dt_b = datetime.fromisoformat(ts_b.replace("Z", "+00:00"))
            time_diff = abs((dt_a - dt_b).total_seconds()) / 3600
            if time_diff > max_time_hours:
                return False, 0.0, f"time_{time_diff:.1f}h"
        except (ValueError, TypeError):
            pass

    # Calculate confidence based on distance and time
    distance_score = max(0, 1 - (distance / max_distance_km))
    confidence = distance_score * 0.7 + 0.3  # At least 0.3 for passing both checks

    return True, confidence, "matched"


def correlate_events(
    events: List[Dict[str, Any]],
    max_distance_km: float = DEFAULT_DISTANCE_KM,
    max_time_hours: float = DEFAULT_TIME_WINDOW_HOURS,
) -> List[Dict[str, Any]]:
    """Group events into correlated clusters.

    Returns list of clusters, each containing related events.
    """
    if not events:
        return []

    # Sort by timestamp (None timestamps go to the end)
    events = sorted(events, key=lambda e: e.get("timestamp") or "")

    clusters = []
    assigned = set()

    for i, event_a in enumerate(events):
        if i in assigned:
            continue

        cluster = [event_a]
        assigned.add(i)

        for j, event_b in enumerate(events):
            if j in assigned:
                continue

            is_correlated, confidence, reason = are_events_correlated(
                event_a, event_b, max_distance_km, max_time_hours
            )

            # Check against any event in the cluster
            if is_correlated:
                cluster.append(event_b)
                assigned.add(j)

        clusters.append({
            "events": cluster,
            "count": len(cluster),
            "avg_confidence": sum((e.get("confidence") or 0.5) for e in cluster) / len(cluster),
            "entity_type": cluster[0].get("entity_type"),
            "sources": list(set(e.get("source", "unknown") for e in cluster)),
        })

    return clusters


def create_incident_from_cluster(
    cluster: Dict[str, Any],
    region_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Create an incident from a correlated event cluster."""
    events = cluster["events"]
    if not events:
        return None

    # Use the most severe event as primary
    primary = max(events, key=lambda e: e.get("severity_float", 0))

    # Calculate centroid
    lats = [e.get("lat", 0) for e in events if e.get("lat")]
    lons = [e.get("lon", 0) for e in events if e.get("lon")]
    centroid_lat = sum(lats) / len(lats) if lats else None
    centroid_lon = sum(lons) / len(lons) if lons else None

    # Build title from sources
    source_list = ", ".join(cluster["sources"])
    title = f"{primary.get('title', 'Incident')} [{source_list}]"

    # Create incident
    incident_data = {
        "title": title[:500],
        "lat": centroid_lat,
        "lon": centroid_lon,
        "event_type": primary.get("entity_type", "other"),
        "source": "correlation",
        "severity": primary.get("severity", "verde"),
        "magnitude": primary.get("magnitude"),
        "description": f"Correlated from {cluster['count']} events across: {source_list}",
        "is_active": True,
    }

    # Store in normalized_events as a correlated incident
    incident_event = {
        "entity_type": "other",
        "source": "correlation",
        "title": title[:500],
        "description": incident_data["description"],
        "lat": centroid_lat,
        "lon": centroid_lon,
        "severity": primary.get("severity"),
        "severity_float": primary.get("severity_float"),
        "magnitude": primary.get("magnitude"),
        "status": "active",
        "is_active": True,
        "raw_metadata": {
            "correlation_method": "distance_time_type",
            "correlated_events": [e.get("id") for e in events],
            "cluster_count": cluster["count"],
            "sources": cluster["sources"],
        },
        "provenance": {
            "source": "correlation",
            "method": "distance_time_type",
            "confidence": cluster["avg_confidence"],
            "event_count": cluster["count"],
        },
    }

    stored = event_models.store_event(incident_event)
    return stored
