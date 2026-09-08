"""Tests for FASE 8 — Operational Nodes.

Tests cover:
- Node CRUD operations
- Spatial queries (nearby nodes)
- H3 indexing
- Filter by type and capability
- Capacity tracking
"""
import pytest
import sys
import os
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
os.environ.setdefault("TESTING", "true")
os.environ.setdefault("JWT_SECRET_KEY", "test-fase8")
os.environ.setdefault("ANEXO_ADMIN_KEY", "test-fase8")

from fastapi.testclient import TestClient
from main import app
from db.database import get_cursor, init_db

client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    yield


def _uid():
    return "n8_" + uuid.uuid4().hex[:8]


class TestNodeCRUD:
    def test_create_node(self):
        """Create a new operational node."""
        nid = _uid()
        resp = client.post("/api/nodes", json={
            "id": nid,
            "node_type": "hospital",
            "name": "Hospital General",
            "lat": 40.4168,
            "lon": -3.7038,
            "capacity": 200,
            "country_code": "ES",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["id"] == nid
        assert data["node_type"] == "hospital"
        assert data["capacity"] == 200
        assert data["h3_index"] is not None

    def test_get_node(self):
        """Get a single node by ID."""
        nid = _uid()
        client.post("/api/nodes", json={
            "id": nid, "node_type": "fire_station", "name": "Cuartel Madrid",
            "lat": 40.4168, "lon": -3.7038,
        })
        resp = client.get(f"/api/nodes/{nid}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Cuartel Madrid"

    def test_get_node_not_found(self):
        """Non-existent node returns 404."""
        resp = client.get("/api/nodes/nonexistent")
        assert resp.status_code == 404

    def test_update_node(self):
        """Update node fields."""
        nid = _uid()
        client.post("/api/nodes", json={
            "id": nid, "node_type": "shelter", "name": "Albergue Temp",
            "lat": 40.0, "lon": -3.5, "capacity": 100,
        })
        resp = client.put(f"/api/nodes/{nid}", json={"capacity": 200, "name": "Albergue Actualizado"})
        assert resp.status_code == 200
        assert resp.json()["capacity"] == 200
        assert resp.json()["name"] == "Albergue Actualizado"

    def test_delete_node(self):
        """Soft-delete a node."""
        nid = _uid()
        client.post("/api/nodes", json={
            "id": nid, "node_type": "warehouse", "name": "Almacen",
            "lat": 40.0, "lon": -3.5,
        })
        resp = client.delete(f"/api/nodes/{nid}")
        assert resp.status_code == 200
        # Verify soft-deleted
        resp = client.get(f"/api/nodes/{nid}")
        assert resp.status_code == 404

    def test_list_nodes(self):
        """List nodes with filters."""
        nid = _uid()
        client.post("/api/nodes", json={
            "id": nid, "node_type": "fire_station", "name": "Cuerpo Bomberos",
            "lat": 40.0, "lon": -3.5, "country_code": "ES",
        })
        resp = client.get("/api/nodes?node_type=fire_station")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 1

    def test_count_nodes(self):
        """Count nodes."""
        resp = client.get("/api/nodes/count")
        assert resp.status_code == 200
        assert "count" in resp.json()


class TestNodeSpatial:
    def test_nearby_nodes(self):
        """AC2: Spatial query returns nearby nodes."""
        nid1 = _uid()
        nid2 = _uid()
        client.post("/api/nodes", json={
            "id": nid1, "node_type": "hospital", "name": "H1",
            "lat": 40.4168, "lon": -3.7038,
        })
        client.post("/api/nodes", json={
            "id": nid2, "node_type": "hospital", "name": "H2",
            "lat": 40.5, "lon": -3.6,
        })
        resp = client.get("/api/nodes/nearby?lat=40.4168&lon=-3.7038&radius_km=20")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 1

    def test_nearby_filter_type(self):
        """Filter nearby by node type."""
        nid = _uid()
        client.post("/api/nodes", json={
            "id": nid, "node_type": "fire_station", "name": "FS1",
            "lat": -33.8688, "lon": 151.2093,  # Sydney — no other test data here
        })
        resp = client.get("/api/nodes/nearby?lat=-33.8688&lon=151.2093&radius_km=10&node_type=hospital")
        assert resp.status_code == 200
        assert resp.json()["count"] == 0


class TestNodeH3:
    def test_node_auto_h3_indexed(self):
        """AC3: Nodes get H3 index on creation."""
        nid = _uid()
        resp = client.post("/api/nodes", json={
            "id": nid, "node_type": "command_post", "name": "CP1",
            "lat": 40.4168, "lon": -3.7038,
        })
        assert resp.status_code == 201
        assert resp.json()["h3_index"] is not None
        assert len(resp.json()["h3_index"]) > 0


class TestNodeCapabilities:
    def test_create_with_capabilities(self):
        """AC4: Nodes with capabilities."""
        nid = _uid()
        resp = client.post("/api/nodes", json={
            "id": nid, "node_type": "hospital", "name": "Hospital UCIs",
            "lat": 40.4168, "lon": -3.7038,
            "capabilities": ["icu", "surgery", "emergency"],
        })
        assert resp.status_code == 201
        assert resp.json()["capabilities"] == ["icu", "surgery", "emergency"]

    def test_create_with_capacity(self):
        """AC5: Capacity tracking."""
        nid = _uid()
        resp = client.post("/api/nodes", json={
            "id": nid, "node_type": "shelter", "name": "Albergue Grande",
            "lat": 40.4168, "lon": -3.7038,
            "capacity": 500, "current_occupancy": 120,
        })
        assert resp.status_code == 201
        assert resp.json()["capacity"] == 500
        assert resp.json()["current_occupancy"] == 120
