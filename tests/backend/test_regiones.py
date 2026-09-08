"""Tests for Region/AOI module."""
import sys
import os
import json
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
os.environ.setdefault("TESTING", "true")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-regions")
os.environ.setdefault("ANEXO_ADMIN_KEY", "test-admin-key-for-regions")

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app, raise_server_exceptions=False)


def _uid():
    """Generate unique test region ID."""
    return "T" + uuid.uuid4().hex[:8]


class TestRegionSchemas:
    """Test region Pydantic schemas."""

    def test_region_create_valid(self):
        from modules.regiones.schemas import RegionCreate
        r = RegionCreate(id="ES-MD", name="Madrid", level="region", country_code="ES")
        assert r.id == "ES-MD"
        assert r.h3_resolution == 3

    def test_region_create_defaults(self):
        from modules.regiones.schemas import RegionCreate
        r = RegionCreate(id="X", name="Test")
        assert r.level == "municipality"
        assert r.is_active is True
        assert r.source == "manual"

    def test_region_update_partial(self):
        from modules.regiones.schemas import RegionUpdate
        u = RegionUpdate(name="Updated")
        d = u.model_dump(exclude_unset=True)
        assert "name" in d
        assert "level" not in d


class TestRegionAPI:
    """Test Region REST endpoints."""

    def test_create_region(self):
        rid = _uid()
        r = client.post("/api/regions", json={
            "id": rid,
            "name": "Test Region",
            "level": "region",
            "country_code": "ES",
            "center_lat": 40.0,
            "center_lon": -3.0,
        })
        assert r.status_code == 201
        d = r.json()
        assert d["id"] == rid
        assert d["name"] == "Test Region"
        assert d["level"] == "region"
        assert d["country_code"] == "ES"
        assert d["is_active"] is True

    def test_create_region_with_geometry(self):
        rid = _uid()
        r = client.post("/api/regions", json={
            "id": rid,
            "name": "Polygon Region",
            "level": "custom",
            "geometry_type": "Polygon",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[-3.5, 40.0], [-3.5, 41.0], [-2.5, 41.0], [-2.5, 40.0], [-3.5, 40.0]]]
            },
        })
        assert r.status_code == 201
        d = r.json()
        assert d["geometry_type"] == "Polygon"
        assert d["geometry"]["type"] == "Polygon"

    def test_create_region_duplicate(self):
        rid = _uid()
        client.post("/api/regions", json={"id": rid, "name": "First"})
        r = client.post("/api/regions", json={"id": rid, "name": "Duplicate"})
        assert r.status_code == 409

    def test_get_region(self):
        rid = _uid()
        client.post("/api/regions", json={"id": rid, "name": "Get Me"})
        r = client.get(f"/api/regions/{rid}")
        assert r.status_code == 200
        assert r.json()["id"] == rid

    def test_get_region_not_found(self):
        r = client.get("/api/regions/NONEXISTENT")
        assert r.status_code == 404

    def test_list_regions(self):
        rid1 = _uid()
        rid2 = _uid()
        client.post("/api/regions", json={"id": rid1, "name": "A"})
        client.post("/api/regions", json={"id": rid2, "name": "B"})
        r = client.get("/api/regions")
        assert r.status_code == 200
        ids = [reg["id"] for reg in r.json()]
        assert rid1 in ids
        assert rid2 in ids

    def test_list_regions_filter_level(self):
        rid1 = _uid()
        rid2 = _uid()
        client.post("/api/regions", json={"id": rid1, "name": "A", "level": "country"})
        client.post("/api/regions", json={"id": rid2, "name": "B", "level": "municipality"})
        r = client.get("/api/regions?level=country")
        ids = [reg["id"] for reg in r.json()]
        assert rid1 in ids
        assert rid2 not in ids

    def test_update_region(self):
        rid = _uid()
        client.post("/api/regions", json={"id": rid, "name": "Original"})
        r = client.patch(f"/api/regions/{rid}", json={"name": "Updated"})
        assert r.status_code == 200
        assert r.json()["name"] == "Updated"

    def test_delete_region(self):
        rid = _uid()
        client.post("/api/regions", json={"id": rid, "name": "To Delete"})
        r = client.delete(f"/api/regions/{rid}")
        assert r.status_code == 200
        assert r.json()["is_active"] is False

    def test_children(self):
        parent = _uid()
        child = _uid()
        client.post("/api/regions", json={"id": parent, "name": "Parent"})
        client.post("/api/regions", json={"id": child, "name": "Child", "parent_id": parent})
        r = client.get(f"/api/regions/{parent}/children")
        assert r.status_code == 200
        assert len(r.json()) == 1
        assert r.json()[0]["id"] == child

    def test_sources(self):
        rid = _uid()
        client.post("/api/regions", json={"id": rid, "name": "With Sources"})
        r = client.post(f"/api/regions/{rid}/sources", json={
            "source_id": "usgs", "is_enabled": True, "priority": 10,
        })
        assert r.status_code == 201
        r = client.get(f"/api/regions/{rid}/sources")
        assert len(r.json()) == 1
        assert r.json()[0]["source_id"] == "usgs"

    def test_remove_source(self):
        rid = _uid()
        client.post("/api/regions", json={"id": rid, "name": "X"})
        client.post(f"/api/regions/{rid}/sources", json={"source_id": "usgs"})
        r = client.delete(f"/api/regions/{rid}/sources/usgs")
        assert r.status_code == 200
        r = client.get(f"/api/regions/{rid}/sources")
        assert len(r.json()) == 0

    def test_active_region(self):
        rid = _uid()
        client.post("/api/regions", json={"id": rid, "name": "Active"})
        r = client.get("/api/regions/active")
        assert r.status_code == 200
        assert r.json()["is_active"] is True


class TestRegionModels:
    """Test region data models directly."""

    def test_create_and_get(self):
        from modules.regiones import models
        rid = _uid()
        r = models.create_region({"id": rid, "name": "Model Test", "level": "municipality"})
        assert r["id"] == rid
        got = models.get_region(rid)
        assert got["name"] == "Model Test"
        models.delete_region(rid)

    def test_update(self):
        from modules.regiones import models
        rid = _uid()
        models.create_region({"id": rid, "name": "Before"})
        updated = models.update_region(rid, {"name": "After"})
        assert updated["name"] == "After"
        models.delete_region(rid)

    def test_region_sources(self):
        from modules.regiones import models
        rid = _uid()
        models.create_region({"id": rid, "name": "Src Test"})
        sources = models.add_region_source(rid, "firms", priority=5)
        assert len(sources) == 1
        assert sources[0]["source_id"] == "firms"
        models.remove_region_source(rid, "firms")
        sources = models.get_region_sources(rid)
        assert len(sources) == 0
        models.delete_region(rid)
