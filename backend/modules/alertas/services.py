"""Business logic, data aggregation, and query filtering for alerts."""

from datetime import datetime, timezone
from enum import Enum
import logging
import threading
from typing import Any, Dict, List, Optional

from integrations import gdacs_client, gdacs_mock, proteccion_civil_client

logger = logging.getLogger(__name__)

LOCAL_ALERTS_DB: Dict[str, Dict[str, Any]] = {}
_DB_LOCK = threading.Lock()

COUNTRY_ALIASES = {
    "españa": "spain",
    "espana": "spain",
    "francia": "france",
    "italia": "italy",
    "grecia": "greece",
    "turquia": "turkey",
    "turquía": "turkey",
    "marruecos": "morocco",
    "portugal": "portugal",
    "alemania": "germany",
    "reino unido": "united kingdom",
    "estados unidos": "united states",
}


def _normalize_alert(item: Dict[str, Any]) -> Dict[str, Any]:
    """Ensures external and internal items comply with unified GeoRisk schemas."""
    normalized = dict(item)
    ext_id = normalized.get("external_id") or normalized.get("id")
    normalized["external_id"] = str(ext_id) if ext_id else None

    source_val = normalized.get("source") or normalized.get("fuente") or "GDACS"
    normalized["source"] = str(source_val).upper()
    normalized["fuente"] = normalized["source"]

    sev_raw = str(normalized.get("severity") or normalized.get("severidad") or "GREEN").upper()
    if sev_raw in ("RED", "ORANGE", "GREEN"):
        normalized["severity"] = sev_raw
        normalized["severidad"] = sev_raw
    else:
        normalized["severity"] = "GREEN"
        normalized["severidad"] = "GREEN"

    if "risk_level" not in normalized and "nivel_riesgo" not in normalized:
        if normalized["severity"] == "RED":
            normalized["risk_level"] = "high"
        elif normalized["severity"] == "ORANGE":
            normalized["risk_level"] = "medium"
        else:
            normalized["risk_level"] = "low"
    elif "nivel_riesgo" in normalized and "risk_level" not in normalized:
        normalized["risk_level"] = normalized["nivel_riesgo"]

    if "status" not in normalized:
        normalized["status"] = "active" if normalized.get("is_active", True) else "deactivated"

    normalized["is_active"] = normalized.get("is_active", True)

    if not normalized.get("zone") and normalized.get("lat") is not None and normalized.get("lon") is not None:
        lat, lon = float(normalized["lat"]), float(normalized["lon"])
        normalized["zone"] = {
            "type": "Polygon",
            "coordinates": [
                [
                    [lon - 0.01, lat - 0.01],
                    [lon + 0.01, lat - 0.01],
                    [lon + 0.01, lat + 0.01],
                    [lon - 0.01, lat + 0.01],
                    [lon - 0.01, lat - 0.01],
                ]
            ],
        }
    return normalized


def fetch_base_alerts() -> List[Dict[str, Any]]:
    """Retrieves raw alert items with deduplication against local state."""
    raw_alerts: List[Dict[str, Any]] = []

    try:
        gdacs_data = gdacs_client.get_alerts()
        if gdacs_data:
            raw_alerts.extend(gdacs_data)
    except Exception as exc:
        logger.error("Failed to fetch alerts from GDACS client: %s", exc, exc_info=True)

    try:
        pc_data = proteccion_civil_client.get_alerts()
        if pc_data:
            raw_alerts.extend(pc_data)
    except Exception as exc:
        logger.error("Failed to fetch alerts from Proteccion Civil client: %s", exc, exc_info=True)

    if not raw_alerts:
        logger.warning("No external alerts retrieved. Falling back to internal mock dataset.")
        raw_alerts = getattr(gdacs_mock, "MOCK_GDACS_DATA", [])

    with _DB_LOCK:
        seen_external_ids = {
            item.get("external_id")
            for item in LOCAL_ALERTS_DB.values()
            if item.get("external_id")
        }
        result: List[Dict[str, Any]] = list(LOCAL_ALERTS_DB.values())

    for item in raw_alerts:
        norm = _normalize_alert(item)
        ext_id = norm.get("external_id")
        if ext_id and ext_id in seen_external_ids:
            continue
        result.append(norm)

    return result


def list_filtered_alerts(
    tipo: Optional[str] = None,
    severidad: Optional[str] = None,
    pais: Optional[str] = None,
    external_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Filters and sorts alert records based on specified query parameters."""
    alerts: List[Dict[str, Any]] = fetch_base_alerts()

    tipo_clean = tipo.strip().lower() if tipo and tipo.strip() else None
    severidad_clean = severidad.strip().upper() if severidad and severidad.strip() else None
    search_term = pais.strip().lower() if pais and pais.strip() else None
    ext_id_clean = external_id.strip() if external_id and external_id.strip() else None

    if search_term:
        search_term = COUNTRY_ALIASES.get(search_term, search_term)

    filtered_alerts = []
    for item in alerts:
        if ext_id_clean and item.get("external_id") != ext_id_clean:
            continue
        if tipo_clean and str(item.get("tipo", item.get("type", ""))).lower() != tipo_clean:
            continue
        if severidad_clean and str(item.get("severidad", item.get("severity", ""))).upper() != severidad_clean:
            continue
        if search_term and search_term not in str(item.get("pais", item.get("country", ""))).lower():
            continue
        filtered_alerts.append(item)

    min_utc_date = datetime.min.replace(tzinfo=timezone.utc)

    def extract_sorting_key(item: Dict[str, Any]) -> datetime:
        dt = item.get("fecha") or item.get("date")
        if not isinstance(dt, datetime):
            return min_utc_date
        return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)

    filtered_alerts.sort(key=extract_sorting_key, reverse=True)
    return filtered_alerts


def create_manual_alert(data: Dict[str, Any]) -> Dict[str, Any]:
    """Creates a new manual alert item and stores it locally."""
    with _DB_LOCK:
        alert_id = f"manual-{len(LOCAL_ALERTS_DB) + 1000}"
        risk_level = data.get("nivel_riesgo") or data.get("risk_level") or "low"
        if isinstance(risk_level, Enum):
            risk_level = risk_level.value
            
        tipo_val = data.get("tipo") or data.get("type") or "otro"
        if isinstance(tipo_val, Enum):
            tipo_val = tipo_val.value

        new_alert = {
            "id": alert_id,
            "external_id": alert_id,
            "source": "MANUAL",
            "fuente": "MANUAL",
            "tipo": tipo_val,
            "titulo": data.get("titulo") or data.get("title") or "Alerta Manual",
            "descripcion": data.get("descripcion") or data.get("description") or "",
            "severidad": "RED" if risk_level == "high" else "GREEN",
            "severity": "RED" if risk_level == "high" else "GREEN",
            "risk_level": risk_level,
            "status": "active",
            "is_active": True,
            "zone": data.get("zone"),
            "pais": "Spain",
            "fecha": data.get("fecha") or data.get("date") or datetime.now(timezone.utc),
            "enlace": "",
        }
        LOCAL_ALERTS_DB[alert_id] = new_alert
    return new_alert


def set_alert_status(alert_id: str, action: str) -> Dict[str, Any]:
    """Updates operational status or risk tier for a given alert by identifier."""
    alerts = fetch_base_alerts()
    target = next((a for a in alerts if a["id"] == alert_id or a.get("external_id") == alert_id), None)

    if not target:
        raise KeyError("Alert not found")

    if action in ("activar", "activate"):
        target["status"] = "active"
        target["is_active"] = True
    elif action in ("alto-riesgo", "high-risk"):
        target["risk_level"] = "high"
        target["status"] = "high_risk"
        target["is_active"] = True
    elif action in ("desactivar", "deactivate"):
        target["status"] = "deactivated"
        target["is_active"] = False

    with _DB_LOCK:
        LOCAL_ALERTS_DB[target["id"]] = target
    return target