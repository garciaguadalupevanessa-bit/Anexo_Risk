"""Tests for GeoRisk Finder integration.

Tests the circuit breaker, caching, fallback behavior, and API endpoints.
All tests use mocked HTTP calls — no real GeoRisk service required.
"""
from __future__ import annotations

import time
from unittest.mock import patch, MagicMock

import pytest


# ---------------------------------------------------------------------------
# H3 Resolver tests
# ---------------------------------------------------------------------------
class TestH3Resolver:
    """Tests for the H3 spatial resolver."""

    def test_import(self):
        from geodata.services.h3_resolver import latlon_to_h3, h3_to_center, get_h3_resolution
        assert callable(latlon_to_h3)
        assert callable(h3_to_center)
        assert get_h3_resolution() == 3

    def test_latlon_to_h3_returns_string(self):
        from geodata.services.h3_resolver import latlon_to_h3, H3_AVAILABLE
        if not H3_AVAILABLE:
            pytest.skip("h3 not installed")
        result = latlon_to_h3(40.4168, -3.7038)
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0

    def test_latlon_to_h3_invalid_coords(self):
        from geodata.services.h3_resolver import latlon_to_h3, H3_AVAILABLE
        if not H3_AVAILABLE:
            pytest.skip("h3 not installed")
        assert latlon_to_h3(999, -3.7038) is None
        assert latlon_to_h3(40.4168, 999) is None

    def test_h3_to_center(self):
        from geodata.services.h3_resolver import latlon_to_h3, h3_to_center, H3_AVAILABLE
        if not H3_AVAILABLE:
            pytest.skip("h3 not installed")
        h3_idx = latlon_to_h3(40.4168, -3.7038)
        assert h3_idx is not None
        center = h3_to_center(h3_idx)
        assert center is not None
        lat, lon = center
        assert 39 < lat < 42
        assert -5 < lon < -2


# ---------------------------------------------------------------------------
# GeoRisk Client tests
# ---------------------------------------------------------------------------
class TestGeoRiskClient:
    """Tests for the GeoRisk integration client."""

    def test_circuit_breaker_initial_closed(self):
        import integrations.georisk_client as client
        # Reset state
        client._cb_failures = 0
        client._cb_open_until = 0.0
        assert client.is_georisk_available() is True
        status = client.get_circuit_status()
        assert status["state"] == "closed"
        assert status["failures"] == 0

    def test_circuit_breaker_opens_after_failures(self):
        import integrations.georisk_client as client
        client._cb_failures = 0
        client._cb_open_until = 0.0
        for _ in range(3):
            client._cb_record_failure()
        assert client.is_georisk_available() is False
        status = client.get_circuit_status()
        assert status["state"] == "open"

    def test_circuit_breaker_resets_after_time(self):
        import integrations.georisk_client as client
        client._cb_failures = 3
        client._cb_open_until = time.time() - 1  # already expired
        assert client.is_georisk_available() is True  # half-open

    def test_circuit_breaker_resets_on_success(self):
        import integrations.georisk_client as client
        client._cb_failures = 2
        client._cb_open_until = 0.0
        client._cb_record_success()
        assert client._cb_failures == 0
        assert client.is_georisk_available() is True

    def test_cache_hit(self):
        import integrations.georisk_client as client
        client._cache_set("test:key", {"data": "value"})
        result = client._cache_get("test:key")
        assert result == {"data": "value"}

    def test_cache_expired(self):
        import integrations.georisk_client as client
        client._cache["test:expired"] = (time.time() - 10, {"data": "old"})
        result = client._cache_get("test:expired")
        assert result is None

    @patch("integrations.georisk_client.httpx")
    def test_get_cell_risk_success(self, mock_httpx):
        import integrations.georisk_client as client
        client._cb_failures = 0
        client._cb_open_until = 0.0
        client._cache.clear()

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "risk_score": 75.5,
            "risk_level": "high",
            "model_version": "georisk-v3",
            "cluster_id": 2,
            "cluster_label": "Zona sísmica",
            "features": {"eq_count": 45},
            "explanation": "Alta actividad",
            "confidence": 0.85,
            "generated_at": "2026-09-07T12:00:00Z",
        }
        mock_resp.raise_for_status = MagicMock()
        mock_httpx.get.return_value = mock_resp

        result = client.get_cell_risk("832bffffffffff")
        assert result is not None
        assert result["risk_score"] == 75.5
        assert result["source"] == "georisk"

    @patch("integrations.georisk_client.httpx")
    def test_get_cell_risk_timeout_returns_none(self, mock_httpx):
        import integrations.georisk_client as client
        client._cb_failures = 0
        client._cb_open_until = 0.0
        client._cache.clear()

        import httpx
        mock_httpx.TimeoutException = httpx.TimeoutException
        mock_httpx.get.side_effect = httpx.TimeoutException("timeout")

        result = client.get_cell_risk("832bffffffffff")
        assert result is None
        assert client._cb_failures == 1

    @patch("integrations.georisk_client.httpx")
    def test_get_cell_risk_http_error_returns_none(self, mock_httpx):
        import integrations.georisk_client as client
        client._cb_failures = 0
        client._cb_open_until = 0.0
        client._cache.clear()

        import httpx
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_httpx.HTTPStatusError = httpx.HTTPStatusError
        mock_httpx.get.side_effect = httpx.HTTPStatusError(
            "Server Error", request=MagicMock(), response=mock_resp
        )

        result = client.get_cell_risk("832bffffffffff")
        assert result is None

    def test_get_cell_risk_circuit_open_returns_none(self):
        import integrations.georisk_client as client
        client._cb_failures = 5
        client._cb_open_until = time.time() + 60

        result = client.get_cell_risk("832bffffffffff")
        assert result is None


# ---------------------------------------------------------------------------
# External Risk API endpoint tests
# ---------------------------------------------------------------------------
class TestExternalRiskAPI:
    """Tests for the /api/external-risk endpoints."""

    def test_import(self):
        from modules.external_risk.routes import router
        assert router is not None

    def test_router_prefix(self):
        from modules.external_risk.routes import router
        assert router.prefix == "/api/external-risk"

    def test_status_endpoint_when_available(self):
        from integrations.georisk_client import _cb_failures, _cb_open_until
        import integrations.georisk_client as client
        client._cb_failures = 0
        client._cb_open_until = 0.0

        from fastapi.testclient import TestClient
        from main import app
        client_test = TestClient(app, raise_server_exceptions=False)
        resp = client_test.get("/api/external-risk/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "georisk_available" in data
        assert "circuit_breaker" in data

    @patch("modules.external_risk.routes.get_cell_risk")
    @patch("modules.external_risk.routes.is_georisk_available")
    def test_cell_endpoint_when_available(self, mock_avail, mock_risk):
        mock_avail.return_value = True
        mock_risk.return_value = {
            "h3_index": "832bffffffffff",
            "risk_score": 75.5,
            "risk_level": "high",
            "source": "georisk",
        }

        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/api/external-risk/cell/832bffffffffff")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["data"]["risk_score"] == 75.5

    @patch("modules.external_risk.routes.is_georisk_available")
    def test_cell_endpoint_when_unavailable(self, mock_avail):
        mock_avail.return_value = False

        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/api/external-risk/cell/832bffffffffff")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "unavailable"
        assert "GeoRisk no disponible" in data["message"]

    @patch("modules.external_risk.routes.get_cell_risk")
    @patch("modules.external_risk.routes.is_georisk_available")
    def test_cell_endpoint_when_not_found(self, mock_avail, mock_risk):
        mock_avail.return_value = True
        mock_risk.return_value = None

        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/api/external-risk/cell/832bffffffffff")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "not_found"


# ---------------------------------------------------------------------------
# Decision Center integration with GeoRisk
# ---------------------------------------------------------------------------
class TestDecisionCenterGeoRisk:
    """Tests that the Decision Center includes GeoRisk data."""

    def test_decision_context_includes_georisk_field(self):
        from modules.decision_center.service import build_decision_context
        incident = {
            "latitud": 40.4168,
            "longitud": -3.7038,
            "severity": 0.7,
            "magnitude": 5.0,
            "event_type": "terremoto",
            "source": "USGS",
        }
        result = build_decision_context(incident)
        assert "georisk" in result
        assert "h3_index" in result

    def test_decision_context_h3_index_generated(self):
        from modules.decision_center.service import build_decision_context
        incident = {
            "latitud": 40.4168,
            "longitud": -3.7038,
            "severity": 0.5,
        }
        result = build_decision_context(incident)
        assert result["h3_index"] is not None
        assert isinstance(result["h3_index"], str)
        assert len(result["h3_index"]) > 0

    @patch("modules.decision_center.service.get_cell_risk")
    @patch("modules.decision_center.service.is_georisk_available")
    def test_decision_context_georisk_ok(self, mock_avail, mock_risk):
        mock_avail.return_value = True
        mock_risk.return_value = {
            "risk_score": 82.5,
            "risk_level": "high",
            "model_version": "georisk-v3",
            "source": "georisk",
        }
        from modules.decision_center.service import build_decision_context
        incident = {
            "latitud": 40.4168,
            "longitud": -3.7038,
            "severity": 0.7,
        }
        result = build_decision_context(incident)
        assert result["georisk"]["status"] == "ok"
        assert result["georisk"]["risk_score"] == 82.5

    @patch("modules.decision_center.service.is_georisk_available")
    def test_decision_context_georisk_unavailable(self, mock_avail):
        mock_avail.return_value = False
        from modules.decision_center.service import build_decision_context
        incident = {
            "latitud": 40.4168,
            "longitud": -3.7038,
            "severity": 0.5,
        }
        result = build_decision_context(incident)
        assert result["georisk"]["status"] == "unavailable"
