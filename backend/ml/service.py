"""ML Service para Anexo Risk — Capa de servicio para predicción explicable.

Proporciona:
- Carga del modelo desde artifact
- Predicción con metadata completa
- Explicación humana de la predicción
- Fallback a rules-v1 si ML no disponible
- Trazabilidad: model_version, training_date, methodology

IMPORTANTE: El modelo actual aprende scoring rule-based.
No es una predicción validada de resultados reales de emergencias.
"""
from __future__ import annotations

import json
import logging
import os
import pickle
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ml.pipeline import FEATURE_COLUMNS

logger = logging.getLogger(__name__)

ML_METHOD_VERSION = "ml-v1"
MODEL_DIR = os.getenv("ML_MODEL_DIR", "ml/artifacts")
MODEL_VERSION_FILE = os.getenv("ML_VERSION_FILE", "ml/artifacts/current_version.json")

_model_cache: dict[str, Any] | None = None
_model_meta_cache: dict[str, Any] | None = None


def _load_version_info() -> dict | None:
    """Carga la información de versión del modelo actual."""
    version_path = Path(MODEL_VERSION_FILE)
    if not version_path.exists():
        return None
    try:
        with open(version_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning("No se pudo leer current_version.json: %s", e)
        return None


def _load_model_from_artifact() -> tuple[Any, dict] | None:
    """Carga el modelo y scaler desde el artifact más reciente."""
    global _model_cache, _model_meta_cache

    if _model_cache is not None:
        return _model_cache, _model_meta_cache

    version_info = _load_version_info()
    if not version_info:
        logger.info("No hay modelo entrenado disponible (current_version.json no existe)")
        return None

    filename = version_info.get("filename")
    if not filename:
        logger.info("current_version.json no contiene campo 'filename'")
        return None

    artifact_path = Path(filename)
    if not artifact_path.exists():
        logger.info("Artifact no encontrado: %s", filename)
        return None

    try:
        with open(artifact_path, "rb") as f:
            artifact = pickle.load(f)
        _model_cache = artifact
        _model_meta_cache = {
            "version": artifact.get("version"),
            "model_type": artifact.get("model_type"),
            "metrics": artifact.get("metrics"),
            "feature_importance": artifact.get("feature_importance"),
            "trained_at": artifact.get("trained_at"),
        }
        logger.info(
            "Modelo ML cargado: version=%s, type=%s",
            artifact.get("version"),
            artifact.get("model_type"),
        )
        return _model_cache, _model_meta_cache
    except Exception as e:
        logger.error("Error cargando artifact ML: %s", e)
        return None


def is_ml_available() -> bool:
    """Verifica si el modelo ML está disponible y cargable."""
    try:
        result = _load_model_from_artifact()
        return result is not None
    except Exception:
        return False


def predict_with_explanation(
    event: dict,
    all_events: list[dict] | None = None,
    needs: list[dict] | None = None,
    resources: list[dict] | None = None,
) -> dict:
    """Predice prioridad con explicación completa y metadata.

    Parameters
    ----------
    event : dict
        Evento con latitud/lat, longitud/lon, severity, magnitude, depth, etc.
    all_events : list[dict] or None
        Todos los eventos para calcular densidad.
    needs : list[dict] or None
        Necesidades abiertas.
    resources : list[dict] or None
        Recursos disponibles.

    Returns
    -------
    dict
        Predicción con metadata, explicación, y fallback info.
    """
    model_data = _load_model_from_artifact()

    if model_data is None:
        return _build_ml_fallback("Modelo ML no disponible")

    model, meta = model_data
    model = model.get("model") if isinstance(model, dict) else model
    scaler = meta.get("scaler") if isinstance(meta, dict) else None

    if model is None or scaler is None:
        return _build_ml_fallback("Modelo o scaler no encontrado en artifact")

    lat = event.get("latitud") or event.get("lat", 0)
    lon = event.get("longitud") or event.get("lon", 0)

    features = _build_features_for_prediction(event, all_events, needs, resources)

    try:
        import numpy as np
        from sklearn.impute import SimpleImputer

        X = np.array([[features.get(f, 0) for f in FEATURE_COLUMNS]])

        imputer = SimpleImputer(strategy="median")
        X = imputer.fit_transform(X)

        X_scaled = scaler.transform(X)

        prediction = model.predict(X_scaled)[0]
        probabilities = model.predict_proba(X_scaled)[0]
        confidence = float(max(probabilities))

        classes = list(model.classes_)
        prob_dict = {cls: round(float(p), 4) for cls, p in zip(classes, probabilities)}

        top_features = _get_top_features(meta.get("feature_importance", {}))

        explanation = _build_human_explanation(
            prediction=prediction,
            confidence=confidence,
            model_type=meta.get("model_type", "unknown"),
            version=meta.get("version", "unknown"),
            top_features=top_features,
        )

        return {
            "prediction": prediction,
            "confidence": round(confidence, 4),
            "probabilities": prob_dict,
            "model_version": meta.get("version", "unknown"),
            "model_type": meta.get("model_type", "unknown"),
            "training_date": meta.get("trained_at"),
            "prediction_timestamp": datetime.now(timezone.utc).isoformat(),
            "methodology": ML_METHOD_VERSION,
            "methodology_version": ML_METHOD_VERSION,
            "source": "ml",
            "top_features": top_features,
            "explanation": explanation,
            "model_metrics": {
                "accuracy": meta.get("metrics", {}).get("accuracy"),
                "f1_weighted": meta.get("metrics", {}).get("f1_weighted"),
            },
            "available": True,
            "disclaimer": (
                "El modelo actual aprende scoring rule-based, "
                "no predice resultados reales de emergencias."
            ),
        }

    except Exception as e:
        logger.error("Error en predicción ML: %s", e)
        return _build_ml_fallback(f"Error en predicción: {e}")


def _build_features_for_prediction(
    event: dict,
    all_events: list[dict] | None,
    needs: list[dict] | None,
    resources: list[dict] | None,
) -> dict:
    """Construye features para predicción ML."""
    lat = event.get("latitud") or event.get("lat", 0)
    lon = event.get("longitud") or event.get("lon", 0)

    from geodata.services.spatial import find_nearby, haversine_distance

    event_density = 0.0
    if all_events and lat and lon:
        nearby = find_nearby(lat, lon, all_events, radius_km=100)
        event_density = min(len(nearby) / 10, 1.0)

    needs_open = 0
    if needs and lat and lon:
        nearby_needs = find_nearby(lat, lon, needs, radius_km=50)
        needs_open = len([n for n in nearby_needs if n.get("estado") == "abierta"])

    resources_nearby = 0
    if resources and lat and lon:
        nearby_res = find_nearby(lat, lon, resources, radius_km=50)
        resources_nearby = len([r for r in nearby_res if r.get("status") == "disponible"])

    from ml.pipeline import _estimate_distance_to_coast

    return {
        "depth": event.get("depth", 0),
        "event_density": event_density,
        "needs_open": needs_open,
        "resources_nearby": resources_nearby,
        "weather_score": 0.0,
        "distance_to_coast": _estimate_distance_to_coast(lat, lon),
    }


def _get_top_features(feature_importance: dict, n: int = 3) -> list[dict]:
    """Extrae las top N features con importancia > 0."""
    sorted_features = sorted(
        feature_importance.items(), key=lambda x: x[1], reverse=True
    )
    return [
        {"name": name, "importance": round(imp, 4)}
        for name, imp in sorted_features[:n]
        if imp > 0
    ]


def _build_human_explanation(
    prediction: str,
    confidence: float,
    model_type: str,
    version: str,
    top_features: list[dict],
) -> dict:
    """Construye explicación legible por humanos."""
    level_map = {
        "critico": "CRÍTICA",
        "alto": "ALTA",
        "medio": "MEDIA",
        "bajo": "BAJA",
        "informativo": "INFORMATIVA",
    }
    level_text = level_map.get(prediction, prediction.upper())

    features_text = ""
    if top_features:
        names = [f["name"] for f in top_features]
        features_text = ", ".join(names)

    summary = (
        f"Predicción ML: prioridad {level_text} "
        f"(confianza: {confidence:.0%}). "
        f"Modelo: {model_type} {version}. "
    )
    if features_text:
        summary += (
            f"Factores con mayor contribución para el modelo: {features_text}. "
        )
    summary += (
        "Nota: este modelo aprende scoring rule-based, "
        "no resultados reales de emergencias."
    )

    return {
        "summary": summary,
        "level": level_text,
        "confidence_pct": f"{confidence:.0%}",
        "model": f"{model_type} {version}",
        "top_factors": [
            f"{f['name']} (importancia: {f['importance']:.1%})"
            for f in top_features
        ],
        "methodology_note": (
            "El target está derivado de severidad del evento. "
            "Las features incluyen variables contextuales del evento."
        ),
    }


def _build_ml_fallback(reason: str) -> dict:
    """Construye respuesta de fallback cuando ML no está disponible."""
    return {
        "prediction": None,
        "confidence": None,
        "probabilities": None,
        "model_version": None,
        "model_type": None,
        "training_date": None,
        "prediction_timestamp": datetime.now(timezone.utc).isoformat(),
        "methodology": "rules-v1",
        "methodology_version": "rules-v1",
        "source": "rules",
        "top_features": [],
        "explanation": {
            "summary": f"ML no disponible — usando evaluación determinista. {reason}",
            "level": None,
            "confidence_pct": None,
            "model": None,
            "top_factors": [],
            "methodology_note": reason,
        },
        "model_metrics": None,
        "available": False,
        "disclaimer": reason,
    }


def clear_model_cache():
    """Limpia la caché del modelo (útil para testing)."""
    global _model_cache, _model_meta_cache
    _model_cache = None
    _model_meta_cache = None
