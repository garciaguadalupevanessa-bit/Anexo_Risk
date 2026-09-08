"""Tests for FASE 13 — Federated Organizations.

Tests cover:
- Region access grants
- Access level checking
- Orgs in region queries
- Access revocation
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
os.environ.setdefault("TESTING", "true")
os.environ.setdefault("JWT_SECRET_KEY", "test-fase13")
os.environ.setdefault("ANEXO_ADMIN_KEY", "test-fase13")

from fastapi.testclient import TestClient
from main import app
from db.database import init_db

client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    yield


@pytest.fixture
def org_id():
    """Create a test organization."""
    resp = client.post("/api/organizations", json={
        "name": "Test Org F13",
        "type": "emergency_services",
        "region": "Madrid",
    }, headers={"X-Admin-Key": os.environ["ANEXO_ADMIN_KEY"]})
    if resp.status_code == 201:
        return resp.json()["id"]
    # Fallback: use existing org
    resp = client.get("/api/organizations")
    orgs = resp.json()
    if orgs:
        return orgs[0]["id"]
    return None


class TestRegionAccess:
    def test_grant_region_access(self, org_id):
        """Grant organization access to a region."""
        if not org_id:
            pytest.skip("No org available")
        resp = client.post(f"/api/organizations/{org_id}/region-access", json={
            "region_id": "madrid centro",
            "access_level": "read",
        })
        assert resp.status_code == 200
        assert resp.json()["access_level"] == "read"

    def test_check_region_access(self, org_id):
        """Check organization has access to a region."""
        if not org_id:
            pytest.skip("No org available")
        client.post(f"/api/organizations/{org_id}/region-access", json={
            "region_id": "test_region",
            "access_level": "write",
        })
        resp = client.get(f"/api/organizations/{org_id}/check-access/test_region?level=read")
        assert resp.status_code == 200
        assert resp.json()["has_access"] is True

    def test_check_no_access(self, org_id):
        """Check organization has no access to ungranted region."""
        if not org_id:
            pytest.skip("No org available")
        resp = client.get(f"/api/organizations/{org_id}/check-access/ungranted_region")
        assert resp.status_code == 200
        assert resp.json()["has_access"] is False

    def test_revoke_region_access(self, org_id):
        """Revoke organization access."""
        if not org_id:
            pytest.skip("No org available")
        client.post(f"/api/organizations/{org_id}/region-access", json={
            "region_id": "revoke_me",
            "access_level": "read",
        })
        resp = client.delete(f"/api/organizations/{org_id}/region-access/revoke_me")
        assert resp.status_code == 200
        assert resp.json()["revoked"] is True
        # Verify revoked
        resp = client.get(f"/api/organizations/{org_id}/check-access/revoke_me")
        assert resp.json()["has_access"] is False

    def test_get_org_access_grants(self, org_id):
        """Get all access grants for an organization."""
        if not org_id:
            pytest.skip("No org available")
        client.post(f"/api/organizations/{org_id}/region-access", json={
            "region_id": "region_a",
            "access_level": "read",
        })
        resp = client.get(f"/api/organizations/{org_id}/region-access")
        assert resp.status_code == 200
        assert len(resp.json()["grants"]) >= 1

    def test_orgs_in_region(self, org_id):
        """Get organizations in a region."""
        if not org_id:
            pytest.skip("No org available")
        client.post(f"/api/organizations/{org_id}/region-access", json={
            "region_id": "shared_region",
            "access_level": "read",
        })
        resp = client.get("/api/organizations/region/shared_region")
        assert resp.status_code == 200
        assert resp.json()["count"] >= 1


class TestAccessLevels:
    def test_read_does_not_grant_write(self, org_id):
        """Read access doesn't satisfy write requirement."""
        if not org_id:
            pytest.skip("No org available")
        client.post(f"/api/organizations/{org_id}/region-access", json={
            "region_id": "level_test",
            "access_level": "read",
        })
        resp = client.get(f"/api/organizations/{org_id}/check-access/level_test?level=write")
        assert resp.json()["has_access"] is False

    def test_admin_grants_read(self, org_id):
        """Admin access satisfies read requirement."""
        if not org_id:
            pytest.skip("No org available")
        client.post(f"/api/organizations/{org_id}/region-access", json={
            "region_id": "admin_test",
            "access_level": "admin",
        })
        resp = client.get(f"/api/organizations/{org_id}/check-access/admin_test?level=read")
        assert resp.json()["has_access"] is True
