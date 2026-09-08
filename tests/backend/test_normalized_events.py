"""Tests for Normalized Events module."""
import sys
import os
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
os.environ.setdefault("TESTING", "true")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-events")
os.environ.setdefault("ANEXO_ADMIN_KEY", "test-admin-key-for-events")

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app, raise_server_exceptions=False)


def _uid():
    return "evt_" + uuid.uuid4().hex[:8]


class TestNormalizedEventsAPI:
    """Test Normalized Events REST endpoints."""

    def test_create_event(self):
        eid = _uid()
        r = client.post("/api/events", json={
            "id": eid,
            "entity_type": "earthquake",
            "source": "usgs",
            "title": "M5.2 Earthquake",
            "lat": 37.17,
            "lon": -3.60,
            "magnitude": 5.2,
            "severity": "naranja",
            "severity_float": 0.75,
        })
        assert r.status_code == 201
        d = r.json()
        assert d["id"] == eid
        assert d["entity_type"] == "earthquake"
        assert d["source"] == "usgs"
        assert d["magnitude"] == 5.2

    def test_create_event_minimal(self):
        r = client.post("/api/events", json={
            "entity_type": "fire",
            "source": "firms",
            "title": "Fire detection",
        })
        assert r.status_code == 201
        assert r.json()["is_active"] is True

    def test_get_event(self):
        eid = _uid()
        client.post("/api/events", json={
            "id": eid, "entity_type": "alert", "source": "gdacs", "title": "Test",
        })
        r = client.get(f"/api/events/{eid}")
        assert r.status_code == 200
        assert r.json()["id"] == eid

    def test_get_event_not_found(self):
        r = client.get("/api/events/nonexistent")
        assert r.status_code == 404

    def test_list_events(self):
        eid = _uid()
        client.post("/api/events", json={
            "id": eid, "entity_type": "earthquake", "source": "usgs", "title": "List me",
        })
        r = client.get("/api/events")
        assert r.status_code == 200
        ids = [e["id"] for e in r.json()]
        assert eid in ids

    def test_list_events_filter_source(self):
        eid = _uid()
        client.post("/api/events", json={
            "id": eid, "entity_type": "earthquake", "source": "usgs", "title": "USGS",
        })
        r = client.get("/api/events?source=usgs")
        ids = [e["id"] for e in r.json()]
        assert eid in ids

    def test_list_events_filter_entity(self):
        eid = _uid()
        client.post("/api/events", json={
            "id": eid, "entity_type": "fire", "source": "firms", "title": "Fire",
        })
        r = client.get("/api/events?entity_type=fire")
        ids = [e["id"] for e in r.json()]
        assert eid in ids

    def test_batch_create(self):
        r = client.post("/api/events/batch", json={
            "events": [
                {"entity_type": "earthquake", "source": "usgs", "title": "EQ1"},
                {"entity_type": "fire", "source": "firms", "title": "FIRE1"},
            ]
        })
        assert r.status_code == 201
        assert r.json()["stored"] == 2
        assert r.json()["total"] == 2

    def test_deactivate_event(self):
        eid = _uid()
        client.post("/api/events", json={
            "id": eid, "entity_type": "alert", "source": "gdacs", "title": "Deactivate",
        })
        r = client.delete(f"/api/events/{eid}")
        assert r.status_code == 200
        event = client.get(f"/api/events/{eid}").json()
        assert event["is_active"] is False

    def test_count_events(self):
        r = client.get("/api/events/count")
        assert r.status_code == 200
        assert "count" in r.json()
        assert isinstance(r.json()["count"], int)


class TestNormalizedEventsModels:
    """Test normalized events data models."""

    def test_store_and_get(self):
        from modules.normalized_events import models
        eid = _uid()
        e = models.store_event({
            "id": eid, "entity_type": "earthquake", "source": "usgs", "title": "Model Test",
        })
        assert e["id"] == eid
        got = models.get_event(eid)
        assert got["title"] == "Model Test"

    def test_store_batch(self):
        from modules.normalized_events import models
        events = [
            {"entity_type": "fire", "source": "firms", "title": "Batch1"},
            {"entity_type": "fire", "source": "firms", "title": "Batch2"},
        ]
        stored = models.store_events_batch(events)
        assert len(stored) == 2

    def test_count(self):
        from modules.normalized_events import models
        count = models.count_events()
        assert isinstance(count, int)
