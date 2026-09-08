"""Tests for FASE 7 — H3 Operational Mesh.

Tests cover:
- H3 indexing of events
- Region → H3 cell conversion
- Per-cell aggregation
- Spatial queries (bbox, radius)
- Coverage metric
- Existing H3 endpoints unchanged
"""
import pytest
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
os.environ.setdefault("TESTING", "true")
os.environ.setdefault("JWT_SECRET_KEY", "test-fase7")
os.environ.setdefault("ANEXO_ADMIN_KEY", "test-fase7")

from fastapi.testclient import TestClient
from main import app
from db.database import get_cursor, init_db

client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    yield


@pytest.fixture
def seed_events():
    """Insert test events with various coordinates."""
    now = datetime.utcnow().isoformat()
    events = [
        ("h3_evt_1", "firms", "fire", "Fire near Madrid", now, 40.4168, -3.7038, "naranja", 0.75, "ES"),
        ("h3_evt_2", "firms", "fire", "Fire near Toledo", now, 39.8628, -4.0273, "amarilla", 0.5, "ES"),
        ("h3_evt_3", "usgs", "earthquake", "Quake SE Spain", now, 37.9870, -1.1300, "roja", 1.0, "ES"),
        ("h3_evt_4", "aemet", "weather", "Storm Bilbao", now, 43.2630, -2.9350, "amarilla", 0.5, "ES"),
    ]
    with get_cursor() as cur:
        for e in events:
            cur.execute(
                """INSERT OR REPLACE INTO normalized_events
                (id, source, entity_type, title, timestamp, lat, lon,
                 severity, severity_float, country, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)""",
                (e[0], e[1], e[2], e[3], e[4], e[5], e[6], e[7], e[8], e[9]),
            )
    return events


class TestH3Indexing:
    def test_event_has_h3_index(self, seed_events):
        """AC1: Events get h3_index when geolocalized."""
        from services.h3_mesh import index_event
        h3_idx = index_event("h3_evt_1", 40.4168, -3.7038, 3)
        assert h3_idx is not None
        assert len(h3_idx) > 0
        with get_cursor() as cur:
            row = cur.execute(
                "SELECT h3_index FROM normalized_events WHERE id = 'h3_evt_1'"
            ).fetchone()
            assert row["h3_index"] == h3_idx

    def test_index_event_invalid_coords(self):
        """Invalid coordinates return None."""
        from services.h3_mesh import index_event
        result = index_event("bad", 999.0, -999.0, 3)
        assert result is None


class TestRegionToH3:
    def test_bbox_to_cells(self):
        """AC2: Region bbox converts to H3 cells."""
        from services.h3_mesh import region_to_h3_cells
        cells = region_to_h3_cells(
            bbox={"min_lat": 37.0, "min_lon": -5.0, "max_lat": 44.0, "max_lon": 4.0},
            resolution=3,
        )
        assert len(cells) > 0
        assert all(isinstance(c, str) for c in cells)

    def test_center_radius_to_cells(self):
        """Center+radius produces H3 cells."""
        from services.h3_mesh import region_to_h3_cells
        cells = region_to_h3_cells(center_lat=40.0, center_lon=-3.7, radius_km=100, resolution=3)
        assert len(cells) > 0

    def test_invalid_bbox_returns_empty(self):
        """Invalid bbox returns empty list."""
        from services.h3_mesh import region_to_h3_cells
        cells = region_to_h3_cells(bbox={"min_lat": None, "min_lon": None, "max_lat": None, "max_lon": None}, resolution=3)
        assert cells == []


class TestCellAggregation:
    def test_aggregate_cell_with_events(self, seed_events):
        """AC3: Per-cell aggregation returns counts."""
        from services.h3_mesh import index_event, aggregate_cell
        h3_idx = index_event("h3_evt_1", 40.4168, -3.7038, 3)
        assert h3_idx is not None
        cell = aggregate_cell(h3_idx, 3)
        assert cell["h3_index"] == h3_idx
        assert cell["event_count"] >= 1
        assert cell["avg_severity"] > 0
        assert "fire" in cell["entity_types"]
        assert "firms" in cell["sources"]

    def test_aggregate_empty_cell(self):
        """Empty cell returns zero counts."""
        from services.h3_mesh import aggregate_cell
        from geodata.services.h3_resolver import latlon_to_h3
        # Use coordinates far from any test event
        h3_idx = latlon_to_h3(-33.8688, 151.2093, 3)  # Sydney
        cell = aggregate_cell(h3_idx, 3)
        assert cell["event_count"] == 0


class TestSpatialQueries:
    def test_cells_in_bbox_returns_aggregated(self, seed_events):
        """AC5: Spatial query (bbox) returns relevant cells with data."""
        from services.h3_mesh import index_event, cells_in_bbox
        index_event("h3_evt_1", 40.4168, -3.7038, 3)
        index_event("h3_evt_2", 39.8628, -4.0273, 3)
        cells = cells_in_bbox(38.0, -6.0, 42.0, 0.0, 3)
        assert len(cells) >= 1
        total_events = sum(c["event_count"] for c in cells)
        assert total_events >= 2

    def test_cells_in_radius(self, seed_events):
        """Cells within radius returns relevant cells."""
        from services.h3_mesh import index_event, cells_in_radius
        index_event("h3_evt_1", 40.4168, -3.7038, 3)
        cells = cells_in_radius(40.4168, -3.7038, 50, 3)
        assert len(cells) >= 1

    def test_single_cell_detail(self, seed_events):
        """Single cell detail endpoint."""
        from services.h3_mesh import index_event, aggregate_cell
        h3_idx = index_event("h3_evt_1", 40.4168, -3.7038, 3)
        cell = aggregate_cell(h3_idx, 3)
        assert cell["center_lat"] is not None
        assert cell["center_lon"] is not None


class TestCoverage:
    def test_coverage_metric(self, seed_events):
        """AC7: Operational coverage metric calculable."""
        from services.h3_mesh import index_event, operational_coverage
        index_event("h3_evt_1", 40.4168, -3.7038, 3)
        index_event("h3_evt_2", 39.8628, -4.0273, 3)
        cov = operational_coverage(
            region_bbox={"min_lat": 38.0, "min_lon": -6.0, "max_lat": 42.0, "max_lon": 0.0},
            resolution=3,
        )
        assert cov["total_cells"] > 0
        assert cov["covered_cells"] >= 1
        assert 0.0 < cov["coverage_ratio"] <= 1.0

    def test_coverage_empty_region(self):
        """Coverage for region with no data returns zeros."""
        from services.h3_mesh import operational_coverage
        cov = operational_coverage(
            region_bbox={"min_lat": -35.0, "min_lon": 149.0, "max_lat": -33.0, "max_lon": 152.0},
            resolution=3,
        )
        assert cov["total_cells"] > 0
        assert cov["covered_cells"] == 0
        assert cov["coverage_ratio"] == 0.0


class TestH3APIEndpoints:
    def test_get_cells_bbox(self, seed_events):
        """GET /api/h3/cells returns cells in bbox."""
        from services.h3_mesh import index_event
        index_event("h3_evt_1", 40.4168, -3.7038, 3)
        resp = client.get("/api/h3/cells?min_lat=38&min_lon=-6&max_lat=42&max_lon=0&resolution=3")
        assert resp.status_code == 200
        data = resp.json()
        assert "cells" in data
        assert data["resolution"] == 3

    def test_get_cells_radius(self, seed_events):
        """GET /api/h3/cells/radius returns cells in radius."""
        from services.h3_mesh import index_event
        index_event("h3_evt_1", 40.4168, -3.7038, 3)
        resp = client.get("/api/h3/cells/radius?center_lat=40.4&center_lon=-3.7&radius_km=50&resolution=3")
        assert resp.status_code == 200
        data = resp.json()
        assert "cells" in data

    def test_get_coverage(self, seed_events):
        """GET /api/h3/coverage returns coverage metrics."""
        from services.h3_mesh import index_event
        index_event("h3_evt_1", 40.4168, -3.7038, 3)
        resp = client.get("/api/h3/coverage?min_lat=38&min_lon=-6&max_lat=42&max_lon=0&resolution=3")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_cells" in data
        assert "coverage_ratio" in data

    def test_get_region_cells(self, seed_events):
        """GET /api/h3/region/{id} returns cells for a region."""
        from modules.regiones import models as rm
        import uuid
        region_id = "h3_test_" + uuid.uuid4().hex[:8]
        region = rm.create_region({
            "id": region_id,
            "name": "H3 Test Region",
            "level": "municipality",
            "country_code": "ES",
            "h3_resolution": 3,
            "center_lat": 40.4168,
            "center_lon": -3.7038,
            "radius_km": 100,
        })
        resp = client.get(f"/api/h3/region/{region_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["region_id"] == region_id
        assert data["total_cells"] >= 0
