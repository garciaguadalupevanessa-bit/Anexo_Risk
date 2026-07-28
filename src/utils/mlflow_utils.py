import contextlib
import importlib.metadata
import os
import platform
import subprocess
from datetime import datetime, timezone
from typing import Any

import matplotlib.figure
import mlflow
import pandas as pd

from src.config.mlflow_config import (
    ARTIFACT_PATH,
    DEFAULT_TAGS,
    ENABLE_TRACKING,
    FIGURES_DIR,
    MLFLOW_EXPERIMENT,
    MLFLOW_TRACKING_URI,
    REGISTER_MODELS,
)

_RUN_STACK: list[mlflow.ActiveRun] = []


def setup_mlflow() -> None:
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(MLFLOW_EXPERIMENT)


def _get_git_info() -> dict[str, str]:
    info = {}
    try:
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        if branch.returncode == 0:
            info["git_branch"] = branch.stdout.strip()
    except Exception:
        info["git_branch"] = "unknown"

    try:
        commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        if commit.returncode == 0:
            info["git_commit"] = commit.stdout.strip()
    except Exception:
        info["git_commit"] = "unknown"

    try:
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, timeout=5,
        )
        info["git_dirty"] = "true" if status.stdout.strip() else "false"
    except Exception:
        info["git_dirty"] = "unknown"

    return info


def _get_env_info() -> dict[str, Any]:
    return {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "user": os.environ.get("USER", os.environ.get("USERNAME", "unknown")),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _get_package_versions() -> dict[str, str]:
    packages = ["scikit-learn", "numpy", "pandas", "mlflow", "joblib", "scipy"]
    versions = {}
    for pkg in packages:
        try:
            versions[pkg.replace("-", "_") + "_version"] = importlib.metadata.version(pkg)
        except importlib.metadata.PackageNotFoundError:
            versions[pkg.replace("-", "_") + "_version"] = "unknown"
    return versions


@contextlib.contextmanager
def start_pipeline_run(
    run_name: str,
    tags: dict[str, str] | None = None,
    nested: bool = False,
):
    if not ENABLE_TRACKING:
        yield None
        return

    setup_mlflow()

    merged_tags = dict(DEFAULT_TAGS)
    if tags:
        merged_tags.update(tags)
    merged_tags.update(_get_git_info())

    with mlflow.start_run(run_name=run_name, nested=nested, tags=merged_tags) as run:
        _RUN_STACK.append(run)

        env_info = _get_env_info()
        mlflow.log_params(
            {
                "run_timestamp": env_info["timestamp"],
                "python_version": env_info["python_version"],
                "platform": env_info["platform"],
                "user": env_info["user"],
            }
        )
        mlflow.log_params(_get_package_versions())

        try:
            yield run
        finally:
            _RUN_STACK.pop()
            mlflow.end_run()


def log_dataset_info(df: pd.DataFrame, name: str = "dataset") -> None:
    if not ENABLE_TRACKING:
        return
    mlflow.log_params(
        {
            f"{name}_n_samples": df.shape[0],
            f"{name}_n_features": df.shape[1],
            f"{name}_columns": list(df.columns),
        }
    )
    mlflow.log_metrics(
        {
            f"{name}_missing_total": int(df.isna().sum().sum()),
            f"{name}_missing_ratio": round(float(df.isna().sum().sum() / df.size), 4),
        }
    )


def log_model(model: Any, name: str = ARTIFACT_PATH) -> None:
    if not ENABLE_TRACKING or not REGISTER_MODELS:
        return
    try:
        import mlflow.sklearn

        mlflow.sklearn.log_model(
            model,
            name,
            skops_trusted_types=[
                "numpy.number",
                "sklearn.compose._column_transformer.make_column_selector",
                "sklearn.pipeline.Pipeline",
                "sklearn.decomposition._pca.PCA",
                "sklearn.preprocessing._data.StandardScaler",
                "sklearn.compose._column_transformer.ColumnTransformer",
            ],
        )
    except Exception:
        import joblib

        tmp_path = f"/tmp/{name}.joblib"
        os.makedirs(os.path.dirname(tmp_path) or ".", exist_ok=True)
        joblib.dump(model, tmp_path)
        mlflow.log_artifact(tmp_path)


def log_figures(
    figures: list[matplotlib.figure.Figure],
    names: list[str] | None = None,
    save_dir: str = FIGURES_DIR,
) -> list[str]:
    if not ENABLE_TRACKING:
        return []
    os.makedirs(save_dir, exist_ok=True)
    paths = []
    for i, fig in enumerate(figures):
        name = names[i] if names and i < len(names) else f"figure_{i:02d}"
        path = os.path.join(save_dir, f"{name}.png")
        fig.savefig(path, dpi=150, bbox_inches="tight")
        mlflow.log_artifact(path)
        paths.append(path)
    return paths


def log_dataframe_schema(df: pd.DataFrame, name: str = "dataframe") -> None:
    if not ENABLE_TRACKING:
        return
    schema = {col: str(df[col].dtype) for col in df.columns}
    mlflow.log_params({f"{name}_schema": str(schema)})
    mlflow.log_params(
        {
            f"{name}_dtypes": str(df.dtypes.to_dict()),
            f"{name}_memory_mb": round(df.memory_usage(deep=True).sum() / 1e6, 2),
        }
    )


def safe_end_run():
    if _RUN_STACK:
        try:
            mlflow.end_run()
        except Exception:
            pass
        _RUN_STACK.clear()
