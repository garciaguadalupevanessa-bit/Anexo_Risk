"""Tests for FASE 10 — Accessibility/Routing.

Tests cover:
- Path finding between nodes
- Reachability through open links
- Blocked routes excluded by default
- Batch accessibility
- Blocked routes listing
"""
import pytest
import sys
import os
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
os.environ.setdefault("TESTING", "true")
os.environ.setdefault("JWT_SECRET_KEY", "test-fase10")
os.environ.setdefault("ANEXO_ADMIN_KEY", "test-fase10")

from fastapi.testclient import TestClient
from main import app
from db.database import init_db

client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    yield


def _uid():
    return "a10_" + uuid.uuid4().hex[:8]


def _create_triangle():
    """Create 3 nodes connected in a triangle: A-B-C-A."""
    nid_a = _uid()
    nid_b = _uid()
    nid_c = _uid()
    for nid, name, lat, lon in [
        (nid_a, "NodeA", 40.0, -3.0),
        (nid_b, "NodeB", 40.1, -3.1),
        (nid_c, "NodeC", 40.2, -3.2),
    ]:
        client.post("/api/nodes", json={
            "id": nid, "node_type": "hospital", "name": name,
            "lat": lat, "lon": lon,
        })
    # Links: A-B, B-C, A-C
    for s, e, name, dist in [
        (nid_a, nid_b, "A-B", 15.0),
        (nid_b, nid_c, "B-C", 15.0),
        (nid_a, nid_c, "A-C", 30.0),
    ]:
        client.post("/api/links", json={
            "link_type": "road", "name": name,
            "start_node_id": s, "end_node_id": e,
            "start_lat": 40.0, "start_lon": -3.0,
            "end_lat": 40.1, "end_lon": -3.1,
            "distance_km": dist,
            "estimated_time_min": dist * 0.5,
        })
    return nid_a, nid_b, nid_c


class TestPathFinding:
    def test_direct_path(self):
        """Direct path between connected nodes."""
        nid_a, nid_b, nid_c = _create_triangle()
        resp = client.get(f"/api/accessibility/path?origin={nid_a}&destination={nid_b}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_reachable"] is True
        assert data["shortest_distance_km"] == 15.0
        assert data["hops"] == 1

    def test_indirect_path(self):
        """Path through intermediate node."""
        nid_a, nid_b, nid_c = _create_triangle()
        resp = client.get(f"/api/accessibility/path?origin={nid_a}&destination={nid_c}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_reachable"] is True
        # Should prefer A-C direct (30km) over A-B-C (30km)
        assert data["shortest_distance_km"] <= 30.0

    def test_same_node(self):
        """Same origin and destination."""
        nid_a, _, _ = _create_triangle()
        resp = client.get(f"/api/accessibility/path?origin={nid_a}&destination={nid_a}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_reachable"] is True
        assert data["shortest_distance_km"] == 0.0
        assert data["hops"] == 0

    def test_unreachable_node(self):
        """Node with no connections is unreachable."""
        nid_a, _, _ = _create_triangle()
        nid_orphan = _uid()
        client.post("/api/nodes", json={
            "id": nid_orphan, "node_type": "shelter", "name": "Orphan",
            "lat": 50.0, "lon": 10.0,
        })
        resp = client.get(f"/api/accessibility/path?origin={nid_a}&destination={nid_orphan}")
        assert resp.status_code == 200
        assert resp.json()["is_reachable"] is False


class TestBlockedRoutes:
    def test_blocked_excluded_by_default(self):
        """Blocked links are excluded from path finding."""
        nid_a, nid_b, nid_c = _create_triangle()
        # Block the direct A-C link
        links = client.get(f"/api/links/node/{nid_a}").json()["links"]
        ac_link = [l for l in links if l["name"] == "A-C"][0]
        client.put(f"/api/links/{ac_link['id']}", json={"status": "blocked"})
        # A→C should now go A→B→C
        resp = client.get(f"/api/accessibility/path?origin={nid_a}&destination={nid_c}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_reachable"] is True
        assert data["shortest_distance_km"] == 30.0  # A-B (15) + B-C (15)

    def test_blocked_included_when_flagged(self):
        """Blocked links included when include_blocked=True."""
        nid_a, nid_b, nid_c = _create_triangle()
        links = client.get(f"/api/links/node/{nid_a}").json()["links"]
        ac_link = [l for l in links if l["name"] == "A-C"][0]
        client.put(f"/api/links/{ac_link['id']}", json={"status": "blocked"})
        resp = client.get(f"/api/accessibility/path?origin={nid_a}&destination={nid_c}&include_blocked=true")
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_reachable"] is True
        assert data["shortest_distance_km"] == 30.0  # A-C direct still 30

    def test_get_blocked_routes(self):
        """List blocked routes."""
        nid_a, nid_b, _ = _create_triangle()
        links = client.get(f"/api/links/node/{nid_a}").json()["links"]
        client.put(f"/api/links/{links[0]['id']}", json={"status": "blocked"})
        resp = client.get("/api/accessibility/blocked")
        assert resp.status_code == 200
        assert resp.json()["count"] >= 1


class TestBatchAccessibility:
    def test_batch_check(self):
        """Batch accessibility check."""
        nid_a, nid_b, nid_c = _create_triangle()
        resp = client.post("/api/accessibility/batch", json={
            "origin_ids": [nid_a],
            "destination_ids": [nid_b, nid_c],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 2
        assert all(r["is_reachable"] for r in data["results"])
