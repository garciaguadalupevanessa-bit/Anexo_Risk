"""Tests for bidirectional integration — Anexo_Risk → GeoRisk.

Tests the operational endpoints that GeoRisk can consume:
- /api/operational/events
- /api/operational/needs
- /api/operational/resources
- /api/operational/summary
- /api/operational/h3/{h3_index}

Also tests the feedback loop model.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

# Valid H3 index for Madrid (40.4168, -3.7038) at resolution 3
VALID_H3_INDEX = "83390cfffffffff"


@pytest.fixture
def client():
    from main import app
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Operational Events
# ---------------------------------------------------------------------------
class TestOperationalEvents:
    def test_events_returns_list(self, client):
        resp = client.get("/api/operational/events")
        assert resp.status_code == 200
        data = resp.json()
        assert "events" in data
        assert "total" in data
        assert data["source"] == "anexo_risk"

    def test_events_with_limit(self, client):
        resp = client.get("/api/operational/events?limit=5")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] <= 5

    def test_events_with_invalid_bbox(self, client):
        resp = client.get("/api/operational/events?bbox=invalid")
        assert resp.status_code == 200
        data = resp.json()
        assert "events" in data

    def test_events_with_valid_bbox(self, client):
        resp = client.get("/api/operational/events?bbox=39.0,-4.0,41.0,-3.0")
        assert resp.status_code == 200
        data = resp.json()
        assert "events" in data

    def test_events_with_since(self, client):
        resp = client.get("/api/operational/events?since=2026-01-01T00:00:00Z")
        assert resp.status_code == 200
        data = resp.json()
        assert "events" in data

    def test_events_with_radius(self, client):
        resp = client.get("/api/operational/events?center_lat=40.4168&center_lon=-3.7038&radius_km=50")
        assert resp.status_code == 200
        data = resp.json()
        assert "events" in data

    def test_events_limit_validation(self, client):
        resp = client.get("/api/operational/events?limit=0")
        assert resp.status_code == 422

    def test_events_limit_max(self, client):
        resp = client.get("/api/operational/events?limit=2000")
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Operational Needs
# ---------------------------------------------------------------------------
class TestOperationalNeeds:
    def test_needs_returns_list(self, client):
        resp = client.get("/api/operational/needs")
        assert resp.status_code == 200
        data = resp.json()
        assert "needs" in data
        assert "total" in data
        assert data["source"] == "anexo_risk"

    def test_needs_default_open(self, client):
        resp = client.get("/api/operational/needs")
        assert resp.status_code == 200
        data = resp.json()
        # All returned needs should be open by default
        for need in data["needs"]:
            assert need.get("estado") == "abierta"

    def test_needs_with_status_filter(self, client):
        resp = client.get("/api/operational/needs?status=cubierta")
        assert resp.status_code == 200
        data = resp.json()
        for need in data["needs"]:
            assert need.get("estado") == "cubierta"

    def test_needs_with_priority_filter(self, client):
        resp = client.get("/api/operational/needs?priority=critica")
        assert resp.status_code == 200
        data = resp.json()
        for need in data["needs"]:
            assert need.get("prioridad") == "critica"

    def test_needs_with_h3_index(self, client):
        resp = client.get("/api/operational/needs?h3_index=83390cfffffffff")
        assert resp.status_code == 200
        data = resp.json()
        assert "needs" in data

    def test_needs_with_bbox(self, client):
        resp = client.get("/api/operational/needs?bbox=39.0,-4.0,41.0,-3.0")
        assert resp.status_code == 200
        data = resp.json()
        assert "needs" in data


# ---------------------------------------------------------------------------
# Operational Resources
# ---------------------------------------------------------------------------
class TestOperationalResources:
    def test_resources_returns_list(self, client):
        resp = client.get("/api/operational/resources")
        assert resp.status_code == 200
        data = resp.json()
        assert "resources" in data
        assert "total" in data
        assert data["source"] == "anexo_risk"

    def test_resources_with_status_filter(self, client):
        resp = client.get("/api/operational/resources?status=disponible")
        assert resp.status_code == 200
        data = resp.json()
        for res in data["resources"]:
            assert res.get("status") == "disponible"

    def test_resources_with_h3_index(self, client):
        resp = client.get("/api/operational/resources?h3_index=83390cfffffffff")
        assert resp.status_code == 200
        data = resp.json()
        assert "resources" in data

    def test_resources_with_bbox(self, client):
        resp = client.get("/api/operational/resources?bbox=39.0,-4.0,41.0,-3.0")
        assert resp.status_code == 200
        data = resp.json()
        assert "resources" in data


# ---------------------------------------------------------------------------
# Operational Summary
# ---------------------------------------------------------------------------
class TestOperationalSummary:
    def test_summary_returns_all_sections(self, client):
        resp = client.get("/api/operational/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert "needs" in data
        assert "alerts" in data
        assert "resources" in data
        assert "assignments" in data
        assert "metrics" in data
        assert data["source"] == "anexo_risk"

    def test_summary_metrics_fields(self, client):
        resp = client.get("/api/operational/summary")
        data = resp.json()
        metrics = data["metrics"]
        assert "resource_gap" in metrics
        assert "operational_load" in metrics
        assert "needs_open" in metrics
        assert "needs_uncovered" in metrics

    def test_summary_with_h3_index(self, client):
        resp = client.get("/api/operational/summary?h3_index=83390cfffffffff")
        assert resp.status_code == 200
        data = resp.json()
        assert "metrics" in data

    def test_summary_with_bbox(self, client):
        resp = client.get("/api/operational/summary?bbox=39.0,-4.0,41.0,-3.0")
        assert resp.status_code == 200
        data = resp.json()
        assert "metrics" in data

    def test_summary_operational_load_range(self, client):
        resp = client.get("/api/operational/summary")
        data = resp.json()
        load = data["metrics"]["operational_load"]
        assert 0.0 <= load <= 1.0


# ---------------------------------------------------------------------------
# Operational H3 Cell
# ---------------------------------------------------------------------------
class TestOperationalH3:
    def test_h3_cell_returns_metrics(self, client):
        resp = client.get("/api/operational/h3/83390cfffffffff")
        assert resp.status_code == 200
        data = resp.json()
        assert "h3_index" in data
        assert "needs" in data
        assert "resources" in data
        assert "alerts" in data
        assert "metrics" in data
        assert data["source"] == "anexo_risk"

    def test_h3_cell_metrics_fields(self, client):
        resp = client.get("/api/operational/h3/83390cfffffffff")
        data = resp.json()
        metrics = data["metrics"]
        assert "resource_gap" in metrics
        assert "operational_load" in metrics
        assert "needs_open" in metrics
        assert "needs_uncovered" in metrics

    def test_h3_cell_centroid(self, client):
        resp = client.get("/api/operational/h3/83390cfffffffff")
        data = resp.json()
        assert "centroid" in data
        assert "lat" in data["centroid"]
        assert "lon" in data["centroid"]

    def test_h3_cell_invalid_index(self, client):
        resp = client.get("/api/operational/h3/invalid")
        data = resp.json()
        assert "error" in data


# ---------------------------------------------------------------------------
# Feedback Loop Model
# ---------------------------------------------------------------------------
class TestFeedbackLoop:
    def test_record_prediction(self):
        from models.feedback import record_prediction, init_feedback_table
        init_feedback_table()
        result = record_prediction(
            prediction_source="anexo_risk",
            model_version="rules-v1",
            predicted_level="alta",
            predicted_score=72.5,
            prediction_time="2026-09-07T12:00:00Z",
            h3_index="83390cfffffffff",
            lat=40.4168,
            lon=-3.7038,
            needs_open=5,
            resources_available=2,
        )
        assert result["status"] == "recorded"
        assert result["id"] > 0

    def test_record_outcome(self):
        from models.feedback import record_prediction, record_outcome, init_feedback_table
        init_feedback_table()
        pred = record_prediction(
            prediction_source="georisk",
            model_version="georisk-v3",
            predicted_level="critica",
            predicted_score=88.0,
            prediction_time="2026-09-07T12:00:00Z",
            h3_index="83390cfffffffff",
        )
        result = record_outcome(
            feedback_id=pred["id"],
            incident_closed=True,
            needs_created=3,
            needs_resolved=5,
            resource_gap=2,
            response_duration_hours=4.5,
            escalation_occurred=False,
        )
        assert result["status"] == "outcome_recorded"

    def test_get_feedback_entries(self):
        from models.feedback import get_feedback_entries
        entries = get_feedback_entries(limit=10)
        assert isinstance(entries, list)

    def test_get_feedback_entries_by_source(self):
        from models.feedback import get_feedback_entries
        entries = get_feedback_entries(prediction_source="anexo_risk")
        assert isinstance(entries, list)

    def test_get_feedback_stats(self):
        from models.feedback import get_feedback_stats
        stats = get_feedback_stats()
        assert isinstance(stats, dict)
        assert "total_predictions" in stats
