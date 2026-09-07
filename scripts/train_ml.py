"""Script para entrenar y guardar el modelo ML con metadata completa."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import json
from pathlib import Path
from datetime import datetime, timezone

from ml.pipeline import (
    build_dataset,
    train_model,
    save_model_artifact,
    FEATURE_COLUMNS,
)
from geodata.adapters.usgs_adapter import fetch_earthquakes
from geodata.adapters.smithsonian_adapter import fetch_volcanoes


def main():
    print("=== Entrenamiento ML Anexo Risk ===\n")

    # 1. Load data
    print("Cargando USGS earthquakes...")
    try:
        earthquakes = fetch_earthquakes(feed="month")
        print(f"  {len(earthquakes)} terremotos cargados")
    except Exception as e:
        print(f"  Error USGS: {e}")
        earthquakes = []

    print("Cargando Smithsonian volcanoes...")
    try:
        volcanoes = fetch_volcanoes()
        print(f"  {len(volcanoes)} volcanes cargados")
    except Exception as e:
        print(f"  Error Smithsonian: {e}")
        volcanoes = []

    all_events = earthquakes + volcanoes
    print(f"\nTotal: {len(all_events)} eventos")

    if len(all_events) < 10:
        print("ERROR: datos insuficientes")
        return

    # 2. Build dataset
    print("\nConstruyendo dataset...")
    dataset = build_dataset(all_events)
    df = dataset["df"]
    print(f"  Muestras: {len(df)}")
    print(f"  Features: {dataset['feature_names']}")
    print(f"  Distribución target:")
    for cls, count in dataset["metadata"]["target_distribution"].items():
        print(f"    {cls}: {count}")

    # 3. Train
    print("\nEntrenando GradientBoostingClassifier...")
    result = train_model(
        dataset["X"],
        dataset["y"],
        dataset["feature_names"],
        model_type="gradient_boosting",
    )

    print(f"  Accuracy: {result['metrics']['accuracy']}")
    print(f"  F1 Weighted: {result['metrics']['f1_weighted']}")
    print(f"  Baseline: {result['metrics']['baseline_majority_class']['accuracy']}")

    # 4. Save artifact
    version = f"ml-v1-{datetime.now(timezone.utc).strftime('%Y%m%d')}"
    print(f"\nGuardando artifact: {version}...")

    filename = save_model_artifact(
        model=result["model"],
        scaler=result["scaler"],
        metrics=result["metrics"],
        feature_importance=result["feature_importance"],
        version=version,
        output_dir="ml/artifacts",
    )
    print(f"  Artifact: {filename}")

    # 5. Save version info
    version_info = {
        "version": version,
        "model_type": result["model_type"],
        "metrics": result["metrics"],
        "feature_importance": result["feature_importance"],
        "feature_columns": FEATURE_COLUMNS,
        "trained_at": result["trained_at"],
        "filename": filename,
        "training_samples": len(all_events),
        "target_type": "rule-based (severity only)",
        "disclaimer": (
            "El target está derivado de severidad del evento. "
            "El modelo aprende scoring rule-based, no resultados reales."
        ),
    }

    version_path = Path("ml/artifacts/current_version.json")
    version_path.parent.mkdir(parents=True, exist_ok=True)
    with open(version_path, "w", encoding="utf-8") as f:
        json.dump(version_info, f, indent=2, default=str)
    print(f"  Version file: {version_path}")

    print("\n=== Entrenamiento completado ===")
    print(f"  Modelo: {version}")
    print(f"  Accuracy: {result['metrics']['accuracy']}")
    print(f"  F1: {result['metrics']['f1_weighted']}")
    print(f"  Top features: {list(result['feature_importance'].keys())[:3]}")


if __name__ == "__main__":
    main()
