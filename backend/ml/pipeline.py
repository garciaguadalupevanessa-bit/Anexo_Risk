"""Pipeline ML para Anexo Risk — Construcción de dataset histórico y modelos.

Pipeline:
raw → clean → normalize → features → dataset → train/test → model → evaluation → artifact

Target: Clasificación de prioridad operacional (crítico/alto/medio/bajo)
basado en features geoespaciales y meteorológicas.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
    from sklearn.metrics import accuracy_score, classification_report, f1_score
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


FEATURE_COLUMNS = [
    "severity",
    "magnitude",
    "depth",
    "latitude",
    "longitude",
    "event_density",
    "needs_open",
    "resources_nearby",
    "weather_score",
    "distance_to_coast",
]

TARGET_COLUMN = "priority_level"


def build_features_from_events(events: list[dict]) -> list[dict]:
    """Convierte eventos crudos en features para ML.

    Parameters
    ----------
    events : list[dict]
        Eventos con campos normalizados.

    Returns
    -------
    list[dict]
        Lista de feature vectors.
    """
    features = []
    for event in events:
        lat = event.get("latitud") or event.get("lat", 0)
        lon = event.get("longitud") or event.get("lon", 0)

        feature = {
            "severity": event.get("severity", 0),
            "magnitude": event.get("magnitude", 0),
            "depth": event.get("depth", 0),
            "latitude": lat,
            "longitude": lon,
            "event_density": event.get("event_density", 0),
            "needs_open": event.get("needs_open", 0),
            "resources_nearby": event.get("resources_nearby", 0),
            "weather_score": event.get("weather_score", 0),
            "distance_to_coast": _estimate_distance_to_coast(lat, lon),
        }
        features.append(feature)
    return features


def create_target_from_rules(events: list[dict]) -> list[str]:
    """Genera target usando reglas deterministas (baseline).

    Target: prioridad operacional basada en severidad + exposición.
    """
    targets = []
    for event in events:
        severity = event.get("severity", 0)
        needs = event.get("needs_open", 0)
        density = event.get("event_density", 0)

        score = severity * 0.5 + min(needs / 5, 1.0) * 0.3 + density * 0.2

        if score >= 0.7:
            targets.append("critico")
        elif score >= 0.5:
            targets.append("alto")
        elif score >= 0.3:
            targets.append("medio")
        else:
            targets.append("bajo")
    return targets


def build_dataset(
    events: list[dict],
    targets: list[str] | None = None,
) -> dict:
    """Construye dataset para entrenamiento.

    Returns
    -------
    dict
        dataset con X, y, feature_names, metadata.
    """
    if not HAS_PANDAS:
        raise RuntimeError("pandas requerido para ML pipeline")

    features = build_features_from_events(events)
    df = pd.DataFrame(features)

    if targets is None:
        targets = create_target_from_rules(events)
    df[TARGET_COLUMN] = targets

    metadata = {
        "n_samples": len(df),
        "n_features": len(FEATURE_COLUMNS),
        "feature_names": FEATURE_COLUMNS,
        "target_distribution": df[TARGET_COLUMN].value_counts().to_dict(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    return {
        "X": df[FEATURE_COLUMNS].values,
        "y": df[TARGET_COLUMN].values,
        "feature_names": FEATURE_COLUMNS,
        "df": df,
        "metadata": metadata,
    }


def train_model(
    X: np.ndarray,
    y: np.ndarray,
    feature_names: list[str],
    model_type: str = "gradient_boosting",
    test_size: float = 0.2,
    random_state: int = 42,
) -> dict:
    """Entrena un modelo de clasificación.

    Parameters
    ----------
    X : np.ndarray
        Features.
    y : np.ndarray
        Target.
    feature_names : list[str]
        Nombres de features.
    model_type : str
        'random_forest' o 'gradient_boosting'.
    test_size : float
        Proporción de test.
    random_state : int
        Semilla aleatoria.

    Returns
    -------
    dict
        result con model, metrics, feature_importance, scaler.
    """
    if not HAS_SKLEARN:
        raise RuntimeError("scikit-learn requerido para ML")

    # Handle NaN values
    X = np.nan_to_num(X, nan=0.0)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    if model_type == "random_forest":
        model = RandomForestClassifier(
            n_estimators=100, random_state=random_state, n_jobs=-1
        )
    else:
        model = GradientBoostingClassifier(
            n_estimators=100, random_state=random_state
        )

    model.fit(X_train_scaled, y_train)

    y_pred = model.predict(X_test_scaled)

    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average="weighted")

    report = classification_report(y_test, y_pred, output_dict=True)

    if hasattr(model, "feature_importances_"):
        importance = dict(zip(feature_names, model.feature_importances_))
        importance = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
    else:
        importance = {}

    return {
        "model": model,
        "scaler": scaler,
        "metrics": {
            "accuracy": round(accuracy, 4),
            "f1_weighted": round(f1, 4),
            "classification_report": report,
        },
        "feature_importance": importance,
        "model_type": model_type,
        "n_train": len(X_train),
        "n_test": len(X_test),
        "trained_at": datetime.now(timezone.utc).isoformat(),
    }


def predict_priority(
    model,
    scaler,
    features: dict,
) -> dict:
    """Predice prioridad operacional para un nuevo evento.

    Returns
    -------
    dict
        prediction con level, confidence, probabilities.
    """
    if not HAS_SKLEARN:
        raise RuntimeError("scikit-learn requerido para predicción")

    X = np.array([[features.get(f, 0) for f in FEATURE_COLUMNS]])
    X_scaled = scaler.transform(X)

    prediction = model.predict(X_scaled)[0]
    probabilities = model.predict_proba(X_scaled)[0]
    confidence = float(max(probabilities))

    classes = list(model.classes_)
    prob_dict = {cls: round(float(p), 4) for cls, p in zip(classes, probabilities)}

    return {
        "prediction": prediction,
        "confidence": round(confidence, 4),
        "probabilities": prob_dict,
    }


def save_model_artifact(
    model,
    scaler,
    metrics: dict,
    feature_importance: dict,
    version: str,
    output_dir: str = "ml/artifacts",
) -> str:
    """Guarda modelo como artifact versionado.

    Returns
    -------
    str
        Ruta del artifact guardado.
    """
    import pickle

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    artifact = {
        "model": model,
        "scaler": scaler,
        "metrics": metrics,
        "feature_importance": feature_importance,
        "version": version,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    filename = output_path / f"model_{version}.pkl"
    with open(filename, "wb") as f:
        pickle.dump(artifact, f)

    meta_filename = output_path / f"model_{version}_meta.json"
    meta = {
        "version": version,
        "metrics": metrics,
        "feature_importance": feature_importance,
        "created_at": artifact["created_at"],
        "filename": str(filename),
    }
    with open(meta_filename, "w") as f:
        json.dump(meta, f, indent=2, default=str)

    return str(filename)


def _estimate_distance_to_coast(lat: float, lon: float) -> float:
    """Estimación simplificada de distancia a costa (km).

    Usa una aproximación: puntos en el borde de masa terrestre.
    """
    if lat is None or lon is None:
        return 100.0

    coast_points = [
        (36.0, -5.0), (37.0, -7.0), (38.0, -9.0),
        (39.0, -9.5), (40.0, -9.0), (41.0, -9.0),
        (42.0, -9.0), (43.0, -2.0), (44.0, -1.0),
    ]

    min_dist = float("inf")
    for clat, clon in coast_points:
        dist = ((lat - clat) ** 2 + (lon - clon) ** 2) ** 0.5 * 111
        min_dist = min(min_dist, dist)

    return min_dist
