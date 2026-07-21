import numpy as np
import pandas as pd
import pytest
from sklearn.pipeline import Pipeline

from src.preprocessing import (
    detectar_columnas_skew,
    pipeline_preprocesamiento_pca,
)


class TestDetectarSkew:
    def test_retorna_columnas_con_skew_alto(self, sample_df):
        skew_cols = detectar_columnas_skew(sample_df, umbral=0.75)
        assert isinstance(skew_cols, list)
        assert len(skew_cols) > 0

    def test_excluye_columnas_constantes(self):
        df = pd.DataFrame({"a": [1, 1, 1], "b": [1, 2, 3]})
        cols = detectar_columnas_skew(df, umbral=0.1)
        assert "a" not in cols

    def test_devuelve_vacia_sin_numericas(self):
        df = pd.DataFrame({"x": ["a", "b", "c"]})
        assert detectar_columnas_skew(df) == []


class TestPipeline:
    def test_pipeline_end_to_end(self, sample_df):
        df_pca, pipeline, df_scaled = pipeline_preprocesamiento_pca(
            sample_df, target_variance=0.85, save_path=None
        )
        assert df_pca.shape[0] == sample_df.shape[0]
        assert df_pca.shape[1] >= 1
        assert "PC1" in df_pca.columns
        assert isinstance(pipeline, Pipeline)
        assert "pca" in pipeline.named_steps
        assert "scaler" in pipeline.named_steps

    def test_varianza_retenida(self, sample_df):
        _, pipeline, _ = pipeline_preprocesamiento_pca(
            sample_df, target_variance=0.85, save_path=None
        )
        pca = pipeline.named_steps["pca"]
        cum_var = np.cumsum(pca.explained_variance_ratio_)
        assert cum_var[-1] >= 0.80

    def test_columnas_excluidas_no_entran_al_pca(self, sample_df):
        df_con_coords = sample_df.copy()
        _, _, df_scaled = pipeline_preprocesamiento_pca(
            df_con_coords, save_path=None
        )
        coord_cols = {"lat", "lon"}
        assert not coord_cols.intersection(set(df_scaled.columns))

    def test_output_shapes(self, small_df):
        df_pca, _, df_scaled = pipeline_preprocesamiento_pca(
            small_df, save_path=None
        )
        assert df_scaled.shape[1] >= 2
        assert df_pca.shape[0] == small_df.shape[0]

    def test_raise_error_sin_features_numericas(self):
        with pytest.raises(ValueError):
            pipeline_preprocesamiento_pca(
                pd.DataFrame({"a": ["x", "y", "z"]}), save_path=None
            )

    def test_pipeline_object_se_puede_reesar(self, sample_df):
        _, pipeline, _ = pipeline_preprocesamiento_pca(
            sample_df, target_variance=0.90, save_path=None
        )
        result = pipeline.transform(sample_df.head(5))
        assert result.shape[0] == 5
        assert result.shape[1] >= 1

    def test_pipeline_serializa_con_joblib(self, sample_df, tmp_path):
        import joblib

        path = tmp_path / "test_pipeline.pkl"
        _, pipeline, _ = pipeline_preprocesamiento_pca(
            sample_df, save_path=str(path)
        )
        assert path.exists()
        loaded = joblib.load(str(path))
        assert isinstance(loaded, Pipeline)
        result = loaded.transform(sample_df.head(3))
        assert result.shape[0] == 3
