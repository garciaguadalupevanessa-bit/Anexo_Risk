"""Tests del módulo de clima: esquemas, constantes, rutas y caché.

Prueba la validación Pydantic, el endpoint HTTP y el comportamiento
de caché del servicio meteorológico (AEMET → Open-Meteo fallback).
"""
import time
from unittest.mock import patch, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from modules.clima import models
from modules.clima import routes as clima_routes
from modules.clima.models import SPAIN_ZONES, fetch_weather, _CACHE, _CACHE_TIME, CACHE_TTL
from modules.clima.routes import router
from modules.clima.schemas import WeatherAlert, WeatherResponse


# ──────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_cache():
    """Resetea la caché global antes de cada prueba."""
    models._CACHE = None
    models._CACHE_TIME = 0
    yield
    models._CACHE = None
    models._CACHE_TIME = 0


@pytest.fixture
def client():
    """Crea un cliente HTTP aislado para probar el router de clima."""
    test_app = FastAPI()
    test_app.include_router(router)
    return TestClient(test_app)


# ──────────────────────────────────────────────
# 1. Schema validation — WeatherAlert
# ──────────────────────────────────────────────

def test_weather_alert_valid_data():
    """WeatherAlert acepta datos completos y válidos."""
    alert = WeatherAlert(
        id="om-heat-Madrid-2026",
        tipo="calor",
        nivel="naranja",
        titulo="Temperatura extrema en Madrid: 40°C",
        descripcion="Riesgo alto para la salud.",
        region="Madrid",
        fecha="2026-09-04T12:00",
        fuente="Open-Meteo",
    )
    assert alert.id == "om-heat-Madrid-2026"
    assert alert.tipo == "calor"
    assert alert.nivel == "naranja"
    assert alert.fuente == "Open-Meteo"


def test_weather_alert_defaults():
    """WeatherAlert aplica valores por defecto para campos opcionales."""
    alert = WeatherAlert(
        id="test-1",
        tipo="viento",
        nivel="rojo",
        titulo="Ráfagas fuertes",
        fuente="AEMET",
    )
    assert alert.descripcion == ""
    assert alert.region == "España"
    assert alert.fecha == ""


def test_weather_alert_rejects_missing_required_fields():
    """WeatherAlert rechaza la creación sin campos obligatorios."""
    with pytest.raises(ValidationError):
        WeatherAlert()

    with pytest.raises(ValidationError):
        WeatherAlert(id="x", tipo="lluvia")

    with pytest.raises(ValidationError):
        WeatherAlert(id="x", tipo="lluvia", nivel="amarillo")


def test_weather_alert_rejects_long_fields():
    """WeatherAlert rechaza valores que exceden los límites de longitud."""
    with pytest.raises(ValidationError):
        WeatherAlert(
            id="x" * 101,
            tipo="calor",
            nivel="rojo",
            titulo="ok",
            fuente="test",
        )

    with pytest.raises(ValidationError):
        WeatherAlert(
            id="x",
            tipo="calor",
            nivel="rojo",
            titulo="x" * 301,
            fuente="test",
        )


def test_weather_alert_extra_fields_ignored():
    """WeatherAlert ignora campos extra (config extra='ignore')."""
    alert = WeatherAlert(
        id="test",
        tipo="nieve",
        nivel="verde",
        titulo="Nieve",
        fuente="AEMET",
        campo_inesperado="debería ignorarse",
    )
    assert alert.id == "test"
    assert not hasattr(alert, "campo_inesperado")


# ──────────────────────────────────────────────
# 2. WeatherResponse schema
# ──────────────────────────────────────────────

def test_weather_response_defaults():
    """WeatherResponse tiene valores por defecto sensatos."""
    resp = WeatherResponse()
    assert resp.total == 0
    assert resp.alertas == []
    assert resp.fuente == "Open-Meteo"
    assert resp.cached_at is None
    assert resp.fallback_activado is False
    assert resp.error is None


def test_weather_response_error_is_optional():
    """El campo error es Optional y puede ser None o un string."""
    resp_ok = WeatherResponse(error=None)
    assert resp_ok.error is None

    resp_err = WeatherResponse(error="Ninguna fuente disponible")
    assert resp_err.error == "Ninguna fuente disponible"


def test_weather_response_with_alerts():
    """WeatherResponse acepta una lista de WeatherAlert."""
    alert = WeatherAlert(
        id="a1",
        tipo="lluvia",
        nivel="amarillo",
        titulo="Lluvia moderada",
        fuente="Open-Meteo",
    )
    resp = WeatherResponse(total=1, alertas=[alert], fuente="Open-Meteo")
    assert resp.total == 1
    assert len(resp.alertas) == 1
    assert resp.alertas[0].id == "a1"


def test_weather_response_serializes_correctly():
    """WeatherResponse serializa a JSON con los nombres del contrato."""
    resp = WeatherResponse(
        total=1,
        alertas=[],
        fuente="AEMET",
        cached_at="2026-09-04T12:00:00",
        fallback_activado=True,
        error=None,
    )
    dumped = resp.model_dump(mode="json")
    assert dumped["total"] == 1
    assert dumped["fuente"] == "AEMET"
    assert dumped["fallback_activado"] is True
    assert dumped["error"] is None


# ──────────────────────────────────────────────
# 3. SPAIN_ZONES constant
# ──────────────────────────────────────────────

def test_spain_zones_has_seven_cities():
    """SPAIN_ZONES contiene exactamente 7 ciudades españolas."""
    assert len(SPAIN_ZONES) == 7


def test_spain_zones_city_names():
    """SPAIN_ZONES incluye las 7 ciudades configuradas."""
    names = {z["name"] for z in SPAIN_ZONES}
    expected = {"Madrid", "Barcelona", "Valencia", "Sevilla", "Bilbao", "Zaragoza", "Málaga"}
    assert names == expected


def test_spain_zones_have_lat_lon():
    """Cada zona tiene latitud y longitud dentro de rangos válidos."""
    for zone in SPAIN_ZONES:
        assert "lat" in zone
        assert "lon" in zone
        assert -90 <= zone["lat"] <= 90
        assert -180 <= zone["lon"] <= 180


# ──────────────────────────────────────────────
# 4. Route endpoint — GET /api/clima
# ──────────────────────────────────────────────

SAMPLE_WEATHER_RESULT = {
    "total": 2,
    "alertas": [
        {
            "id": "om-heat-Madrid-2026",
            "tipo": "calor",
            "nivel": "naranja",
            "titulo": "Temperatura extrema en Madrid: 40°C",
            "descripcion": "Riesgo alto.",
            "region": "Madrid",
            "fecha": "2026-09-04T12:00",
            "fuente": "Open-Meteo",
        },
        {
            "id": "om-wind-Sevilla-2026",
            "tipo": "viento",
            "nivel": "rojo",
            "titulo": "Ráfagas en Sevilla: 80 km/h",
            "descripcion": "Precaución.",
            "region": "Sevilla",
            "fecha": "2026-09-04T12:00",
            "fuente": "Open-Meteo",
        },
    ],
    "fuente": "Open-Meteo (fallback)",
    "cached_at": "2026-09-04T12:00:00",
    "fallback_activado": True,
}


def test_get_weather_returns_200(client, monkeypatch):
    """GET /api/clima devuelve código 200 con datos válidos."""
    monkeypatch.setattr(clima_routes, "fetch_weather", lambda force_refresh=False: SAMPLE_WEATHER_RESULT)

    response = client.get("/api/clima")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert len(body["alertas"]) == 2
    assert body["alertas"][0]["tipo"] == "calor"
    assert body["alertas"][1]["tipo"] == "viento"


def test_get_weather_empty_response(client, monkeypatch):
    """GET /api/clima devuelve lista vacía cuando no hay alertas."""
    monkeypatch.setattr(
        clima_routes,
        "fetch_weather",
        lambda force_refresh=False: {
            "total": 0,
            "alertas": [],
            "fuente": "Open-Meteo",
            "cached_at": "2026-09-04T12:00:00",
            "fallback_activado": False,
        },
    )

    response = client.get("/api/clima")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 0
    assert body["alertas"] == []


def test_get_weather_error_response(client, monkeypatch):
    """GET /api/clima maneja errores devueltos por el servicio."""
    monkeypatch.setattr(
        clima_routes,
        "fetch_weather",
        lambda force_refresh=False: {
            "total": 0,
            "alertas": [],
            "fuente": "AEMET + Open-Meteo",
            "cached_at": "2026-09-04T12:00:00",
            "fallback_activado": True,
            "error": "Ninguna fuente de clima disponible",
        },
    )

    response = client.get("/api/clima")

    assert response.status_code == 200
    body = response.json()
    assert body["error"] == "Ninguna fuente de clima disponible"
    assert body["total"] == 0


# ──────────────────────────────────────────────
# 5. Route with refresh — ?refresh=true
# ──────────────────────────────────────────────

def test_get_weather_with_refresh_forces_fresh_data(client, monkeypatch):
    """GET /api/clima?refresh=true pasa force_refresh=True al servicio."""
    received_args = {}

    def fake_fetch(force_refresh=False):
        received_args["force_refresh"] = force_refresh
        return SAMPLE_WEATHER_RESULT

    monkeypatch.setattr(clima_routes, "fetch_weather", fake_fetch)

    response = client.get("/api/clima", params={"refresh": "true"})

    assert response.status_code == 200
    assert received_args["force_refresh"] is True


def test_get_weather_without_refresh_uses_cache(client, monkeypatch):
    """GET /api/clima sin refresh pasa force_refresh=False (default)."""
    received_args = {}

    def fake_fetch(force_refresh=False):
        received_args["force_refresh"] = force_refresh
        return SAMPLE_WEATHER_RESULT

    monkeypatch.setattr(clima_routes, "fetch_weather", fake_fetch)

    response = client.get("/api/clima")

    assert response.status_code == 200
    assert received_args["force_refresh"] is False


# ──────────────────────────────────────────────
# 6. Cache behavior
# ──────────────────────────────────────────────

def test_fetch_weather_returns_cache_when_valid(monkeypatch):
    """fetch_weather retorna caché si no ha expirado."""
    fake_response = SAMPLE_WEATHER_RESULT.copy()
    call_count = {"n": 0}

    def fake_open_meteo():
        call_count["n"] += 1
        return []

    monkeypatch.setattr(models, "_fetch_aemet", lambda: None)
    monkeypatch.setattr(models, "_fetch_open_meteo", fake_open_meteo)

    # Primera llamada → fetch real
    result1 = fetch_weather(force_refresh=False)
    assert call_count["n"] == 1

    # Segunda llamada → caché (noincrementa call_count)
    result2 = fetch_weather(force_refresh=False)
    assert call_count["n"] == 1
    assert result2["cached_at"] == result1["cached_at"]


def test_fetch_weather_force_refresh_bypasses_cache(monkeypatch):
    """force_refresh=True ignora la caché y vuelve a consultar."""
    call_count = {"n": 0}

    def fake_open_meteo():
        call_count["n"] += 1
        return []

    monkeypatch.setattr(models, "_fetch_aemet", lambda: None)
    monkeypatch.setattr(models, "_fetch_open_meteo", fake_open_meteo)

    fetch_weather(force_refresh=False)
    assert call_count["n"] == 1

    fetch_weather(force_refresh=True)
    assert call_count["n"] == 2


def test_fetch_weather_cache_expires_after_ttl(monkeypatch):
    """La caché expira después de CACHE_TTL segundos."""
    call_count = {"n": 0}

    def fake_open_meteo():
        call_count["n"] += 1
        return []

    monkeypatch.setattr(models, "_fetch_aemet", lambda: None)
    monkeypatch.setattr(models, "_fetch_open_meteo", fake_open_meteo)

    fetch_weather(force_refresh=False)
    assert call_count["n"] == 1

    # Simular expiración de caché
    models._CACHE_TIME = time.time() - CACHE_TTL - 1

    fetch_weather(force_refresh=False)
    assert call_count["n"] == 2


def test_fetch_weather_fallback_error_cached(monkeypatch):
    """Cuando ambas fuentes fallan, el error se cachea."""
    monkeypatch.setattr(models, "_fetch_aemet", lambda: None)
    monkeypatch.setattr(models, "_fetch_open_meteo", lambda: None)

    result = fetch_weather(force_refresh=False)

    assert result["error"] == "Ninguna fuente de clima disponible"
    assert result["total"] == 0
    assert result["fallback_activado"] is True

    # La caché válida evita llamadas posteriores
    result2 = fetch_weather(force_refresh=False)
    assert result2["error"] == "Ninguna fuente de clima disponible"


def test_is_cache_valid_returns_false_when_empty():
    """_is_cache_valid retorna False si no hay caché."""
    models._CACHE = None
    models._CACHE_TIME = 0
    assert models._is_cache_valid() is False


def test_is_cache_valid_returns_true_when_recent():
    """_is_cache_valid retorna True si la caché está dentro del TTL."""
    models._CACHE = {"test": True}
    models._CACHE_TIME = time.time()
    assert models._is_cache_valid() is True


def test_is_cache_valid_returns_false_when_expired():
    """_is_cache_valid retorna False si la caché ha expirado."""
    models._CACHE = {"test": True}
    models._CACHE_TIME = time.time() - CACHE_TTL - 1
    assert models._is_cache_valid() is False
