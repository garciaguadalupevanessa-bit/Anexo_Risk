import os
import shutil
from unittest.mock import patch

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

import src.config.mlflow_config as cfg
from src.utils.mlflow_utils import (
    log_dataframe_schema,
    log_dataset_info,
    log_figures,
    log_model,
    safe_end_run,
    setup_mlflow,
    start_pipeline_run,
)


@pytest.fixture(autouse=True)
def reset_tracking():
    safe_end_run()


@pytest.fixture
def sample_df():
    np.random.seed(42)
    n = 50
    return pd.DataFrame(
        {
            "eq_count": np.random.poisson(5, n).astype(float),
            "eq_mag_mean": np.random.exponential(2.0, n) + 3.0,
            "categoria_tormenta": np.random.choice(["TD", "TS", "C1"], n),
        }
    )


class TestTrackingEnabled:
    def test_start_pipeline_run_creates_run(self):
        with start_pipeline_run("test-run", tags={"env": "test"}) as run:
            assert run is not None
            assert run.info.run_id is not None

    def test_log_dataset_info_does_not_crash(self, sample_df):
        with start_pipeline_run("test-dataset-info"):
            log_dataset_info(sample_df, name="input")

    def test_log_dataframe_schema_does_not_crash(self, sample_df):
        with start_pipeline_run("test-schema"):
            log_dataframe_schema(sample_df)

    def test_log_model_does_not_crash(self):
        pipe = Pipeline([("scaler", StandardScaler()), ("pca", PCA(n_components=2))])
        X = np.random.randn(20, 5)
        pipe.fit(X)

        with start_pipeline_run("test-model-log"):
            log_model(pipe, "test_model")

    def test_log_figures_does_not_crash(self):
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 9])

        with start_pipeline_run("test-figures"):
            paths = log_figures([fig], ["test_plot"], save_dir="outputs/test_figures")
            assert len(paths) == 1
            assert os.path.exists(paths[0])
            os.remove(paths[0])
            os.rmdir("outputs/test_figures")
        plt.close(fig)


class TestTrackingDisabled:
    @pytest.fixture(autouse=True)
    def disable_tracking(self):
        with patch("src.utils.mlflow_utils.ENABLE_TRACKING", False):
            yield

    def test_start_pipeline_run_returns_none(self):
        with start_pipeline_run("test-disabled") as run:
            assert run is None

    def test_log_dataset_info_does_not_crash_when_disabled(self, sample_df):
        with start_pipeline_run("test-disabled"):
            log_dataset_info(sample_df)

    def test_log_dataframe_schema_does_not_crash_when_disabled(self, sample_df):
        with start_pipeline_run("test-disabled"):
            log_dataframe_schema(sample_df)

    def test_log_model_does_not_crash_when_disabled(self):
        pca = PCA(n_components=2)
        pca.fit(np.random.randn(10, 3))

        with start_pipeline_run("test-disabled"):
            log_model(pca)

    def test_log_figures_returns_empty_when_disabled(self):
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 9])

        with start_pipeline_run("test-disabled"):
            paths = log_figures([fig], ["test_plot"])
            assert paths == []
        plt.close(fig)

    def test_log_figures_does_not_create_files_when_disabled(self):
        test_dir = "outputs/test_should_not_exist"
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)

        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 9])

        with start_pipeline_run("test-disabled"):
            paths = log_figures([fig], ["test_plot"], save_dir=test_dir)
            assert paths == []
            assert not os.path.exists(test_dir)
        plt.close(fig)


class TestConfig:
    def test_mlflow_config_has_required_fields(self):
        assert cfg.MLFLOW_EXPERIMENT == "georisk_preprocessing"
        assert cfg.MLFLOW_TRACKING_URI == "sqlite:///mlflow.db"
        assert isinstance(cfg.ENABLE_TRACKING, bool)
        assert isinstance(cfg.REGISTER_MODELS, bool)
        assert isinstance(cfg.RUN_NAME_TEMPLATE, str)
        assert isinstance(cfg.DEFAULT_TAGS, dict)

    def test_default_tags_include_project(self):
        assert cfg.DEFAULT_TAGS["project"] == "georisk_finder"

    def test_tracking_can_be_toggled(self):
        assert cfg.ENABLE_TRACKING in (True, False)


class TestUtils:
    def test_setup_mlflow_does_not_crash(self):
        setup_mlflow()

    def test_safe_end_run_does_not_crash_when_no_run_active(self):
        safe_end_run()

    def test_start_pipeline_run_nested_works(self):
        with start_pipeline_run("parent", tags={"level": "parent"}) as parent:
            assert parent is not None
            with start_pipeline_run("child", nested=True) as child:
                assert child is not None
