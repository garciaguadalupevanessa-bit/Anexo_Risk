"""End-to-end integration tests for the vertical slice.

Tests the full chain: incident → decision context → need → outcome.
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def sample_incident_payload():
    return {
        "title": "Terremoto magnitude 5.2 en Granada",
        "lat": 37.17,
        "lon": -3.60,
        "event_type": "terremoto",
        "source": "usgs",
        "severity": "naranja",
        "magnitude": 5.2,
        "description": "Sismo de magnitud 5.2 a 15km de profundidad",
    }


class TestIncidentCreation:
    """Test incident creation records detection in timeline."""

    def test_create_incident_returns_201(self, client, sample_incident_payload):
        response = client.post("/api/incidents", json=sample_incident_payload)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == sample_incident_payload["title"]
        assert data["lat"] == sample_incident_payload["lat"]
        assert data["lon"] == sample_incident_payload["lon"]
        assert data["severity"] == "naranja"
        assert data["is_active"] == 1

    def test_create_incident_generates_h3_index(self, client, sample_incident_payload):
        response = client.post("/api/incidents", json=sample_incident_payload)
        data = response.json()
        assert data["h3_index"] is not None
        assert len(data["h3_index"]) > 0

    def test_create_incident_records_timeline_event(self, client, sample_incident_payload):
        create_resp = client.post("/api/incidents", json=sample_incident_payload)
        incident_id = create_resp.json()["id"]

        timeline_resp = client.get(f"/api/incidents/{incident_id}/timeline")
        assert timeline_resp.status_code == 200
        events = timeline_resp.json()["events"]
        assert len(events) >= 1
        assert events[0]["event_type"] == "detected"
        assert "detectado" in events[0]["description"]

    def test_get_incident_not_found(self, client):
        response = client.get("/api/incidents/999999")
        assert response.status_code == 404


class TestIncidentAnalysis:
    """Test the analyze endpoint: incident → decision context → risk scores."""

    def test_analyze_returns_decision_context(self, client, sample_incident_payload):
        create_resp = client.post("/api/incidents", json=sample_incident_payload)
        incident_id = create_resp.json()["id"]

        response = client.post(f"/api/incidents/{incident_id}/analyze")
        assert response.status_code == 200
        data = response.json()
        assert data["incident_id"] == incident_id
        assert "decision_context" in data
        assert data["scores_updated"] is True

    def test_analyze_populates_risk_score(self, client, sample_incident_payload):
        create_resp = client.post("/api/incidents", json=sample_incident_payload)
        incident_id = create_resp.json()["id"]

        response = client.post(f"/api/incidents/{incident_id}/analyze")
        ctx = response.json()["decision_context"]
        assert "risk" in ctx
        assert "combined_score" in ctx["risk"]
        assert "priority_level" in ctx["risk"]
        assert "source" in ctx["risk"]

    def test_analyze_records_timeline_event(self, client, sample_incident_payload):
        create_resp = client.post("/api/incidents", json=sample_incident_payload)
        incident_id = create_resp.json()["id"]

        client.post(f"/api/incidents/{incident_id}/analyze")

        timeline_resp = client.get(f"/api/incidents/{incident_id}/timeline")
        events = timeline_resp.json()["events"]
        event_types = [e["event_type"] for e in events]
        assert "detected" in event_types
        assert "evaluated" in event_types

    def test_analyze_updates_incident_scores(self, client, sample_incident_payload):
        create_resp = client.post("/api/incidents", json=sample_incident_payload)
        incident_id = create_resp.json()["id"]

        client.post(f"/api/incidents/{incident_id}/analyze")

        get_resp = client.get(f"/api/incidents/{incident_id}")
        incident = get_resp.json()
        assert incident["priority_score"] is not None
        assert incident["priority_score"] > 0

    def test_analyze_not_found(self, client):
        response = client.post("/api/incidents/999999/analyze")
        assert response.status_code == 404


class TestNeedCreationFromIncident:
    """Test creating needs linked to incidents."""

    def test_create_need_for_incident(self, client, sample_incident_payload):
        create_resp = client.post("/api/incidents", json=sample_incident_payload)
        incident_id = create_resp.json()["id"]

        need_payload = {
            "titulo": "Agua potable para familias afectadas",
            "tipo": "agua",
            "descripcion": "Se necesita agua potable para 50 familias",
            "latitud": 37.17,
            "longitud": -3.60,
            "prioridad": "alta",
        }

        response = client.post(f"/api/incidents/{incident_id}/needs", json=need_payload)
        assert response.status_code == 201
        data = response.json()
        assert data["tipo"] == "agua"
        assert data["prioridad"] == "alta"

    def test_need_creation_records_timeline(self, client, sample_incident_payload):
        create_resp = client.post("/api/incidents", json=sample_incident_payload)
        incident_id = create_resp.json()["id"]

        need_payload = {
            "titulo": "Refugio temporal",
            "tipo": "refugio",
            "latitud": 37.17,
            "longitud": -3.60,
            "prioridad": "critica",
        }

        client.post(f"/api/incidents/{incident_id}/needs", json=need_payload)

        timeline_resp = client.get(f"/api/incidents/{incident_id}/timeline")
        events = timeline_resp.json()["events"]
        event_types = [e["event_type"] for e in events]
        assert "need_created" in event_types

    def test_need_creation_updates_incident_status(self, client, sample_incident_payload):
        create_resp = client.post("/api/incidents", json=sample_incident_payload)
        incident_id = create_resp.json()["id"]

        need_payload = {
            "titulo": "Alimentos",
            "tipo": "alimentos",
            "latitud": 37.17,
            "longitud": -3.60,
        }

        client.post(f"/api/incidents/{incident_id}/needs", json=need_payload)

        get_resp = client.get(f"/api/incidents/{incident_id}")
        assert get_resp.json()["status"] == "en_respuesta"

    def test_need_for_nonexistent_incident(self, client):
        need_payload = {
            "titulo": "Test",
            "tipo": "agua",
            "latitud": 37.17,
            "longitud": -3.60,
        }
        response = client.post("/api/incidents/999999/needs", json=need_payload)
        assert response.status_code == 404


class TestFullVerticalSlice:
    """Full E2E: create incident → analyze → create need → check timeline."""

    def test_complete_lifecycle(self, client):
        # 1. Create incident
        incident_payload = {
            "title": "Inundación en zona urbana",
            "lat": 40.42,
            "lon": -3.70,
            "event_type": "alerta",
            "source": "aemet",
            "severity": "roja",
            "description": "Avenida de agua en barrio residencial",
        }
        create_resp = client.post("/api/incidents", json=incident_payload)
        assert create_resp.status_code == 201
        incident_id = create_resp.json()["id"]

        # 2. Analyze incident
        analyze_resp = client.post(f"/api/incidents/{incident_id}/analyze")
        assert analyze_resp.status_code == 200
        ctx = analyze_resp.json()["decision_context"]
        assert ctx["risk"]["combined_score"] > 0

        # 3. Create need
        need_payload = {
            "titulo": "Evacuación de familias",
            "tipo": "refugio",
            "latitud": 40.42,
            "longitud": -3.70,
            "prioridad": "critica",
        }
        need_resp = client.post(f"/api/incidents/{incident_id}/needs", json=need_payload)
        assert need_resp.status_code == 201

        # 4. Verify full timeline
        timeline_resp = client.get(f"/api/incidents/{incident_id}/timeline")
        events = timeline_resp.json()["events"]
        event_types = [e["event_type"] for e in events]
        assert "detected" in event_types
        assert "evaluated" in event_types
        assert "need_created" in event_types

        # 5. Verify incident final state
        get_resp = client.get(f"/api/incidents/{incident_id}")
        incident = get_resp.json()
        assert incident["status"] == "en_respuesta"
        assert incident["priority_score"] > 0


class TestOutcomesAPI:
    """Test the outcome recording API."""

    def test_record_prediction(self, client):
        payload = {
            "incident_id": 1,
            "prediction_source": "anexo_risk",
            "model_version": "ml-v1-20260907",
            "predicted_level": "alto",
            "predicted_score": 72.5,
            "h3_index": "8c3a1b2badfffff",
            "lat": 37.17,
            "lon": -3.60,
        }
        response = client.post("/api/outcomes/prediction", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "recorded"

    def test_list_outcomes(self, client):
        response = client.get("/api/outcomes")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_outcome_stats(self, client):
        response = client.get("/api/outcomes/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_predictions" in data
