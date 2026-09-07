"""Pipeline ML para Anexo Risk — Construcción de dataset histórico y modelos.

Pipeline:
raw → clean → normalize → features → dataset → train/test → model → evaluation → artifact

Target: Clasificación de prioridad operacional (crítico/alto/medio/bajo).

IMPORTANTE: El target actual está generado por reglas deterministas (risk engine).
El modelo aprende las reglas, NO predice resultados reales.
Esto debe documentarse en toda presentación del modelo.
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
    from sklearn.metrics import (
        accuracy_score,
        classification_report,
        confusion_matrix,
        f1_score,
    )
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    from sklearn.dummy import DummyClassifier
    from sklearn.impute import SimpleImputer
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


FEATURE_COLUMNS = [
    "depth",
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
            "depth": event.get("depth", 0),
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

    Target: prioridad operacional basada EXCLUSIVAMENTE en severidad del evento.
    Esto evita data leakage: las features no contienen severidad.

    IMPORTANTE: El target es rule-based, no observado.
    """
    targets = []
    for event in events:
        severity = event.get("severity", 0)

        if severity >= 0.8:
            targets.append("critico")
        elif severity >= 0.6:
            targets.append("alto")
        elif severity >= 0.4:
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

    # Handle NaN values with imputer
    imputer = SimpleImputer(strategy="median")
    X = imputer.fit_transform(X)

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
    cm = confusion_matrix(y_test, y_pred, labels=model.classes_).tolist()

    report = classification_report(y_test, y_pred, output_dict=True)

    # Baseline: majority class
    dummy = DummyClassifier(strategy="most_frequent", random_state=random_state)
    dummy.fit(X_train_scaled, y_train)
    y_dummy = dummy.predict(X_test_scaled)
    baseline_accuracy = accuracy_score(y_test, y_dummy)
    baseline_f1 = f1_score(y_test, y_dummy, average="weighted", zero_division=0)

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
            "confusion_matrix": cm,
            "confusion_matrix_labels": list(model.classes_),
            "classification_report": report,
            "baseline_majority_class": {
                "accuracy": round(baseline_accuracy, 4),
                "f1_weighted": round(baseline_f1, 4),
            },
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

    Usa puntos de referencia en costas principales (global, no solo España).
    """
    if lat is None or lon is None:
        return 100.0

    coast_points = [
        # Europa
        (36.0, -5.0), (37.0, -7.0), (38.0, -9.0),
        (39.0, -9.5), (40.0, -9.0), (41.0, -9.0),
        (42.0, -9.0), (43.0, -2.0), (44.0, -1.0),
        # Mediterráneo
        (38.0, 0.0), (39.0, 3.0), (40.0, 4.0),
        # Atlántico
        (28.0, -16.0), (29.0, -13.0),
        # América (referencia básica)
        (25.0, -80.0), (40.0, -74.0), (34.0, -118.0),
        # Asia (referencia básica)
        (35.0, 139.0), (22.0, 114.0), (1.0, 103.0),
    ]

    min_dist = float("inf")
    for clat, clon in coast_points:
        dist = ((lat - clat) ** 2 + (lon - clon) ** 2) ** 0.5 * 111
        min_dist = min(min_dist, dist)

    return min_dist


def generate_evaluation_report(
    metrics: dict,
    feature_importance: dict,
    metadata: dict,
    output_path: str = "docs/ml-evaluation.md",
) -> str:
    """Genera document Markdown con la evaluación completa del modelo.

    Returns
    -------
    str
        Ruta del archivo generado.
    """
    lines = []
    lines.append("# Evaluación ML — Anexo Risk 2.x")
    lines.append("")
    lines.append(f"**Fecha:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append(f"**Muestras:** {metadata.get('n_samples', 'N/A')}")
    lines.append(f"**Features:** {metadata.get('n_features', 'N/A')}")
    lines.append("")

    lines.append("## Advertencia importante")
    lines.append("")
    lines.append("> El target actual está generado por reglas deterministas (solo severidad).")
    lines.append("> Las métricas reflejan la capacidad del modelo de aprender esas reglas,")
    lines.append("> NO de predecir resultados reales de emergencias.")
    lines.append("> Se requieren datos observados para una validación genuina.")
    lines.append("")

    lines.append("## Métricas")
    lines.append("")
    lines.append(f"| Métrica | Valor |")
    lines.append(f"|---------|-------|")
    lines.append(f"| Accuracy | {metrics.get('accuracy', 'N/A')} |")
    lines.append(f"| F1 Weighted | {metrics.get('f1_weighted', 'N/A')} |")
    lines.append("")

    baseline = metrics.get("baseline_majority_class", {})
    if baseline:
        lines.append("## Baseline (Majority Class)")
        lines.append("")
        lines.append(f"| Métrica | Valor |")
        lines.append(f"|---------|-------|")
        lines.append(f"| Accuracy | {baseline.get('accuracy', 'N/A')} |")
        lines.append(f"| F1 Weighted | {baseline.get('f1_weighted', 'N/A')} |")
        lines.append("")

    cm = metrics.get("confusion_matrix", [])
    labels = metrics.get("confusion_matrix_labels", [])
    if cm and labels:
        lines.append("## Confusion Matrix")
        lines.append("")
        header = "| | " + " | ".join(labels) + " |"
        sep = "|---" * (len(labels) + 1) + "|"
        lines.append(header)
        lines.append(sep)
        for i, row in enumerate(cm):
            row_str = f"| {labels[i]} | " + " | ".join(str(v) for v in row) + " |"
            lines.append(row_str)
        lines.append("")

    lines.append("## Feature Importance")
    lines.append("")
    lines.append("> La importancia NO implica causalidad.")
    lines.append("")
    if feature_importance:
        lines.append("| Feature | Importancia |")
        lines.append("|---------|-------------|")
        for feat, imp in feature_importance.items():
            lines.append(f"| {feat} | {imp:.4f} |")
    lines.append("")

    lines.append("## Limitaciones")
    lines.append("")
    lines.append("- Target rule-based, no observado")
    lines.append("- _estimate_distance_to_coast() es una aproximación global simplificada")
    lines.append("- Sin separación temporal/espacial en train/test")
    lines.append("- Sin evaluación con datos reales de emergencias")
    lines.append("")
    lines.append("## Próximos pasos")
    lines.append("")
    lines.append("1. Recopilar datos observados de incidentes reales")
    lines.append("2. Crear target basado en tiempo de respuesta, escalada, impacto")
    lines.append("3. Re-entrenar con target observado")
    lines.append("4. Comparar ambos modelos")
    lines.append("")

    content = "\n".join(lines)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        f.write(content)

    return str(output)
