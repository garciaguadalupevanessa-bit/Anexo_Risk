"""Tests for FASE 4 — Region Sources + Normalized Adapters."""
import sys
import os
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
os.environ.setdefault("TESTING", "true")
os.environ.setdefault("JWT_SECRET_KEY", "test-fase4")
os.environ.setdefault("ANEXO_ADMIN_KEY", "test-fase4")

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app, raise_server_exceptions=False)


def _uid():
    return "f4_" + uuid.uuid4().hex[:8]


class TestRegionSourceResolution:
    """Test region→source resolution logic."""

    def test_global_source_applies_to_any_region(self):
        from services.region_source_resolution import _source_applies_to_region
        source = {"scope": "global", "id": "usgs"}
        region = {"country_code": "ES"}
        assert _source_applies_to_region(source, region, {}) is True

    def test_country_source_matches_country(self):
        from services.region_source_resolution import _source_applies_to_region
        source = {"scope": "country:ES", "id": "aemet"}
        region = {"country_code": "ES"}
        assert _source_applies_to_region(source, region, {}) is True

    def test_country_source_no_match(self):
        from services.region_source_resolution import _source_applies_to_region
        source = {"scope": "country:ES", "id": "aemet"}
        region = {"country_code": "FR"}
        assert _source_applies_to_region(source, region, {}) is False

    def test_explicit_link_takes_precedence(self):
        from services.region_source_resolution import _source_applies_to_region
        source = {"scope": "regional", "id": "local_source"}
        region = {"country_code": "ES"}
        config = {"is_enabled": True, "priority": 10}
        assert _source_applies_to_region(source, region, config) is True

    def test_disabled_link_returns_false(self):
        from services.region_source_resolution import _source_applies_to_region
        source = {"scope": "regional", "id": "local_source"}
        region = {"country_code": "ES"}
        config = {"is_enabled": False}
        assert _source_applies_to_region(source, region, config) is False

    def test_get_sources_for_region(self):
        from services.region_source_resolution import get_sources_for_region
        rid = _uid()
        client.post("/api/regions", json={"id": rid, "name": "Test", "country_code": "ES"})
        sources = get_sources_for_region(rid)
        assert isinstance(sources, list)
        assert len(sources) > 0
        # Global sources should be included
        ids = [s["id"] for s in sources]
        assert "usgs" in ids
        assert "gdacs" in ids

    def test_api_applicable_sources(self):
        rid = _uid()
        client.post("/api/regions", json={"id": rid, "name": "Test", "country_code": "ES"})
        r = client.get(f"/api/regions/{rid}/applicable-sources")
        assert r.status_code == 200
        assert r.json()["region_id"] == rid
        assert len(r.json()["sources"]) > 0

    def test_api_source_health(self):
        rid = _uid()
        client.post("/api/regions", json={"id": rid, "name": "Test", "country_code": "ES"})
        r = client.get(f"/api/regions/{rid}/source-health")
        assert r.status_code == 200
        assert len(r.json()["sources"]) > 0

    def test_region_not_found(self):
        r = client.get("/api/regions/NONEXISTENT/applicable-sources")
        assert r.status_code == 404


class TestNormalizedAdapters:
    """Test adapter normalization functions."""

    def test_normalize_gdacs(self):
        from services.normalized_adapters import normalize_gdacs_event
        event = {
            "id": "123",
            "tipo": "Earthquake",
            "titulo": "M6.0 Test",
            "descripcion": "Test earthquake",
            "severidad": "red",
            "pais": "Spain",
            "lat": 40.0,
            "lon": -3.0,
            "fecha": "2026-09-08T10:00:00Z",
        }
        result = normalize_gdacs_event(event)
        assert result.source == "gdacs"
        assert result.entity_type.value == "earthquake"
        assert result.severity == "red"
        assert result.severity_float == 1.0
        assert result.lat == 40.0
        assert result.provenance["source"] == "gdacs"

    def test_normalize_usgs(self):
        from services.normalized_adapters import normalize_usgs_event
        event = {
            "external_id": "us123",
            "title": "M5.2 Test",
            "magnitude": 5.2,
            "depth": 10.0,
            "latitud": 37.17,
            "longitud": -3.60,
            "event_time": "2026-09-08T10:00:00Z",
        }
        result = normalize_usgs_event(event)
        assert result.source == "usgs"
        assert result.entity_type.value == "earthquake"
        assert result.magnitude == 5.2
        assert result.severity_float == pytest.approx(5.2 / 8.0, abs=0.01)

    def test_normalize_firms(self):
        from services.normalized_adapters import normalize_firms_event
        event = {
            "id": "f1",
            "satellite": "VIIRS",
            "lat": 40.0,
            "lon": -3.0,
            "brightness": 320.5,
            "confidence": "high",
            "acq_date": "2026-09-08",
            "acq_time": "1200",
            "frp": 15.2,
        }
        result = normalize_firms_event(event)
        assert result.source == "firms"
        assert result.entity_type.value == "fire"
        assert result.confidence == 0.75

    def test_normalize_aemet(self):
        from services.normalized_adapters import normalize_aemet_event
        alert = {
            "id": "a1",
            "nivel": "naranja",
            "titulo": "High temperature alert",
            "lat": 40.0,
            "lon": -3.0,
            "fuente": "aemet",
        }
        result = normalize_aemet_event(alert)
        assert result.source == "aemet"
        assert result.entity_type.value == "weather"
        assert result.severity == "naranja"
        assert result.severity_float == 0.75

    def test_severity_from_float(self):
        from services.normalized_adapters import _severity_from_float
        assert _severity_from_float(0.9) == "rojo"
        assert _severity_from_float(0.6) == "naranja"
        assert _severity_from_float(0.3) == "amarillo"
        assert _severity_from_float(0.1) == "verde"
