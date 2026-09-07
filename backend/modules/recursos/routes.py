"""Routes para Recursos."""
from fastapi import APIRouter, Depends, HTTPException, Query
from middleware.auth import requiere_clave_organizador

from modules.recursos.models import (
    create_resource,
    get_nearby_resources,
    get_resource,
    list_resources,
    update_resource,
)
from modules.recursos.schemas import ResourceCreate, ResourceResponse, ResourceUpdate

router = APIRouter(prefix="/api/resources", tags=["resources"])


@router.get("", response_model=list[ResourceResponse])
def list_res(
    organization_id: int | None = None,
    type: str | None = None,
    status: str | None = None,
    lat_min: float | None = Query(None, ge=-90, le=90),
    lat_max: float | None = Query(None, ge=-90, le=90),
    lon_min: float | None = Query(None, ge=-180, le=180),
    lon_max: float | None = Query(None, ge=-180, le=180),
):
    return list_resources(
        org_id=organization_id,
        resource_type=type,
        status=status,
        lat_min=lat_min,
        lat_max=lat_max,
        lon_min=lon_min,
        lon_max=lon_max,
    )


@router.get("/nearby", response_model=list[ResourceResponse])
def nearby_resources(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    radius: float = Query(1.0, gt=0, le=10),
):
    return get_nearby_resources(lat, lon, radius)


@router.get("/{resource_id}", response_model=ResourceResponse)
def get_res(resource_id: int):
    res = get_resource(resource_id)
    if not res:
        raise HTTPException(status_code=404, detail="Recurso no encontrado")
    return res


@router.post("", response_model=ResourceResponse, status_code=201, dependencies=[Depends(requiere_clave_organizador)])
def create_res(data: ResourceCreate):
    return create_resource(
        data.organization_id,
        data.type,
        data.name,
        data.description,
        data.quantity,
        data.latitud,
        data.longitud,
    )


@router.patch("/{resource_id}", response_model=ResourceResponse, dependencies=[Depends(requiere_clave_organizador)])
def update_res(resource_id: int, data: ResourceUpdate):
    res = update_resource(
        resource_id,
        available_quantity=data.available_quantity,
        status=data.status,
        latitud=data.latitud,
        longitud=data.longitud,
    )
    if not res:
        raise HTTPException(status_code=404, detail="Recurso no encontrado")
    return res
