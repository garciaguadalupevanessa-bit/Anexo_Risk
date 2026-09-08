"""Tests for Source Registry module."""
import sys
import os
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
os.environ.setdefault("TESTING", "true")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-sources")
os.environ.setdefault("ANEXO_ADMIN_KEY", "test-admin-key-for-sources")

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app, raise_server_exceptions=False)


def _uid():
    return "src_" + uuid.uuid4().hex[:8]


class TestSourceRegistryAPI:
    """Test Source Registry REST endpoints."""

    def test_register_source(self):
        sid = _uid()
        r = client.post("/api/sources", json={
            "id": sid,
            "name": "Test Source",
            "scope": "global",
            "data_types": ["earthquake"],
            "supports_point": True,
        })
        assert r.status_code == 201
        d = r.json()
        assert d["id"] == sid
        assert d["name"] == "Test Source"
        assert d["scope"] == "global"
        assert d["data_types"] == ["earthquake"]
        assert d["supports_point"] is True

    def test_register_duplicate(self):
        sid = _uid()
        client.post("/api/sources", json={"id": sid, "name": "First"})
        r = client.post("/api/sources", json={"id": sid, "name": "Duplicate"})
        assert r.status_code == 409

    def test_get_source(self):
        sid = _uid()
        client.post("/api/sources", json={"id": sid, "name": "Get Me"})
        r = client.get(f"/api/sources/{sid}")
        assert r.status_code == 200
        assert r.json()["id"] == sid

    def test_get_source_not_found(self):
        r = client.get("/api/sources/nonexistent")
        assert r.status_code == 404

    def test_list_sources(self):
        sid = _uid()
        client.post("/api/sources", json={"id": sid, "name": "List Me"})
        r = client.get("/api/sources")
        assert r.status_code == 200
        ids = [s["id"] for s in r.json()]
        assert sid in ids

    def test_list_sources_filter_scope(self):
        sid = _uid()
        client.post("/api/sources", json={"id": sid, "name": "Global", "scope": "global"})
        r = client.get("/api/sources?scope=global")
        ids = [s["id"] for s in r.json()]
        assert sid in ids

    def test_update_source(self):
        sid = _uid()
        client.post("/api/sources", json={"id": sid, "name": "Original"})
        r = client.patch(f"/api/sources/{sid}", json={"name": "Updated"})
        assert r.status_code == 200
        assert r.json()["name"] == "Updated"

    def test_delete_source(self):
        sid = _uid()
        client.post("/api/sources", json={"id": sid, "name": "To Delete"})
        r = client.delete(f"/api/sources/{sid}")
        assert r.status_code == 200
        r = client.get(f"/api/sources/{sid}")
        assert r.status_code == 404

    def test_health_summary(self):
        r = client.get("/api/sources/health")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_update_status(self):
        sid = _uid()
        client.post("/api/sources", json={"id": sid, "name": "Status Test"})
        r = client.post(f"/api/sources/{sid}/status?status=active&latency_ms=150")
        assert r.status_code == 200
        assert r.json()["latency_ms"] == 150.0
        assert r.json()["last_successful_fetch"] is not None

    def test_update_status_error(self):
        sid = _uid()
        client.post("/api/sources", json={"id": sid, "name": "Error Test"})
        r = client.post(f"/api/sources/{sid}/status?status=degraded&error=timeout")
        assert r.status_code == 200
        assert r.json()["status"] == "degraded"
        assert r.json()["last_error"] == "timeout"


class TestSourceRegistryModels:
    """Test source registry data models."""

    def test_register_and_get(self):
        from modules.source_registry import models
        sid = _uid()
        s = models.register_source({"id": sid, "name": "Model Test", "scope": "global"})
        assert s["id"] == sid
        got = models.get_source(sid)
        assert got["name"] == "Model Test"
        models.delete_source(sid)

    def test_health_summary(self):
        from modules.source_registry import models
        summary = models.get_source_health_summary()
        assert isinstance(summary, list)
