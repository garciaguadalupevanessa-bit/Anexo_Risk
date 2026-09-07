"""Routes para Organizaciones y Usuarios Operacionales."""
from fastapi import APIRouter, Depends, HTTPException
from middleware.auth import requiere_clave_organizador

from modules.organizaciones.models import (
    create_organization,
    create_operational_user,
    get_organization,
    list_organizations,
    list_operational_users,
)
from modules.organizaciones.schemas import (
    OperationalUserCreate,
    OperationalUserResponse,
    OrganizationCreate,
    OrganizationResponse,
)

router = APIRouter(prefix="/api/organizations", tags=["organizations"])


@router.get("", response_model=list[OrganizationResponse])
def list_orgs(org_type: str | None = None, region: str | None = None):
    return list_organizations(org_type=org_type, region=region)


@router.get("/{org_id}", response_model=OrganizationResponse)
def get_org(org_id: int):
    org = get_organization(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organización no encontrada")
    return org


@router.post("", response_model=OrganizationResponse, status_code=201, dependencies=[Depends(requiere_clave_organizador)])
def create_org(data: OrganizationCreate):
    return create_organization(data.name, data.type, data.region)


@router.get("/{org_id}/users", response_model=list[OperationalUserResponse])
def list_users(org_id: int, role: str | None = None):
    return list_operational_users(org_id=org_id, role=role)


@router.post("/{org_id}/users", response_model=OperationalUserResponse, status_code=201, dependencies=[Depends(requiere_clave_organizador)])
def create_user(org_id: int, data: OperationalUserCreate):
    org = get_organization(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organización no encontrada")
    return create_operational_user(org_id, data.username, data.display_name, data.role)
