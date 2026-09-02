"""Comprehensive test suite for the alerts API module.

Covers GDACS RSS data parsing and integration contracts, query parameter
filtering, descending chronological sorting, in-memory caching performance,
alert status lifecycle actions (activate, high-risk, deactivate), and resilience 
against malformed XML payloads, missing fields, invalid GeoJSON, and external 
network failures.
"""

from typing import Any
from unittest.mock import patch
from fastapi.testclient import TestClient
import pytest

from integrations import gdacs_client
from modules.alertas import services
from main import app


@pytest.fixture(autouse=True)
def reset_gdacs_cache():
    """Resets GDACS client cache and local database before each test execution."""
    gdacs_client.clear_cache()
    with services._DB_LOCK:
        services.LOCAL_ALERTS_DB.clear()
    yield


class TestAlertsBase:
    """Base test class holding shared fixtures and mock datasets."""

    client: TestClient = TestClient(app)

    MOCK_GDACS_RSS_XML: str = """<?xml version="1.0" encoding="utf-8"?>
    <rss version="2.0" xmlns:gdacs="http://www.gdacs.org" xmlns:geo="http://www.w3.org/2003/01/geo/wgs84_pos#">
        <channel>
            <item>
                <title>Earthquake - Spain</title>
                <description>Sismo registrado en la región de Granada</description>
                <link>https://www.gdacs.org/report.aspx?eventid=1001</link>
                <pubDate>Wed, 29 Apr 2026 08:30:00 GMT</pubDate>
                <gdacs:eventtype>EQ</gdacs:eventtype>
                <gdacs:alertlevel>Green</gdacs:alertlevel>
                <gdacs:country>Spain</gdacs:country>
                <geo:lat>37.17</geo:lat>
                <geo:long>-3.60</geo:long>
            </item>
            <item>
                <title>Flood - Spain</title>
                <description>Inundación en la cuenca del Ebro</description>
                <link>https://www.gdacs.org/report.aspx?eventid=1002</link>
                <pubDate>Thu, 30 Apr 2026 13:07:47 GMT</pubDate>
                <gdacs:eventtype>FL</gdacs:eventtype>
                <gdacs:alertlevel>Red</gdacs:alertlevel>
                <gdacs:country>Espania</gdacs:country>
                <geo:lat>41.65</geo:lat>
                <geo:long>-0.88</geo:long>
            </item>
            <item>
                <title>Tropical Cyclone - Philippines</title>
                <description>Ciclón en Filipinas</description>
                <link>https://www.gdacs.org/report.aspx?eventid=1003</link>
                <pubDate>Tue, 28 Apr 2026 10:00:00 GMT</pubDate>
                <gdacs:eventtype>TC</gdacs:eventtype>
                <gdacs:alertlevel>Orange</gdacs:alertlevel>
                <gdacs:country>Philippines</gdacs:country>
                <geo:lat>12.87</geo:lat>
                <geo:long>121.77</geo:long>
            </item>
        </channel>
    </rss>
    """

    MOCK_XML_MISSING_FIELDS: str = """<?xml version="1.0" encoding="utf-8"?>
    <rss version="2.0" xmlns:gdacs="http://www.gdacs.org">
        <channel>
            <item>
                <title>Alert with missing fields</title>
                <description>Alerta sin fecha ni pais</description>
                <link>https://www.gdacs.org/report.aspx?eventid=9999</link>
                <gdacs:eventtype>EQ</gdacs:eventtype>
                <gdacs:alertlevel>Green</gdacs:alertlevel>
            </item>
        </channel>
    </rss>
    """


class TestAlertsContractAndSorting(TestAlertsBase):
    """Test cases focused on contract status, schema compliance, and ordering."""

    @patch("integrations.gdacs_client.requests.get")
    def test_read_alerts_success_status_and_schema(
        self, mock_get: Any
    ) -> None:
        """Verifies 200 OK status code and response schema integrity."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = self.MOCK_GDACS_RSS_XML.encode("utf-8")

        response = self.client.get("/api/alertas")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3

        expected_keys = {
            "id",
            "source",
            "tipo",
            "titulo",
            "descripcion",
            "severidad",
            "risk_level",
            "status",
            "is_active",
            "pais",
            "lat",
            "lon",
            "fecha",
            "enlace",
        }
        for item in data:
            assert expected_keys.issubset(item.keys())

    @patch("integrations.gdacs_client.requests.get")
    def test_read_alerts_chronological_sorting(self, mock_get: Any) -> None:
        """Ensures alerts are sorted in descending chronological order."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = self.MOCK_GDACS_RSS_XML.encode("utf-8")

        response = self.client.get("/api/alertas")
        assert response.status_code == 200

        data = response.json()
        assert data[0]["tipo"] in ("inundacion", "flood")
        assert data[1]["tipo"] in ("terremoto", "earthquake")
        assert data[2]["tipo"] in ("ciclon", "cyclone")


class TestAlertsFiltering(TestAlertsBase):
    """Test cases focused on query parameter filtering mechanisms."""

    @patch("integrations.gdacs_client.requests.get")
    def test_filter_by_alert_level(self, mock_get: Any) -> None:
        """Tests filtering results by severity attribute."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = self.MOCK_GDACS_RSS_XML.encode("utf-8")

        response = self.client.get("/api/alertas?severidad=RED")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1
        assert data[0]["severidad"] == "RED"
        assert data[0]["tipo"] in ("inundacion", "flood")

    @patch("integrations.gdacs_client.requests.get")
    def test_filter_by_event_type(self, mock_get: Any) -> None:
        """Tests filtering results by tipo attribute."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = self.MOCK_GDACS_RSS_XML.encode("utf-8")

        response = self.client.get("/api/alertas?tipo=terremoto")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1
        assert data[0]["tipo"] in ("terremoto", "earthquake")

    @patch("integrations.gdacs_client.requests.get")
    def test_filter_case_insensitivity_and_partial_country(
        self, mock_get: Any
    ) -> None:
        """Ensures query filtering is case-insensitive and supports country substrings."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = self.MOCK_GDACS_RSS_XML.encode("utf-8")

        response = self.client.get("/api/alertas?pais=ESPA&severidad=RED")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1
        assert data[0]["severidad"] == "RED"
        assert "espania" in data[0]["pais"].lower() or "spain" in data[0]["pais"].lower()

    @patch("integrations.gdacs_client.requests.get")
    def test_filter_no_matches_returns_empty_list(self, mock_get: Any) -> None:
        """Verifies that queries with no matching entities return an empty JSON list."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = self.MOCK_GDACS_RSS_XML.encode("utf-8")

        response = self.client.get("/api/alertas?tipo=volcan")
        assert response.status_code == 200
        assert response.json() == []

    def test_invalid_enum_filter_returns_422_validation_error(self) -> None:
        """Validates OpenAPI contract validation when passing illegal Enum query options."""
        response = self.client.get("/api/alertas?tipo=invalid_type")
        assert response.status_code == 422


class TestAlertsCachingAndPerformance(TestAlertsBase):
    """Test cases verifying caching performance requirements."""

    @patch("integrations.gdacs_client.requests.get")
    def test_caching_mechanism_prevents_duplicate_http_calls(
        self, mock_get: Any
    ) -> None:
        """Validates that a second request retrieves data from in-memory cache."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = self.MOCK_GDACS_RSS_XML.encode("utf-8")

        res1 = self.client.get("/api/alertas")
        assert res1.status_code == 200

        res2 = self.client.get("/api/alertas")
        assert res2.status_code == 200

        assert mock_get.call_count <= 1


class TestAlertsActions(TestAlertsBase):
    """Test suite targeting alert creation and operational status state transitions."""

    @patch("integrations.gdacs_client.requests.get")
    def test_create_alert_success(self, mock_get: Any) -> None:
        """Verifies manual alert creation returning 201 Created status and standard schema."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = self.MOCK_GDACS_RSS_XML.encode("utf-8")

        payload = {
            "title": "Alerta de prueba",
            "description": "Detalles de la alerta",
            "type": "inundacion",
            "zone": {
                "type": "Polygon",
                "coordinates": [[[-0.37, 39.46], [-0.36, 39.46], [-0.36, 39.45], [-0.37, 39.45], [-0.37, 39.46]]],
            },
            "risk_level": "medium",
        }
        res = self.client.post("/api/alertas", json=payload)
        assert res.status_code == 201

        data = res.json()
        assert data["titulo"] == "Alerta de prueba"
        assert data["tipo"] == "inundacion"
        assert data["risk_level"] == "medium"
        assert data["is_active"] is True

    @patch("integrations.gdacs_client.requests.get")
    def test_high_risk_unlocks_zone(self, mock_get: Any) -> None:
        """Verifies setting high risk updates risk_level to high and marks state as active."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = self.MOCK_GDACS_RSS_XML.encode("utf-8")

        payload = {
            "title": "Simulacro Valencia",
            "zone": {
                "type": "Polygon",
                "coordinates": [[[-0.37, 39.46], [-0.36, 39.46], [-0.36, 39.45], [-0.37, 39.45], [-0.37, 39.46]]],
            },
            "risk_level": "low",
        }
        create_res = self.client.post("/api/alertas", json=payload)
        assert create_res.status_code == 201
        alert_id = create_res.json()["id"]

        high_risk_res = self.client.post(f"/api/alertas/{alert_id}/alto-riesgo")
        assert high_risk_res.status_code == 200

        data = high_risk_res.json()
        assert data["risk_level"] == "high"
        assert data["is_active"] is True
        assert data["zone"]["type"] == "Polygon"

    @patch("integrations.gdacs_client.requests.get")
    def test_deactivate_and_activate_alert_lifecycle(self, mock_get: Any) -> None:
        """Verifies deactivating and re-activating an existing alert updates operational status."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = self.MOCK_GDACS_RSS_XML.encode("utf-8")

        payload = {
            "title": "Test Ciclo de Vida",
            "zone": {
                "type": "Polygon",
                "coordinates": [[[-0.37, 39.46], [-0.36, 39.46], [-0.36, 39.45], [-0.37, 39.45], [-0.37, 39.46]]],
            },
        }
        create_res = self.client.post("/api/alertas", json=payload)
        assert create_res.status_code == 201
        alert_id = create_res.json()["id"]

        # 1. Desactivar
        deactivate_res = self.client.post(f"/api/alertas/{alert_id}/desactivar")
        assert deactivate_res.status_code == 200
        assert deactivate_res.json()["status"] == "deactivated"
        assert deactivate_res.json()["is_active"] is False

        # 2. Reactivar
        activate_res = self.client.post(f"/api/alertas/{alert_id}/activar")
        assert activate_res.status_code == 200
        assert activate_res.json()["status"] == "active"
        assert activate_res.json()["is_active"] is True

    def test_alert_action_not_found_returns_404(self) -> None:
        """Verifies 404 Not Found status code when triggering actions on missing alert IDs."""
        for endpoint_suffix in ("activar", "alto-riesgo", "desactivar"):
            res = self.client.post(f"/api/alertas/non-existent-id/{endpoint_suffix}")
            assert res.status_code == 404
            assert res.json()["detail"] == "Alerta no encontrada"

    def test_create_alert_invalid_geojson_polygon_returns_422(self) -> None:
        """Verifies 422 Unprocessable Entity when creating an alert with non-Polygon GeoJSON."""
        invalid_payload = {
            "title": "Zona Inválida",
            "zone": {
                "type": "Point",
                "coordinates": [-0.37, 39.46],
            },
        }
        res = self.client.post("/api/alertas", json=invalid_payload)
        assert res.status_code == 422
        assert "Polygon" in res.json()["detail"]


class TestAlertsResilienceAndEdgeCases(TestAlertsBase):
    """Test cases covering resilience against errors, network issues, and bad input."""

    @patch("integrations.gdacs_client.requests.get")
    def test_resilience_on_external_network_exception(
        self, mock_get: Any
    ) -> None:
        """Ensures service handles network timeouts gracefully."""
        mock_get.side_effect = Exception("Connection Timeout Error")

        response = self.client.get("/api/alertas")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @patch("integrations.gdacs_client.requests.get")
    def test_resilience_on_500_server_error_from_gdacs(
        self, mock_get: Any
    ) -> None:
        """Ensures service handles HTTP error status codes from GDACS gracefully."""
        mock_get.return_value.status_code = 500
        mock_get.return_value.content = b"Internal Server Error"

        response = self.client.get("/api/alertas")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @patch("integrations.gdacs_client.requests.get")
    def test_resilience_on_malformed_xml_payload(self, mock_get: Any) -> None:
        """Verifies that unparseable RSS XML responses do not crash the endpoint."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b"<rss><channel><unclosed_tag></channel>"

        response = self.client.get("/api/alertas")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @patch("integrations.gdacs_client.requests.get")
    def test_read_alerts_handles_missing_fields_gracefully(
        self, mock_get: Any
    ) -> None:
        """Verifies missing non-essential XML tags do not cause internal server errors."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = self.MOCK_XML_MISSING_FIELDS.encode(
            "utf-8"
        )

        response = self.client.get("/api/alertas")
        assert response.status_code == 200

        data = response.json()
        assert len(data) >= 0

    @patch("integrations.gdacs_client.requests.get")
    def test_read_alerts_handles_invalid_date_format(
        self, mock_get: Any
    ) -> None:
        """Ensures unparseable date strings default safely without crashing."""
        bad_date_xml = self.MOCK_GDACS_RSS_XML.replace(
            "Thu, 30 Apr 2026 13:07:47 GMT", "Invalid-Date-String"
        )
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = bad_date_xml.encode("utf-8")

        response = self.client.get("/api/alertas")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 3

    @patch("integrations.gdacs_client.requests.get")
    def test_read_alerts_empty_query_string_parameters(
        self, mock_get: Any
    ) -> None:
        """Verifies empty query parameters are ignored without failing."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = self.MOCK_GDACS_RSS_XML.encode("utf-8")

        response = self.client.get("/api/alertas?pais=&tipo=&severidad=")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 3