"""API router for alert endpoints using Spanish routes and parameters."""

from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from modules.alertas.schemas import AlertCreate, AlertResponse, EventTypeEnum, SeverityEnum
from modules.alertas.services import create_manual_alert, list_filtered_alerts, set_alert_status

router = APIRouter(prefix="/api/alertas", tags=["alertas"])


def _validate_polygon_geojson(zone: Dict) -> None:
    """Validates that input dictionary conforms strictly to GeoJSON Polygon specification."""
    if not isinstance(zone, dict) or zone.get("type") != "Polygon":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La zona debe ser un objeto GeoJSON de tipo Polygon válido",
        )
    coordinates = zone.get("coordinates")
    if not isinstance(coordinates, list) or len(coordinates) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Las coordenadas del Polygon no pueden estar vacías",
        )


@router.get("", response_model=List[AlertResponse])
def get_alerts(
    tipo: Optional[str] = Query(None, description="Filtrar por tipo de evento"),
    severidad: Optional[str] = Query(None, description="Filtrar por nivel de severidad"),
    pais: Optional[str] = Query(None, description="Filtrar por país"),
    external_id: Optional[str] = Query(None, description="Filtrar por identificador externo"),
) -> List[Dict]:
    """Retrieves official disaster alerts applying optional filters."""
    clean_type = tipo.strip() if tipo and tipo.strip() else None
    clean_severity = severidad.strip() if severidad and severidad.strip() else None
    clean_country = pais.strip() if pais and pais.strip() else None
    clean_external_id = external_id.strip() if external_id and external_id.strip() else None

    if clean_type:
        try:
            EventTypeEnum(clean_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Tipo de evento no válido: {clean_type}",
            )

    if clean_severity:
        try:
            SeverityEnum(clean_severity.upper())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Nivel de severidad no válido: {clean_severity}",
            )

    return list_filtered_alerts(
        tipo=clean_type,
        severidad=clean_severity,
        pais=clean_country,
        external_id=clean_external_id,
    )


@router.post("", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
def create_alert(payload: AlertCreate) -> Dict:
    """Creates a new manual alert item with spatial polygon delimitation."""
    _validate_polygon_geojson(payload.zone)
    return create_manual_alert(payload.model_dump())


@router.post("/{alert_id}/activar", response_model=AlertResponse)
def activate_alert(alert_id: str) -> Dict:
    """Activates a specific alert by its identifier."""
    try:
        return set_alert_status(alert_id, "activar")
    except KeyError:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")


@router.post("/{alert_id}/alto-riesgo", response_model=AlertResponse)
def set_high_risk_alert(alert_id: str) -> Dict:
    """Marks an alert as high risk (risk_level=high) and sets its status to active."""
    try:
        return set_alert_status(alert_id, "alto-riesgo")
    except KeyError:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")


@router.post("/{alert_id}/desactivar", response_model=AlertResponse)
def deactivate_alert(alert_id: str) -> Dict:
    """Deactivates a specific alert by its identifier."""
    try:
        return set_alert_status(alert_id, "desactivar")
    except KeyError:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")