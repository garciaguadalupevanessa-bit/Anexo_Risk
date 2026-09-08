"""Tests for FASE 11 — Dynamic Action Area.

Tests cover:
- Action area computation by hazard type
- Severity radius adjustment
- Store and retrieve action areas
- H3 cell coverage
- Multiple action areas per incident
"""
import pytest
import sys
import os
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
os.environ.setdefault("TESTING", "true")
os.environ.setdefault("JWT_SECRET_KEY", "test-fase11")
os.environ.setdefault("ANEXO_ADMIN_KEY", "test-fase11")

from fastapi.testclient import TestClient
from main import app
from db.database import init_db

client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    yield


class TestActionAreaComputation:
    def test_fire_area_radius(self):
        """Fire hazard has ~25km base radius."""
        resp = client.post("/api/action-areas/compute", json={
            "lat": 40.4168, "lon": -3.7038, "hazard_type": "fire",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["hazard_type"] == "fire"
        assert data["radius_km"] == 25.0
        assert len(data["h3_cells"]) > 0
        assert data["h3_center"] is not None

    def test_earthquake_area_radius(self):
        """Earthquake has ~100km base radius."""
        resp = client.post("/api/action-areas/compute", json={
            "lat": 37.9870, "lon": -1.1300, "hazard_type": "earthquake",
        })
        assert resp.status_code == 200
        assert resp.json()["radius_km"] == 100.0

    def test_severity_adjusts_radius(self):
        """Severity multiplies the base radius."""
        resp_green = client.post("/api/action-areas/compute", json={
            "lat": 40.0, "lon": -3.5, "hazard_type": "fire", "severity": "verde",
        })
        resp_red = client.post("/api/action-areas/compute", json={
            "lat": 40.0, "lon": -3.5, "hazard_type": "fire", "severity": "roja",
        })
        assert resp_green.json()["radius_km"] < resp_red.json()["radius_km"]

    def test_severity_float_adjusts_radius(self):
        """Severity float adjusts radius proportionally."""
        resp_low = client.post("/api/action-areas/compute", json={
            "lat": 40.0, "lon": -3.5, "hazard_type": "fire", "severity_float": 0.2,
        })
        resp_high = client.post("/api/action-areas/compute", json={
            "lat": 40.0, "lon": -3.5, "hazard_type": "fire", "severity_float": 0.9,
        })
        assert resp_low.json()["radius_km"] < resp_high.json()["radius_km"]

    def test_custom_radius(self):
        """Custom radius overrides default."""
        resp = client.post("/api/action-areas/compute", json={
            "lat": 40.0, "lon": -3.5, "hazard_type": "fire", "custom_radius_km": 5.0,
        })
        assert resp.json()["radius_km"] == 5.0


class TestActionAreaStorage:
    def test_store_and_retrieve(self):
        """Store action area and retrieve by incident."""
        inc_id = "inc_" + uuid.uuid4().hex[:8]
        resp = client.post("/api/action-areas", json={
            "incident_id": inc_id, "lat": 40.4168, "lon": -3.7038,
            "hazard_type": "fire", "severity": "naranja",
        })
        assert resp.status_code == 201
        area_id = resp.json()["id"]

        resp = client.get(f"/api/action-areas/incident/{inc_id}")
        assert resp.status_code == 200
        assert resp.json()["count"] == 1
        assert resp.json()["areas"][0]["id"] == area_id

    def test_multiple_areas_per_incident(self):
        """Multiple action areas for one incident."""
        inc_id = "inc_" + uuid.uuid4().hex[:8]
        for ht in ["fire", "flood"]:
            client.post("/api/action-areas", json={
                "incident_id": inc_id, "lat": 40.4168, "lon": -3.7038,
                "hazard_type": ht,
            })
        resp = client.get(f"/api/action-areas/incident/{inc_id}")
        assert resp.json()["count"] == 2


class TestActionAreaH3:
    def test_h3_cells_cover_center(self):
        """H3 cells include the center cell."""
        resp = client.post("/api/action-areas/compute", json={
            "lat": 40.4168, "lon": -3.7038, "hazard_type": "fire",
        })
        data = resp.json()
        assert data["h3_center"] in data["h3_cells"]

    def test_h3_cell_query(self):
        """Query action areas by H3 cell."""
        resp = client.post("/api/action-areas", json={
            "lat": 40.4168, "lon": -3.7038, "hazard_type": "fire",
        })
        h3_center = resp.json()["h3_center"]
        resp = client.get(f"/api/action-areas/h3/{h3_center}")
        assert resp.status_code == 200
        assert resp.json()["count"] >= 1
