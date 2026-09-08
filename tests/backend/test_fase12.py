"""Tests for FASE 12 — Alert Policy / Dry Run.

Tests cover:
- Policy CRUD
- Policy evaluation in dry-run mode
- Hazard type matching
- Severity threshold
- Risk score threshold
- Eligible node discovery
"""
import pytest
import sys
import os
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
os.environ.setdefault("TESTING", "true")
os.environ.setdefault("JWT_SECRET_KEY", "test-fase12")
os.environ.setdefault("ANEXO_ADMIN_KEY", "test-fase12")

from fastapi.testclient import TestClient
from main import app
from db.database import init_db

client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    yield


def _uid():
    return "p12_" + uuid.uuid4().hex[:8]


class TestPolicyCRUD:
    def test_create_policy(self):
        """Create an alert policy."""
        pid = _uid()
        resp = client.post("/api/alert-policies", json={
            "id": pid, "name": "Fire Alert Policy",
            "hazard_types": ["fire"],
            "min_severity": "naranja",
            "target_node_types": ["fire_station", "hospital"],
        })
        assert resp.status_code == 201
        assert resp.json()["name"] == "Fire Alert Policy"
        assert resp.json()["is_dry_run"] is True

    def test_get_policy(self):
        """Get a single policy."""
        pid = _uid()
        client.post("/api/alert-policies", json={
            "id": pid, "name": "Test Policy",
        })
        resp = client.get(f"/api/alert-policies/{pid}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Test Policy"

    def test_get_policy_not_found(self):
        """Non-existent policy returns 404."""
        resp = client.get("/api/alert-policies/nonexistent")
        assert resp.status_code == 404

    def test_list_policies(self):
        """List policies."""
        pid = _uid()
        client.post("/api/alert-policies", json={"id": pid, "name": "List Me"})
        resp = client.get("/api/alert-policies")
        assert resp.status_code == 200
        assert resp.json()["count"] >= 1


class TestPolicyEvaluation:
    def test_dry_run_no_notifications(self):
        """Dry-run policy computes eligible nodes but sends 0 notifications."""
        pid = _uid()
        # Create a fire station node
        nid = _uid()
        client.post("/api/nodes", json={
            "id": nid, "node_type": "fire_station", "name": "FS1",
            "lat": 40.4168, "lon": -3.7038,
        })
        # Create policy
        client.post("/api/alert-policies", json={
            "id": pid, "name": "Fire Policy",
            "hazard_types": ["fire"],
            "min_severity": "amarilla",
            "target_node_types": ["fire_station"],
            "is_dry_run": True,
        })
        # Get the node's H3 cell
        node = client.get(f"/api/nodes/{nid}").json()
        h3_cell = node["h3_index"]

        resp = client.post(f"/api/alert-policies/{pid}/evaluate", json={
            "hazard_type": "fire",
            "severity": "naranja",
            "action_area_h3_cells": [h3_cell],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["eligible_count"] >= 1
        assert data["notifications_sent"] == 0
        assert data["is_dry_run"] is True

    def test_hazard_type_mismatch(self):
        """Policy doesn't match different hazard type."""
        pid = _uid()
        client.post("/api/alert-policies", json={
            "id": pid, "name": "Fire Only",
            "hazard_types": ["fire"],
            "is_dry_run": True,
        })
        resp = client.post(f"/api/alert-policies/{pid}/evaluate", json={
            "hazard_type": "earthquake",
        })
        assert resp.status_code == 200
        assert resp.json()["reason"] == "hazard_type_mismatch"

    def test_severity_below_threshold(self):
        """Severity below policy threshold."""
        pid = _uid()
        client.post("/api/alert-policies", json={
            "id": pid, "name": "High Severity Only",
            "min_severity": "roja",
            "is_dry_run": True,
        })
        resp = client.post(f"/api/alert-policies/{pid}/evaluate", json={
            "hazard_type": "fire",
            "severity": "amarilla",
        })
        assert resp.status_code == 200
        assert resp.json()["reason"] == "severity_below_threshold"

    def test_risk_score_below_threshold(self):
        """Risk score below policy threshold."""
        pid = _uid()
        client.post("/api/alert-policies", json={
            "id": pid, "name": "High Risk Only",
            "min_risk_score": 0.8,
            "is_dry_run": True,
        })
        resp = client.post(f"/api/alert-policies/{pid}/evaluate", json={
            "hazard_type": "fire",
            "severity_float": 0.3,
        })
        assert resp.status_code == 200
        assert resp.json()["reason"] == "risk_below_threshold"

    def test_evaluations_stored(self):
        """Evaluations are stored and retrievable."""
        pid = _uid()
        client.post("/api/alert-policies", json={
            "id": pid, "name": "Store Evals",
            "is_dry_run": True,
        })
        client.post(f"/api/alert-policies/{pid}/evaluate", json={
            "hazard_type": "fire",
        })
        resp = client.get(f"/api/alert-policies/{pid}/evaluations")
        assert resp.status_code == 200
        assert resp.json()["count"] >= 1
