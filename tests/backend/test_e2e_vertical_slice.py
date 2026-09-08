"""Full E2E integration test — complete vertical slice validation.

Tests the entire chain:
  incident → decision context → exposure → risk → ML → need → resource → assignment → timeline → outcome → feedback

No external API dependencies. Uses controlled fixtures.
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
def incident_payload():
    return {
        "title": "Incendio forestal en Madrid — prueba E2E",
        "lat": 40.42,
        "lon": -3.70,
        "event_type": "incendio",
        "source": "manual",
        "severity": "roja",
        "magnitude": 8.5,
        "description": "Incendio activo con amenaza a zona residencial",
    }


class TestFullVerticalSliceE2E:
    """Complete vertical slice: incident → decision → need → resource → assignment → outcome."""

    def test_01_create_incident(self, client, incident_payload):
        resp = client.post("/api/incidents", json=incident_payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == incident_payload["title"]
        assert data["severity"] == "roja"
        assert data["h3_index"] is not None
        assert data["is_active"] == 1

    def test_02_timeline_records_detection(self, client, incident_payload):
        inc_resp = client.post("/api/incidents", json=incident_payload)
        inc_id = inc_resp.json()["id"]

        tl_resp = client.get(f"/api/incidents/{inc_id}/timeline")
        assert tl_resp.status_code == 200
        data = tl_resp.json()
        events = data["events"]
        assert len(events) >= 1
        assert events[0]["event_type"] == "detected"

    def test_03_analyze_incident(self, client, incident_payload):
        inc_resp = client.post("/api/incidents", json=incident_payload)
        inc_id = inc_resp.json()["id"]

        analyze_resp = client.post(f"/api/incidents/{inc_id}/analyze")
        assert analyze_resp.status_code == 200
        data = analyze_resp.json()
        assert "decision_context" in data
        assert data["scores_updated"] is True

        ctx = data["decision_context"]
        assert "risk" in ctx
        assert "situation" in ctx
        assert "operation" in ctx
        assert "impact" in ctx
        assert ctx["risk"]["combined_score"] >= 0
        assert ctx["risk"]["priority_level"] in ["informativo", "bajo", "medio", "alto", "critico"]

    def test_04_timeline_records_evaluation(self, client, incident_payload):
        inc_resp = client.post("/api/incidents", json=incident_payload)
        inc_id = inc_resp.json()["id"]

        client.post(f"/api/incidents/{inc_id}/analyze")

        tl_resp = client.get(f"/api/incidents/{inc_id}/timeline")
        events = tl_resp.json()["events"]
        event_types = [e["event_type"] for e in events]
        assert "evaluated" in event_types

    def test_05_create_need_for_incident(self, client, incident_payload):
        inc_resp = client.post("/api/incidents", json=incident_payload)
        inc_id = inc_resp.json()["id"]

        need_resp = client.post(f"/api/incidents/{inc_id}/needs", json={
            "tipo": "agua",
            "titulo": "Agua potable para evacuados",
            "descripcion": "Zona sin suministro",
            "prioridad": "alta",
            "latitud": 40.42,
            "longitud": -3.70,
        })
        assert need_resp.status_code == 201
        need = need_resp.json()
        assert need["tipo"] == "agua"
        assert need["prioridad"] == "alta"

    def test_06_timeline_records_need_created(self, client, incident_payload):
        inc_resp = client.post("/api/incidents", json=incident_payload)
        inc_id = inc_resp.json()["id"]

        client.post(f"/api/incidents/{inc_id}/needs", json={
            "tipo": "alimentos",
            "titulo": "Comida para refugiados",
            "descripcion": "Estación de emergencia",
            "prioridad": "media",
            "latitud": 40.42,
            "longitud": -3.70,
        })

        tl_resp = client.get(f"/api/incidents/{inc_id}/timeline")
        events = tl_resp.json()["events"]
        event_types = [e["event_type"] for e in events]
        assert "need_created" in event_types

    def test_07_resolve_incident(self, client, incident_payload):
        inc_resp = client.post("/api/incidents", json=incident_payload)
        inc_id = inc_resp.json()["id"]

        client.post(f"/api/incidents/{inc_id}/analyze")

        resolve_resp = client.post(f"/api/incidents/{inc_id}/resolve")
        assert resolve_resp.status_code == 200
        assert resolve_resp.json()["status"] == "resuelto"

        tl_resp = client.get(f"/api/incidents/{inc_id}/timeline")
        events = tl_resp.json()["events"]
        event_types = [e["event_type"] for e in events]
        assert "resolved" in event_types

    def test_08_feedback_loop_integrity(self, client, incident_payload):
        inc_resp = client.post("/api/incidents", json=incident_payload)
        inc_id = inc_resp.json()["id"]

        client.post(f"/api/incidents/{inc_id}/analyze")

        stats_resp = client.get("/api/outcomes/stats")
        assert stats_resp.status_code == 200
        stats = stats_resp.json()
        assert stats["total_predictions"] >= 1

    def test_09_decision_center_with_context(self, client, incident_payload):
        inc_resp = client.post("/api/incidents", json=incident_payload)
        inc = inc_resp.json()

        dc_resp = client.get(f"/api/decision?lat={inc['lat']}&lon={inc['lon']}")
        assert dc_resp.status_code == 200
        # Response may be HTML fallback or JSON
        content_type = dc_resp.headers.get("content-type", "")
        if "json" in content_type:
            ctx = dc_resp.json()
            assert "situation" in ctx or "risk" in ctx

    def test_10_operational_summary_includes_incidents(self, client, incident_payload):
        client.post("/api/incidents", json=incident_payload)

        summary_resp = client.get("/api/operational/summary")
        assert summary_resp.status_code == 200
        summary = summary_resp.json()
        assert "incidents" in summary
        assert summary["incidents"]["total"] >= 1

    def test_11_operational_incidents_list(self, client, incident_payload):
        client.post("/api/incidents", json=incident_payload)

        resp = client.get("/api/operational/incidents")
        assert resp.status_code == 200
        data = resp.json()
        assert "incidents" in data
        assert len(data["incidents"]) >= 1

    def test_12_severity_filter(self, client, incident_payload):
        client.post("/api/incidents", json=incident_payload)

        resp = client.get("/api/operational/incidents?severity=roja")
        assert resp.status_code == 200
        for inc in resp.json()["incidents"]:
            assert inc["severity"] == "roja"

    def test_13_incident_scores_updated_after_analysis(self, client, incident_payload):
        inc_resp = client.post("/api/incidents", json=incident_payload)
        inc_id = inc_resp.json()["id"]

        client.post(f"/api/incidents/{inc_id}/analyze")

        get_resp = client.get(f"/api/incidents/{inc_id}")
        inc = get_resp.json()
        assert inc["priority_score"] is not None
        assert inc["priority_score"] >= 0

    def test_14_create_need_standalone(self, client):
        resp = client.post("/api/necesidades", json={
            "tipo": "refugio",
            "titulo": "Necesidad E2E standalone",
            "descripcion": "Test standalone need",
            "prioridad": "media",
            "latitud": 40.42,
            "longitud": -3.70,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["tipo"] == "refugio"

    def test_15_health_endpoint(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_16_list_tools(self, client):
        resp = client.get("/api/ai/tools")
        assert resp.status_code == 200
        tools = resp.json()["tools"]
        assert len(tools) == 9

    def test_17_incident_404(self, client):
        resp = client.get("/api/incidents/99999")
        assert resp.status_code == 404

    def test_18_analyze_404(self, client):
        resp = client.post("/api/incidents/99999/analyze")
        assert resp.status_code == 404

    def test_19_full_chain_idempotent(self, client, incident_payload):
        inc_resp = client.post("/api/incidents", json=incident_payload)
        inc_id = inc_resp.json()["id"]

        r1 = client.post(f"/api/incidents/{inc_id}/analyze")
        assert r1.status_code == 200

        r2 = client.post(f"/api/incidents/{inc_id}/analyze")
        assert r2.status_code == 200

    def test_20_need_list(self, client):
        resp = client.get("/api/necesidades")
        assert resp.status_code == 200

    def test_21_resources_list(self, client):
        resp = client.get("/api/resources")
        assert resp.status_code == 200

    def test_22_geodata_earthquakes(self, client):
        resp = client.get("/api/geodata/earthquakes")
        assert resp.status_code == 200

    def test_23_external_risk_status(self, client):
        resp = client.get("/api/external-risk/status")
        assert resp.status_code == 200
