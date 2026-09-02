# MLflow Tracking Guide

## Overview

MLflow Tracking logs parameters, metrics, and artifacts from the GeoRisk Finder pipeline. Every run is recorded in a local SQLite database (`mlflow.db`) and viewable through the MLflow UI.

## Quick Start

```bash
# Start the UI
mlflow ui --port 5001

# Open in browser
# http://127.0.0.1:5001
```

## Creating Experiments

Experiments group related runs. The project uses one experiment per pipeline stage:

| Experiment | Pipeline stage | Created by |
|---|---|---|
| `georisk_preprocessing` | PCA preprocessing | `src/preprocessing.py` |
| `georisk_modelado` *(future)* | K-Means / DBSCAN clustering | Notebook 05 |
| `georisk_estabilidad` *(future)* | Stability evaluation | Notebook 06 |

To create a new experiment:

```python
import mlflow
mlflow.set_experiment("georisk_modelado")
```

## How Runs Are Structured

Each run logs:

**Tags** (for filtering):
- `project`: `georisk_finder`
- `dataset`: `grid_features`
- `source`: `real` or `test` (auto-detected by row count > 5000)
- `git_branch`, `git_commit`, `git_dirty`
- `summary`: human-readable run description

**Params** (input configuration):
- `h3_resolution`, `skew_threshold`, `target_variance`
- `random_state`, `pca_solver`, `scaler`, `imputer`
- `n_samples`, `n_features_input`, `n_features_after_skew`
- `missing_values_before`
- `python_version`, `scikit_learn_version`, `numpy_version`, etc.

**Metrics** (results):
- `explained_variance`, `n_components`
- `missing_values_before`, `missing_values_after`
- `runtime_seconds`

**Artifacts** (files):
- `pipeline_riesgo` (sklearn model, MLflow format)
- `pipeline_riesgo.joblib` (joblib serialized)
- `figures/explained_variance.png`
- `figures/pca_2d.png`
- `figures/loadings_heatmap.png`
- `figures/pairplot_pca.png`

## Comparing Runs

1. Open the MLflow UI at `http://127.0.0.1:5001`
2. Select the experiment in the left sidebar
3. Check the boxes next to runs you want to compare
4. Click **Compare** (top of table)
5. View parameters, metrics, and artifacts side by side

## Downloading Artifacts

From the UI:
1. Open a run
2. Scroll to **Artifacts**
3. Click any artifact to download

From Python:
```python
import mlflow
mlflow.set_tracking_uri("sqlite:///mlflow.db")
client = mlflow.tracking.MlflowClient()
client.download_artifacts(run_id, "pipeline_riesgo", dst_path="./downloads")
```

## Registering Models

To promote a trained pipeline to the Model Registry:
```python
mlflow.register_model(f"runs:/{run_id}/pipeline_riesgo", "GeoRiskPipeline")
```
Then promote to **Staging** or **Production** via the UI under the **Models** tab.

## Disabling Tracking

Set `ENABLE_TRACKING = False` in `src/config/mlflow_config.py` to skip all MLflow logging. This is useful for tests and CI.

## Writing a Notebook with MLflow

```python
from src.utils.mlflow_utils import start_pipeline_run, log_dataset_info, log_model

with start_pipeline_run("experiment-name", tags={"source": "notebook"}):
    df = load_data()
    log_dataset_info(df)

    model = train_model(df)
    log_model(model, "my_model")
```

For multiple trials, use nested runs:

```python
with start_pipeline_run("kmeans-grid", tags={"source": "grid-search"}) as parent:
    for k in range(3, 8):
        with start_pipeline_run(f"k={k}", nested=True):
            model = KMeans(n_clusters=k).fit(X)
            mlflow.log_metric("silhouette", silhouette_score(X, model.labels_))
            mlflow.sklearn.log_model(model, f"kmeans_k{k}")
```

## Best Practices

1. **Always use `start_pipeline_run`** (context manager) instead of raw `mlflow.start_run` — it auto-logs environment info, package versions, and git state.
2. **Use nested runs** for parameter sweeps and grid searches.
3. **Tag runs with meaningful source labels** to distinguish real data from tests.
4. **Set `ENABLE_TRACKING = False`** in tests and CI to avoid polluting the experiment.
5. **Clean the DB periodically** (`mlflow.db` and `mlruns/`) to remove stale test runs.
6. **Do not version `mlflow.db`** — it's in `.gitignore`.
