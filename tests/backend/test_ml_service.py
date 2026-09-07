"""Tests para ML Service — FASE B: ML Explicable."""
import sys
import os
import json
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))


class TestMLServiceMetadata:
    """Tests para metadata de predicción ML."""

    def test_prediction_has_required_metadata_fields(self):
        from ml.service import predict_with_explanation

        event = {
            "latitud": 37.17,
            "longitud": -3.60,
            "severity": 0.5,
            "magnitude": 4.2,
            "depth": 10.0,
        }
        result = predict_with_explanation(event)

        assert "prediction" in result
        assert "confidence" in result
        assert "model_version" in result
        assert "model_type" in result
        assert "training_date" in result
        assert "prediction_timestamp" in result
        assert "methodology" in result
        assert "methodology_version" in result
        assert "source" in result
        assert "top_features" in result
        assert "explanation" in result
        assert "available" in result
        assert "disclaimer" in result

    def test_prediction_source_is_ml_when_available(self):
        from ml.service import predict_with_explanation

        event = {
            "latitud": 37.17,
            "longitud": -3.60,
            "severity": 0.5,
            "magnitude": 4.2,
            "depth": 10.0,
        }
        result = predict_with_explanation(event)

        if result.get("available"):
            assert result["source"] == "ml"
            assert result["methodology"] == "ml-v1"
            assert result["methodology_version"] == "ml-v1"

    def test_prediction_timestamp_is_iso(self):
        from ml.service import predict_with_explanation

        event = {"latitud": 37.17, "longitud": -3.60, "severity": 0.5}
        result = predict_with_explanation(event)

        ts = result.get("prediction_timestamp", "")
        assert "T" in ts
        assert "Z" in ts or "+" in ts


class TestMLServiceExplanation:
    """Tests para explicación humana."""

    def test_explanation_has_summary(self):
        from ml.service import predict_with_explanation

        event = {"latitud": 37.17, "longitud": -3.60, "severity": 0.8, "depth": 5.0}
        result = predict_with_explanation(event)

        explanation = result.get("explanation", {})
        assert "summary" in explanation
        assert len(explanation["summary"]) > 0

    def test_explanation_mentions_model_type(self):
        from ml.service import predict_with_explanation

        event = {"latitud": 37.17, "longitud": -3.60, "severity": 0.5, "depth": 10.0}
        result = predict_with_explanation(event)

        explanation = result.get("explanation", {})
        if result.get("available"):
            assert "model" in explanation
            assert "GradientBoosting" in explanation.get("model", "") or "ml-v1" in explanation.get("model", "")

    def test_explanation_does_not_claim_causality(self):
        from ml.service import predict_with_explanation

        event = {"latitud": 37.17, "longitud": -3.60, "severity": 0.5, "depth": 10.0}
        result = predict_with_explanation(event)

        summary = result.get("explanation", {}).get("summary", "").lower()
        assert "causa" not in summary
        assert "causal" not in summary

    def test_explanation_disclaimer_present(self):
        from ml.service import predict_with_explanation

        event = {"latitud": 37.17, "longitud": -3.60, "severity": 0.5}
        result = predict_with_explanation(event)

        assert "disclaimer" in result
        assert len(result["disclaimer"]) > 0


class TestMLServiceFallback:
    """Tests para fallback cuando ML no está disponible."""

    def test_fallback_when_no_model(self):
        from ml.service import predict_with_explanation, clear_model_cache

        clear_model_cache()
        with patch("ml.service._load_model_from_artifact", return_value=None):
            event = {"latitud": 37.17, "longitud": -3.60, "severity": 0.5}
            result = predict_with_explanation(event)

            assert result["available"] is False
            assert result["source"] == "rules"
            assert result["prediction"] is None
            assert result["confidence"] is None
            assert "ML no disponible" in result["explanation"]["summary"]

    def test_fallback_has_rules_source(self):
        from ml.service import predict_with_explanation, clear_model_cache

        clear_model_cache()
        with patch("ml.service._load_model_from_artifact", return_value=None):
            event = {"latitud": 37.17, "longitud": -3.60, "severity": 0.5}
            result = predict_with_explanation(event)

            assert result["methodology"] == "rules-v1"
            assert result["source"] == "rules"

    def test_fallback_graceful_degradation(self):
        from ml.service import predict_with_explanation

        event = {"latitud": 37.17, "longitud": -3.60, "severity": 0.5}
        result = predict_with_explanation(event)

        assert "prediction" in result
        assert "confidence" in result
        assert "explanation" in result
        assert isinstance(result["explanation"], dict)


class TestMLServiceModelLoading:
    """Tests para carga del modelo."""

    def test_is_ml_available_returns_bool(self):
        from ml.service import is_ml_available

        result = is_ml_available()
        assert isinstance(result, bool)

    def test_clear_model_cache_works(self):
        from ml.service import clear_model_cache, _model_cache

        clear_model_cache()
        from ml.service import _model_cache as cache
        assert cache is None


class TestMLServiceFeatures:
    """Tests para features de predicción."""

    def test_prediction_with_minimal_event(self):
        from ml.service import predict_with_explanation

        event = {"latitud": 0.0, "longitud": 0.0, "severity": 0.5}
        result = predict_with_explanation(event)

        assert "prediction" in result
        assert "confidence" in result

    def test_prediction_with_all_features(self):
        from ml.service import predict_with_explanation

        event = {
            "latitud": 37.17,
            "longitud": -3.60,
            "severity": 0.7,
            "magnitude": 5.0,
            "depth": 15.0,
        }
        needs = [{"latitud": 37.2, "longitud": -3.5, "estado": "abierta"}]
        resources = [{"latitud": 37.15, "longitud": -3.65, "status": "disponible"}]

        result = predict_with_explanation(
            event=event,
            needs=needs,
            resources=resources,
        )

        assert "prediction" in result
        assert "top_features" in result


class TestRiskEngineWithML:
    """Tests para Risk Engine con integración ML."""

    def test_risk_engine_rules_only(self):
        from geodata.services.risk_engine import calculate_risk_score

        result = calculate_risk_score(
            severity=0.8,
            exposure=0.5,
            weather=0.3,
            event_density=0.4,
            needs_open=2,
            trend=0.1,
        )

        assert result["source"] == "rules"
        assert result["methodology_version"] == "rules-v1"
        assert result["ml_confidence"] is None

    def test_risk_engine_with_ml_prediction(self):
        from geodata.services.risk_engine import calculate_risk_score

        ml_pred = {
            "prediction": "alto",
            "confidence": 0.85,
            "available": True,
            "top_features": [{"name": "depth", "importance": 0.6}],
        }

        result = calculate_risk_score(
            severity=0.6,
            exposure=0.5,
            weather=0.3,
            event_density=0.4,
            needs_open=2,
            trend=0.1,
            ml_prediction=ml_pred,
        )

        assert result["source"] == "rules+ml"
        assert result["ml_confidence"] == 0.85
        assert result["ml_risk_score"] is not None

    def test_risk_engine_ml_low_confidence_fallback(self):
        from geodata.services.risk_engine import calculate_risk_score

        ml_pred = {
            "prediction": "alto",
            "confidence": 0.3,
            "available": True,
            "top_features": [],
        }

        result = calculate_risk_score(
            severity=0.6,
            exposure=0.5,
            weather=0.3,
            event_density=0.4,
            needs_open=2,
            trend=0.1,
            ml_prediction=ml_pred,
        )

        assert result["source"] == "rules"
        assert result["ml_confidence"] == 0.3

    def test_risk_engine_ml_unavailable(self):
        from geodata.services.risk_engine import calculate_risk_score

        ml_pred = {
            "prediction": None,
            "confidence": None,
            "available": False,
            "disclaimer": "Modelo no cargado",
        }

        result = calculate_risk_score(
            severity=0.6,
            exposure=0.5,
            weather=0.3,
            event_density=0.4,
            needs_open=2,
            trend=0.1,
            ml_prediction=ml_pred,
        )

        assert result["source"] == "rules"
        assert any("ML no disponible" in f for f in result["factors"])

    def test_risk_engine_has_methodology_version(self):
        from geodata.services.risk_engine import calculate_risk_score

        result = calculate_risk_score(severity=0.5)
        assert "methodology_version" in result
        assert "generated_at" in result
        assert "source" in result


class TestAPIEndpoint:
    """Tests para el endpoint de risk con ML."""

    def test_risk_endpoint_returns_ml_info(self):
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app, raise_server_exceptions=False)

        response = client.get(
            "/api/geodata/risk",
            params={
                "lat": 37.17,
                "lon": -3.60,
                "severity": 0.6,
                "weather": 0.3,
                "event_density": 0.4,
                "needs_open": 2,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "combined_score" in data
        assert "priority_level" in data
        assert "source" in data
        assert "methodology_version" in data
        assert "factors" in data
        assert "explanation" in data
        assert "generated_at" in data

    def test_decision_context_has_ml_info(self):
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app, raise_server_exceptions=False)

        response = client.get(
            "/api/decision/context",
            params={
                "lat": 37.17,
                "lon": -3.60,
                "severity": 0.6,
                "magnitude": 4.5,
                "event_type": "terremoto",
                "source": "usgs",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "risk" in data
        assert "source" in data["risk"]
        assert "methodology_version" in data["risk"]
        assert "ml_info" in data["risk"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
