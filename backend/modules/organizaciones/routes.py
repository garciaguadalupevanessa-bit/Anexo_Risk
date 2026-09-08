"""Routes para Organizaciones y Usuarios Operacionales."""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from middleware.auth import requiere_clave_organizador

from modules.organizaciones.models import (
    create_organization,
    create_operational_user,
    get_organization,
    list_organizations,
    list_operational_users,
    grant_region_access,
    revoke_region_access,
    get_org_region_access,
    check_region_access,
    get_orgs_in_region,
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


class RegionAccessGrant(BaseModel):
    region_id: str
    access_level: str = "read"


@router.post("/{org_id}/region-access")
def grant_access(org_id: int, data: RegionAccessGrant):
    """Grant organization access to a region."""
    org = get_organization(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organización no encontrada")
    grant_region_access(org_id, data.region_id, data.access_level)
    return {"org_id": org_id, "region_id": data.region_id, "access_level": data.access_level}


@router.delete("/{org_id}/region-access/{region_id}")
def revoke_access(org_id: int, region_id: str):
    """Revoke organization access to a region."""
    revoke_region_access(org_id, region_id)
    return {"org_id": org_id, "region_id": region_id, "revoked": True}


@router.get("/{org_id}/region-access")
def get_access(org_id: int):
    """Get all region access grants for an organization."""
    grants = get_org_region_access(org_id)
    return {"org_id": org_id, "grants": grants}


@router.get("/region/{region_id}")
def orgs_in_region(region_id: str):
    """Get all organizations with access to a region."""
    orgs = get_orgs_in_region(region_id)
    return {"region_id": region_id, "count": len(orgs), "organizations": orgs}


@router.get("/{org_id}/check-access/{region_id}")
def check_access(org_id: int, region_id: str, level: str = Query("read")):
    """Check if organization has access to a region."""
    has_access = check_region_access(org_id, region_id, level)
    return {"org_id": org_id, "region_id": region_id, "level": level, "has_access": has_access}
