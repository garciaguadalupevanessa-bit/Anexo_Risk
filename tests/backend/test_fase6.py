"""Tests for FASE 6 — Event Correlation."""
import sys
import os
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
os.environ.setdefault("TESTING", "true")
os.environ.setdefault("JWT_SECRET_KEY", "test-fase6")
os.environ.setdefault("ANEXO_ADMIN_KEY", "test-fase6")

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app, raise_server_exceptions=False)


def _uid():
    return "f6_" + uuid.uuid4().hex[:8]


class TestHaversine:
    """Test distance calculation."""

    def test_same_point(self):
        from services.correlation import haversine_km
        assert haversine_km(40.0, -3.0, 40.0, -3.0) == 0.0

    def test_known_distance(self):
        from services.correlation import haversine_km
        # Madrid to Barcelona ~505km
        d = haversine_km(40.4168, -3.7038, 41.3874, 2.1686)
        assert 490 < d < 520

    def test_short_distance(self):
        from services.correlation import haversine_km
        # ~1km apart
        d = haversine_km(40.0, -3.0, 40.01, -3.0)
        assert 0.5 < d < 1.5


class TestCorrelation:
    """Test event correlation logic."""

    def test_same_type_close_events_correlate(self):
        from services.correlation import are_events_correlated
        a = {"entity_type": "earthquake", "lat": 40.0, "lon": -3.0, "timestamp": "2026-09-08T10:00:00Z"}
        b = {"entity_type": "earthquake", "lat": 40.05, "lon": -3.05, "timestamp": "2026-09-08T10:30:00Z"}
        correlated, confidence, reason = are_events_correlated(a, b)
        assert correlated is True
        assert confidence > 0.5

    def test_different_type_no_correlate(self):
        from services.correlation import are_events_correlated
        a = {"entity_type": "earthquake", "lat": 40.0, "lon": -3.0}
        b = {"entity_type": "fire", "lat": 40.0, "lon": -3.0}
        correlated, _, reason = are_events_correlated(a, b)
        assert correlated is False
        assert reason == "type_mismatch"

    def test_far_events_no_correlate(self):
        from services.correlation import are_events_correlated
        a = {"entity_type": "earthquake", "lat": 40.0, "lon": -3.0}
        b = {"entity_type": "earthquake", "lat": 41.0, "lon": -3.0}  # ~111km
        correlated, _, reason = are_events_correlated(a, b, max_distance_km=50)
        assert correlated is False
        assert "distance" in reason

    def test_missing_coordinates(self):
        from services.correlation import are_events_correlated
        a = {"entity_type": "earthquake"}
        b = {"entity_type": "earthquake", "lat": 40.0, "lon": -3.0}
        correlated, _, reason = are_events_correlated(a, b)
        assert correlated is False
        assert reason == "missing_coordinates"

    def test_correlate_events_cluster(self):
        from services.correlation import correlate_events
        events = [
            {"id": "e1", "entity_type": "earthquake", "lat": 40.0, "lon": -3.0, "source": "usgs", "timestamp": "2026-09-08T10:00:00Z", "severity_float": 0.7},
            {"id": "e2", "entity_type": "earthquake", "lat": 40.02, "lon": -3.02, "source": "gdacs", "timestamp": "2026-09-08T10:15:00Z", "severity_float": 0.6},
            {"id": "e3", "entity_type": "fire", "lat": 41.0, "lon": -4.0, "source": "firms", "timestamp": "2026-09-08T11:00:00Z", "severity_float": 0.5},
        ]
        clusters = correlate_events(events)
        assert len(clusters) >= 1
        # e1 and e2 should cluster, e3 separate
        eq_cluster = [c for c in clusters if c["entity_type"] == "earthquake"]
        assert len(eq_cluster) == 1
        assert eq_cluster[0]["count"] == 2
        assert "usgs" in eq_cluster[0]["sources"]
        assert "gdacs" in eq_cluster[0]["sources"]

    def test_empty_events(self):
        from services.correlation import correlate_events
        assert correlate_events([]) == []


class TestCorrelationAPI:
    """Test correlation API endpoints."""

    def test_get_clusters(self):
        r = client.get("/api/correlation/clusters")
        assert r.status_code == 200
        assert "clusters" in r.json()

    def test_run_correlation(self):
        r = client.post("/api/correlation/run")
        assert r.status_code == 200
        assert "clusters_found" in r.json()

    def test_run_correlation_with_filters(self):
        r = client.post("/api/correlation/run?source=usgs&entity_type=earthquake")
        assert r.status_code == 200
