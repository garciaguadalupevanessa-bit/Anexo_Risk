"""Script para ejecutar la evaluación completa del ML pipeline."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from ml.pipeline import (
    build_dataset,
    train_model,
    generate_evaluation_report,
    FEATURE_COLUMNS,
)
from geodata.adapters.usgs_adapter import fetch_earthquakes
from geodata.adapters.smithsonian_adapter import fetch_volcanoes


def main():
    print("=== Anexo Risk ML Evaluation ===\n")

    # 1. Load real data
    print("Loading USGS earthquakes...")
    try:
        earthquakes = fetch_earthquakes(feed="month")
        print(f"  Loaded {len(earthquakes)} earthquakes")
    except Exception as e:
        print(f"  Error loading USGS: {e}")
        earthquakes = []

    print("Loading Smithsonian volcanoes...")
    try:
        volcanoes = fetch_volcanoes()
        print(f"  Loaded {len(volcanoes)} volcanoes")
    except Exception as e:
        print(f"  Error loading Smithsonian: {e}")
        volcanoes = []

    all_events = earthquakes + volcanoes
    print(f"\nTotal events: {len(all_events)}")

    if len(all_events) < 10:
        print("ERROR: Not enough events to train. Need at least 10.")
        return

    # 2. Build dataset
    print("\nBuilding dataset...")
    dataset = build_dataset(all_events)
    df = dataset["df"]
    print(f"  Samples: {len(df)}")
    print(f"  Features: {dataset['feature_names']}")
    print(f"  Target distribution:")
    for cls, count in dataset["metadata"]["target_distribution"].items():
        print(f"    {cls}: {count}")

    # 3. Train model
    print("\nTraining GradientBoostingClassifier...")
    result = train_model(
        dataset["X"],
        dataset["y"],
        dataset["feature_names"],
        model_type="gradient_boosting",
    )

    print(f"  Accuracy: {result['metrics']['accuracy']}")
    print(f"  F1 Weighted: {result['metrics']['f1_weighted']}")
    baseline = result["metrics"]["baseline_majority_class"]
    print(f"  Baseline Accuracy: {baseline['accuracy']}")
    print(f"  Baseline F1: {baseline['f1_weighted']}")

    print("\nConfusion Matrix:")
    cm = result["metrics"]["confusion_matrix"]
    labels = result["metrics"]["confusion_matrix_labels"]
    print(f"  Labels: {labels}")
    for i, row in enumerate(cm):
        print(f"  {labels[i]}: {row}")

    print("\nFeature Importance:")
    for feat, imp in result["feature_importance"].items():
        print(f"  {feat}: {imp:.4f}")

    # 4. Generate evaluation report
    print("\nGenerating evaluation report...")
    report_path = generate_evaluation_report(
        metrics=result["metrics"],
        feature_importance=result["feature_importance"],
        metadata=dataset["metadata"],
        output_path="docs/ml-evaluation.md",
    )
    print(f"  Report saved to: {report_path}")

    print("\n=== Evaluation Complete ===")


if __name__ == "__main__":
    main()
