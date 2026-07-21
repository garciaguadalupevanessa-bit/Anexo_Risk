"""
Tests unitarios y de integración del pipeline de preprocesamiento y PCA.
"""

import numpy as np
import pandas as pd
import pytest
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from src.preprocessing import (
    codificar_categoricas,
    detectar_columnas_skew,
    pipeline_preprocesamiento_pca,
    transformar_log1p,
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


class TestLog1p:
    def test_reduce_skewness(self, sample_df):
        col = "profundidad_media_sismo"
        skew_before = sample_df[col].skew()
        transformed = transformar_log1p(
            sample_df, columnas=[col]
        )
        skew_after = transformed[f"{col}_log"].skew()
        assert abs(skew_after) < abs(skew_before)

    def test_preserva_ceros(self):
        df = pd.DataFrame({"x": [0, 1, 10, 100]})
        result = transformar_log1p(df, columnas=["x"])
        assert result["x_log"].iloc[0] == 0.0

    def test_no_modifica_original(self, sample_df):
        original = sample_df.copy()
        transformar_log1p(sample_df, columnas=["magnitud_max_sismo"])
        pd.testing.assert_frame_equal(sample_df, original)

    def test_deteccion_automatica(self, sample_df):
        result = transformar_log1p(sample_df)
        log_cols = [c for c in result.columns if c.endswith("_log")]
        assert len(log_cols) >= 1


class TestDummies:
    def test_sin_categoricas_retorna_igual(self):
        df = pd.DataFrame({"a": [1, 2, 3]})
        result = codificar_categoricas(df)
        assert result.shape == df.shape

    def test_expande_columnas(self, sample_df):
        result = codificar_categoricas(sample_df)
        original_cats = [
            "categoria_tormenta",
            "tipo_volcan",
        ]
        for col in original_cats:
            if col in sample_df.columns:
                assert col not in result.columns


class TestPipeline:
    def test_pipeline_end_to_end(self, sample_df):
        df_pca, pca, scaler, df_scaled, _ = (
            pipeline_preprocesamiento_pca(
                sample_df, target_variance=0.85
            )
        )
        assert df_pca.shape[0] == sample_df.shape[0]
        assert "PC1" in df_pca.columns
        assert isinstance(pca, PCA)
        assert isinstance(scaler, StandardScaler)

    def test_varianza_retenida(self, sample_df):
        _, pca, _, _, _ = pipeline_preprocesamiento_pca(
            sample_df, target_variance=0.85
        )
        cum_var = np.cumsum(pca.explained_variance_ratio_)
        assert cum_var[-1] >= 0.80

    def test_columnas_excluidas_no_entran_al_pca(self, sample_df):
        df_con_coords = sample_df.copy()
        df_pca, _, _, df_scaled, _ = (
            pipeline_preprocesamiento_pca(df_con_coords)
        )
        coord_cols = {"lat", "lon"}
        assert not coord_cols.intersection(
            set(df_scaled.columns)
        )

    def test_output_shapes(self, small_df):
        df_pca, _, _, df_scaled, _ = (
            pipeline_preprocesamiento_pca(small_df)
        )
        assert df_scaled.shape[1] >= 2
        assert df_pca.shape[0] == small_df.shape[0]

    def test_raise_error_sin_features_numericas(self):
        with pytest.raises(ValueError):
            pipeline_preprocesamiento_pca(
                pd.DataFrame({"a": ["x", "y", "z"]})
            )

    def test_pipeline_con_mapping_personalizado(self, sample_df):
        features = [
            "magnitud_max_sismo",
            "profundidad_media_sismo",
            "viento_max_ciclones",
        ]
        df_pca, _, _, df_scaled, _ = (
            pipeline_preprocesamiento_pca(
                sample_df,
                target_variance=0.90,
                columnas_features=features,
            )
        )
        assert set(df_scaled.columns) == set(features)
