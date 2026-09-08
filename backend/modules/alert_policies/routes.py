"""Alert Policy API endpoints."""
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from services.alert_policy import (
    create_policy, get_policy, list_policies,
    evaluate_policy, get_evaluations,
)

router = APIRouter(prefix="/api/alert-policies", tags=["alert-policies"])


class PolicyCreate(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = ""
    hazard_types: Optional[List[str]] = None
    min_severity: str = "naranja"
    min_risk_score: float = 0.5
    target_node_types: Optional[List[str]] = None
    target_region_ids: Optional[List[str]] = None
    is_active: bool = True
    is_dry_run: bool = True


class EvaluateRequest(BaseModel):
    hazard_type: str
    severity: Optional[str] = None
    severity_float: Optional[float] = None
    action_area_h3_cells: Optional[List[str]] = None
    incident_id: Optional[str] = None
    event_id: Optional[str] = None


@router.post("", status_code=201)
def create(data: PolicyCreate):
    """Create an alert policy."""
    return create_policy(data.model_dump())


@router.get("")
def list_all(is_active: Optional[bool] = Query(True)):
    """List alert policies."""
    policies = list_policies(is_active)
    return {"count": len(policies), "policies": policies}


@router.get("/{policy_id}")
def get_one(policy_id: str):
    """Get a single policy."""
    policy = get_policy(policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


@router.post("/{policy_id}/evaluate")
def evaluate(policy_id: str, data: EvaluateRequest):
    """Evaluate a policy against conditions (dry-run by default)."""
    result = evaluate_policy(
        policy_id=policy_id,
        hazard_type=data.hazard_type,
        severity=data.severity,
        severity_float=data.severity_float,
        action_area_h3_cells=data.action_area_h3_cells,
        incident_id=data.incident_id,
        event_id=data.event_id,
    )
    return result


@router.get("/{policy_id}/evaluations")
def evaluations(policy_id: str, limit: int = Query(50, ge=1, le=200)):
    """Get recent evaluations for a policy."""
    evals = get_evaluations(policy_id, limit)
    return {"policy_id": policy_id, "count": len(evals), "evaluations": evals}
