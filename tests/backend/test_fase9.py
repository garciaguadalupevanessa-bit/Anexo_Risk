"""Tests for FASE 9 — Network Links.

Tests cover:
- Link CRUD operations
- Link types and statuses
- Auto distance computation
- Node connectivity queries
- Status transitions
"""
import pytest
import sys
import os
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
os.environ.setdefault("TESTING", "true")
os.environ.setdefault("JWT_SECRET_KEY", "test-fase9")
os.environ.setdefault("ANEXO_ADMIN_KEY", "test-fase9")

from fastapi.testclient import TestClient
from main import app
from db.database import init_db

client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    yield


def _uid():
    return "l9_" + uuid.uuid4().hex[:8]


class TestLinkCRUD:
    def test_create_link(self):
        """Create a new network link."""
        lid = _uid()
        resp = client.post("/api/links", json={
            "id": lid,
            "link_type": "road",
            "name": "A-1 Madrid→Burgos",
            "start_lat": 40.4168, "start_lon": -3.7038,
            "end_lat": 42.3439, "end_lon": -3.7038,
            "distance_km": 240,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["id"] == lid
        assert data["link_type"] == "road"
        assert data["h3_start"] is not None
        assert data["h3_end"] is not None

    def test_auto_distance_computed(self):
        """Distance auto-computed from endpoints."""
        lid = _uid()
        resp = client.post("/api/links", json={
            "id": lid, "link_type": "road", "name": "Auto dist",
            "start_lat": 40.4168, "start_lon": -3.7038,
            "end_lat": 41.3874, "end_lon": 2.1686,
        })
        assert resp.status_code == 201
        dist = resp.json()["distance_km"]
        assert 490 < dist < 520  # Madrid→Barcelona ~505km

    def test_get_link(self):
        """Get a single link."""
        lid = _uid()
        client.post("/api/links", json={
            "id": lid, "link_type": "corridor", "name": "Corredor Sur",
            "start_lat": 40.0, "start_lon": -3.5,
            "end_lat": 40.1, "end_lon": -3.4,
        })
        resp = client.get(f"/api/links/{lid}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Corredor Sur"

    def test_get_link_not_found(self):
        """Non-existent link returns 404."""
        resp = client.get("/api/links/nonexistent")
        assert resp.status_code == 404

    def test_update_link_status(self):
        """Update link status."""
        lid = _uid()
        client.post("/api/links", json={
            "id": lid, "link_type": "road", "name": "Test Road",
            "start_lat": 40.0, "start_lon": -3.5,
            "end_lat": 40.1, "end_lon": -3.4,
        })
        resp = client.put(f"/api/links/{lid}", json={"status": "blocked"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "blocked"

    def test_delete_link(self):
        """Soft-delete closes the link."""
        lid = _uid()
        client.post("/api/links", json={
            "id": lid, "link_type": "road", "name": "Delete Me",
            "start_lat": 40.0, "start_lon": -3.5,
            "end_lat": 40.1, "end_lon": -3.4,
        })
        resp = client.delete(f"/api/links/{lid}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "closed"

    def test_list_links(self):
        """List links."""
        lid = _uid()
        client.post("/api/links", json={
            "id": lid, "link_type": "road", "name": "List Me",
            "start_lat": 40.0, "start_lon": -3.5,
            "end_lat": 40.1, "end_lon": -3.4,
        })
        resp = client.get("/api/links?link_type=road")
        assert resp.status_code == 200
        assert resp.json()["count"] >= 1

    def test_count_links(self):
        """Count links."""
        resp = client.get("/api/links/count")
        assert resp.status_code == 200
        assert "count" in resp.json()


class TestLinkNodeConnectivity:
    def test_links_for_node(self):
        """Get links connected to a node."""
        nid1 = _uid()
        nid2 = _uid()
        # Create nodes
        client.post("/api/nodes", json={
            "id": nid1, "node_type": "hospital", "name": "H1",
            "lat": 40.4168, "lon": -3.7038,
        })
        client.post("/api/nodes", json={
            "id": nid2, "node_type": "fire_station", "name": "FS1",
            "lat": 40.5, "lon": -3.6,
        })
        # Create link between them
        lid = _uid()
        client.post("/api/links", json={
            "id": lid, "link_type": "road", "name": "H1→FS1",
            "start_node_id": nid1, "end_node_id": nid2,
            "start_lat": 40.4168, "start_lon": -3.7038,
            "end_lat": 40.5, "end_lon": -3.6,
        })
        resp = client.get(f"/api/links/node/{nid1}")
        assert resp.status_code == 200
        assert resp.json()["count"] >= 1


class TestLinkStatuses:
    def test_link_types(self):
        """All link types work."""
        for lt in ["road", "corridor", "route", "bridge", "tunnel", "evacuation"]:
            lid = _uid()
            resp = client.post("/api/links", json={
                "id": lid, "link_type": lt, "name": f"Link {lt}",
                "start_lat": 40.0, "start_lon": -3.5,
                "end_lat": 40.1, "end_lon": -3.4,
            })
            assert resp.status_code == 201, f"Failed for type {lt}"

    def test_link_statuses(self):
        """All link statuses work."""
        for ls in ["open", "blocked", "restricted", "closed"]:
            lid = _uid()
            resp = client.post("/api/links", json={
                "id": lid, "link_type": "road", "name": f"Link {ls}",
                "start_lat": 40.0, "start_lon": -3.5,
                "end_lat": 40.1, "end_lon": -3.4,
                "status": ls,
            })
            assert resp.status_code == 201, f"Failed for status {ls}"
