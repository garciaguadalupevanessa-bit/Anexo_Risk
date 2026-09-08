"""Alert Policy service.

Evaluates which nodes/entities should be notified based on action areas,
risk levels, and configured policies. Supports dry-run mode.
"""
from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from db.database import get_cursor

logger = logging.getLogger(__name__)

SEVERITY_ORDER = {"verde": 0, "amarilla": 1, "naranja": 2, "roja": 3}


def create_policy(policy_data: dict) -> dict:
    """Create a new alert policy."""
    policy_id = policy_data.get("id") or f"pol_{uuid.uuid4().hex[:12]}"
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO alert_policies
            (id, name, description, hazard_types_json, min_severity,
             min_risk_score, target_node_types_json, target_region_ids_json,
             is_active, is_dry_run)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                policy_id,
                policy_data["name"],
                policy_data.get("description", ""),
                json.dumps(policy_data.get("hazard_types")) if policy_data.get("hazard_types") else None,
                policy_data.get("min_severity", "naranja"),
                policy_data.get("min_risk_score", 0.5),
                json.dumps(policy_data.get("target_node_types")) if policy_data.get("target_node_types") else None,
                json.dumps(policy_data.get("target_region_ids")) if policy_data.get("target_region_ids") else None,
                1 if policy_data.get("is_active", True) else 0,
                1 if policy_data.get("is_dry_run", True) else 0,
            ),
        )
    return get_policy(policy_id)


def get_policy(policy_id: str) -> dict | None:
    """Get a single policy."""
    with get_cursor() as cur:
        row = cur.execute("SELECT * FROM alert_policies WHERE id = ?", (policy_id,)).fetchone()
        if row:
            return _row_to_response(row)
    return None


def list_policies(is_active: bool | None = True) -> list[dict]:
    """List alert policies."""
    query = "SELECT * FROM alert_policies WHERE 1=1"
    params = []
    if is_active is not None:
        query += " AND is_active = ?"
        params.append(1 if is_active else 0)
    query += " ORDER BY name"
    with get_cursor() as cur:
        rows = cur.execute(query, params).fetchall()
        return [_row_to_response(r) for r in rows]


def evaluate_policy(
    policy_id: str,
    hazard_type: str,
    severity: str | None = None,
    severity_float: float | None = None,
    action_area_h3_cells: list[str] | None = None,
    incident_id: str | None = None,
    event_id: str | None = None,
) -> dict[str, Any]:
    """Evaluate a policy against current conditions.

    In dry-run mode, computes eligible nodes but doesn't send notifications.
    """
    policy = get_policy(policy_id)
    if not policy or not policy.get("is_active"):
        return {"eligible_count": 0, "notifications_sent": 0, "reason": "policy_inactive"}

    # Check hazard type match
    hazard_types = policy.get("hazard_types")
    if hazard_types and hazard_type not in hazard_types:
        return {"eligible_count": 0, "notifications_sent": 0, "reason": "hazard_type_mismatch"}

    # Check severity
    min_severity = policy.get("min_severity", "naranja")
    if severity:
        if SEVERITY_ORDER.get(severity, 0) < SEVERITY_ORDER.get(min_severity, 0):
            return {"eligible_count": 0, "notifications_sent": 0, "reason": "severity_below_threshold"}

    # Check risk score
    min_risk = policy.get("min_risk_score", 0.5)
    if severity_float is not None and severity_float < min_risk:
        return {"eligible_count": 0, "notifications_sent": 0, "reason": "risk_below_threshold"}

    # Find eligible nodes in action area
    eligible_nodes = _find_eligible_nodes(
        policy, action_area_h3_cells or []
    )

    is_dry_run = policy.get("is_dry_run", True)
    notifications_sent = 0 if is_dry_run else len(eligible_nodes)

    # Store evaluation
    eval_id = f"eval_{uuid.uuid4().hex[:12]}"
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO alert_policy_evaluations
            (id, policy_id, incident_id, event_id, eligible_nodes_json,
             notifications_sent, is_dry_run)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                eval_id, policy_id, incident_id, event_id,
                json.dumps([n["id"] for n in eligible_nodes]),
                notifications_sent,
                1 if is_dry_run else 0,
            ),
        )

    return {
        "evaluation_id": eval_id,
        "policy_id": policy_id,
        "eligible_count": len(eligible_nodes),
        "eligible_nodes": eligible_nodes,
        "notifications_sent": notifications_sent,
        "is_dry_run": is_dry_run,
    }


def get_evaluations(policy_id: str, limit: int = 50) -> list[dict]:
    """Get recent evaluations for a policy."""
    with get_cursor() as cur:
        rows = cur.execute(
            """SELECT * FROM alert_policy_evaluations
            WHERE policy_id = ? ORDER BY evaluated_at DESC LIMIT ?""",
            (policy_id, limit),
        ).fetchall()
        return [_row_to_eval_response(r) for r in rows]


def _find_eligible_nodes(policy: dict, h3_cells: list[str]) -> list[dict]:
    """Find nodes that match policy targets and are in the action area."""
    target_types = policy.get("target_node_types")
    query = "SELECT * FROM operational_nodes WHERE is_active = 1"
    params = []
    if target_types:
        placeholders = ",".join("?" for _ in target_types)
        query += f" AND node_type IN ({placeholders})"
        params.extend(target_types)

    with get_cursor() as cur:
        rows = cur.execute(query, params).fetchall()
        nodes = [dict(r) for r in rows]

    if not h3_cells:
        return nodes

    # Filter nodes whose h3_index is in the action area
    h3_set = set(h3_cells)
    return [n for n in nodes if n.get("h3_index") in h3_set]


def _row_to_response(row):
    """Convert sqlite3.Row to dict."""
    d = dict(row)
    for key in ("hazard_types_json", "target_node_types_json", "target_region_ids_json"):
        if key in d and d[key]:
            try:
                d[key] = json.loads(d[key])
            except (json.JSONDecodeError, TypeError):
                pass
    if "hazard_types_json" in d:
        d["hazard_types"] = d.pop("hazard_types_json")
    if "target_node_types_json" in d:
        d["target_node_types"] = d.pop("target_node_types_json")
    if "target_region_ids_json" in d:
        d["target_region_ids"] = d.pop("target_region_ids_json")
    if "is_active" in d:
        d["is_active"] = bool(d["is_active"])
    if "is_dry_run" in d:
        d["is_dry_run"] = bool(d["is_dry_run"])
    return d


def _row_to_eval_response(row):
    """Convert evaluation row to dict."""
    d = dict(row)
    for key in ("eligible_nodes_json",):
        if key in d and d[key]:
            try:
                d[key] = json.loads(d[key])
            except (json.JSONDecodeError, TypeError):
                pass
    if "eligible_nodes_json" in d:
        d["eligible_nodes"] = d.pop("eligible_nodes_json")
    if "is_dry_run" in d:
        d["is_dry_run"] = bool(d["is_dry_run"])
    return d
