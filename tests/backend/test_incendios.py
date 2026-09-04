"""Pruebas pytest del módulo de incendios (NASA FIRMS).

Valida schemas, cache, zonas y el endpoint FastAPI.
"""
from unittest.mock import patch, MagicMock

import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient

from modules.incendios.models import (
    FIRE_ZONES,
    fetch_fires,
    _CACHE,
    _CACHE_TIME,
)
from modules.incendios.schemas import FireDetection, FireResponse


# ---------------------------------------------------------------------------
# 1. Schema validation — FireDetection
# ---------------------------------------------------------------------------

def test_fire_detection_valid_data():
    """FireDetection acepta datos mínimos válidos."""
    det = FireDetection(
        id="VIIRS-2026-09-01-39.4-0.3",
        latitud=39.4,
        longitud=-0.3,
    )
    assert det.id == "VIIRS-2026-09-01-39.4-0.3"
    assert det.satellite == "VIIRS"
    assert det.confianza == "nominal"
    assert det.pais == "España"


def test_fire_detection_with_aliases():
    """FireDetection acepta alias en inglés (lat, lon, brightness, etc.)."""
    det = FireDetection(
        id="VIIRS-001",
        lat=40.0,
        lon=-3.0,
        brightness=350.5,
        confidence="high",
        country="España",
    )
    assert det.latitud == 40.0
    assert det.longitud == -3.0
    assert det.brillo == 350.5
    assert det.confianza == "high"


@pytest.mark.parametrize("lat,lon", [
    (91, 0),
    (-91, 0),
    (0, 181),
    (0, -181),
])
def test_fire_detection_rejects_out_of_range(lat, lon):
    """Rechaza latitud/longitud fuera del rango válido."""
    with pytest.raises(ValidationError):
        FireDetection(id="X", latitud=lat, longitud=lon)


def test_fire_detection_missing_required_id():
    """El campo id es obligatorio."""
    with pytest.raises(ValidationError):
        FireDetection(latitud=39.4, longitud=-0.3)


def test_fire_detection_extra_fields_ignored():
    """Campos extra se ignoran (extra='ignore')."""
    det = FireDetection(id="X", latitud=39.4, longitud=-0.3, invented=42)
    assert det.id == "X"


# ---------------------------------------------------------------------------
# 2. FireResponse schema
# ---------------------------------------------------------------------------

def test_fire_response_error_is_optional():
    """El campo error es Optional; sin error se queda None."""
    resp = FireResponse()
    assert resp.error is None
    assert resp.total == 0
    assert resp.detecciones == []


def test_fire_response_with_error():
    """FireResponse acepta un mensaje de error."""
    resp = FireResponse(
        total=0,
        detecciones=[],
        error="Configura NASA_FIRMS_API_KEY en .env",
    )
    assert resp.error == "Configura NASA_FIRMS_API_KEY en .env"


def test_fire_response_with_detections():
    """FireResponse modeliza una lista de detecciones completa."""
    det = FireDetection(
        id="VIIRS-001",
        latitud=39.4,
        longitud=-0.3,
        brillo=310.2,
        confianza="high",
    )
    resp = FireResponse(total=1, detecciones=[det])
    assert len(resp.detecciones) == 1
    assert resp.detecciones[0].brillo == 310.2


# ---------------------------------------------------------------------------
# 3. fetch_fires without API key
# ---------------------------------------------------------------------------

def test_fetch_fires_without_api_key():
    """Sin API key configurada devuelve error dict sin lanzar excepción."""
    with patch("modules.incendios.models.NASA_FIRMS_API_KEY", ""):
        result = fetch_fires(force_refresh=True)

    assert result["total"] == 0
    assert result["detecciones"] == []
    assert "error" in result
    assert "NASA_FIRMS_API_KEY" in result["error"]


# ---------------------------------------------------------------------------
# 4. fetch_fires cache
# ---------------------------------------------------------------------------

def test_fetch_fires_caches_result():
    """La segunda llamada sin force_refresh devuelve el cache sin llamar a la API."""
    with patch("modules.incendios.models.NASA_FIRMS_API_KEY", "dummy-key"):
        with patch("modules.incendios.models.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.text = "latitude,longitude,bright_ti4,confidence,acq_date,acq_time,frp\n"
            mock_resp.raise_for_status = MagicMock()
            mock_get.return_value = mock_resp

            result1 = fetch_fires(force_refresh=True)
            result2 = fetch_fires(force_refresh=False)

            assert result1 == result2
            assert mock_get.call_count == 1


def test_fetch_fires_force_refresh_skips_cache():
    """force_refresh=True siempre llama a la API."""
    with patch("modules.incendios.models.NASA_FIRMS_API_KEY", "dummy-key"):
        with patch("modules.incendios.models.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.text = "latitude,longitude,bright_ti4,confidence,acq_date,acq_time,frp\n"
            mock_resp.raise_for_status = MagicMock()
            mock_get.return_value = mock_resp

            fetch_fires(force_refresh=True)
            fetch_fires(force_refresh=True)

            assert mock_get.call_count == 2


# ---------------------------------------------------------------------------
# 5. Zone parameter — FIRE_ZONES
# ---------------------------------------------------------------------------

def test_fire_zones_has_expected_keys():
    """FIRE_ZONES contiene las 4 zonas esperadas."""
    expected = {"spain", "europa", "mediterraneo", "global"}
    assert expected == set(FIRE_ZONES.keys())


@pytest.mark.parametrize("zone", ["spain", "europa", "mediterraneo", "global"])
def test_fire_zones_bbox_format(zone):
    """Cada zona tiene un bbox con 4 valores separados por comas."""
    bbox = FIRE_ZONES[zone]
    parts = bbox.split(",")
    assert len(parts) == 4
    floats = [float(p) for p in parts]
    assert floats[0] < floats[2]  # west < east
    assert floats[1] < floats[3]  # south < north


def test_fetch_fires_invalid_zone_falls_back_to_spain():
    """Una zona desconocida usa el bbox de spain por defecto."""
    with patch("modules.incendios.models.NASA_FIRMS_API_KEY", "dummy-key"):
        with patch("modules.incendios.models.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.text = "latitude,longitude,bright_ti4,confidence,acq_date,acq_time,frp\n"
            mock_resp.raise_for_status = MagicMock()
            mock_get.return_value = mock_resp

            fetch_fires(force_refresh=True, zone="inexistente")

            called_url = mock_get.call_args[0][0]
            assert FIRE_ZONES["spain"] in called_url


# ---------------------------------------------------------------------------
# 6-8. Route endpoints via TestClient
# ---------------------------------------------------------------------------

@pytest.fixture()
def client():
    """TestClient ligero que evita montar archivos estáticos del frontend."""
    from main import app
    return TestClient(app, raise_server_exceptions=False)


def test_get_incendios_endpoint(client):
    """GET /api/incendios devuelve 200 con estructura FireResponse."""
    with patch("modules.incendios.models.NASA_FIRMS_API_KEY", ""):
        resp = client.get("/api/incendios")

    assert resp.status_code == 200
    body = resp.json()
    assert "total" in body
    assert "detecciones" in body
    assert "error" in body


def test_get_incendios_with_zone(client):
    """GET /api/incendios?zone=europa acepta la zona sin errores."""
    with patch("modules.incendios.models.NASA_FIRMS_API_KEY", ""):
        resp = client.get("/api/incendios", params={"zone": "europa"})

    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body["detecciones"], list)


def test_get_incendios_with_refresh(client):
    """GET /api/incendios?refresh=true fuerza recarga (force_refresh=True)."""
    with patch("modules.incendios.models.NASA_FIRMS_API_KEY", "dummy-key"):
        with patch("modules.incendios.models.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.text = "latitude,longitude,bright_ti4,confidence,acq_date,acq_time,frp\n"
            mock_resp.raise_for_status = MagicMock()
            mock_get.return_value = mock_resp

            client.get("/api/incendios", params={"refresh": "true"})
            client.get("/api/incendios", params={"refresh": "true"})

            # Cada llamada con refresh=true fuerza request nuevo
            assert mock_get.call_count == 2
