import numpy as np
import pandas as pd
import pytest
from sklearn.pipeline import Pipeline

from src.preprocessing import (
    detect_skew_columns,
    preprocessing_pca_pipeline,
)


class TestDetectSkew:
    def test_returns_columns_with_high_skew(self, sample_df):
        skew_cols = detect_skew_columns(sample_df, threshold=0.75)
        assert isinstance(skew_cols, list)
        assert len(skew_cols) > 0

    def test_excludes_constant_columns(self):
        df = pd.DataFrame({"a": [1, 1, 1], "b": [1, 2, 3]})
        cols = detect_skew_columns(df, threshold=0.1)
        assert "a" not in cols

    def test_returns_empty_without_numeric_cols(self):
        df = pd.DataFrame({"x": ["a", "b", "c"]})
        assert detect_skew_columns(df) == []


class TestPipeline:
    def test_pipeline_end_to_end(self, sample_df):
        df_pca, pipeline, df_scaled = preprocessing_pca_pipeline(
            sample_df, target_variance=0.85, save_path=None
        )
        assert df_pca.shape[0] == sample_df.shape[0]
        assert df_pca.shape[1] >= 1
        assert "PC1" in df_pca.columns
        assert isinstance(pipeline, Pipeline)
        assert "pca" in pipeline.named_steps
        assert "scaler" in pipeline.named_steps

    def test_variance_retained(self, sample_df):
        _, pipeline, _ = preprocessing_pca_pipeline(
            sample_df, target_variance=0.85, save_path=None
        )
        pca = pipeline.named_steps["pca"]
        cum_var = np.cumsum(pca.explained_variance_ratio_)
        assert cum_var[-1] >= 0.80

    def test_excluded_columns_not_in_pca(self, sample_df):
        df_with_coords = sample_df.copy()
        _, _, df_scaled = preprocessing_pca_pipeline(
            df_with_coords, save_path=None
        )
        coord_cols = {"lat", "lon"}
        assert not coord_cols.intersection(set(df_scaled.columns))

    def test_output_shapes(self, small_df):
        df_pca, _, df_scaled = preprocessing_pca_pipeline(
            small_df, save_path=None
        )
        assert df_scaled.shape[1] >= 2
        assert df_pca.shape[0] == small_df.shape[0]

    def test_raises_error_with_no_numeric_features(self):
        with pytest.raises(ValueError):
            preprocessing_pca_pipeline(
                pd.DataFrame({"a": ["x", "y", "z"]}), save_path=None
            )

    def test_pipeline_can_be_reused(self, sample_df):
        _, pipeline, _ = preprocessing_pca_pipeline(
            sample_df, target_variance=0.90, save_path=None
        )
        result = pipeline.transform(sample_df.head(5))
        assert result.shape[0] == 5
        assert result.shape[1] >= 1

    def test_pipeline_serializes_with_joblib(self, sample_df, tmp_path):
        import joblib

        path = tmp_path / "test_pipeline.pkl"
        _, pipeline, _ = preprocessing_pca_pipeline(
            sample_df, save_path=str(path)
        )
        assert path.exists()
        loaded = joblib.load(str(path))
        assert isinstance(loaded, Pipeline)
        result = loaded.transform(sample_df.head(3))
        assert result.shape[0] == 3
