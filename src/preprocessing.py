"""
Pipeline modular de preprocesamiento y reduccion de dimensionalidad.

Incluye Pipeline sklearn para exportacion con joblib.
"""

import os
import warnings

import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer, make_column_selector
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .config import PREPROCESSING_CONFIG


def detectar_columnas_skew(df: pd.DataFrame, umbral: float = 0.75) -> list:
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.empty:
        return []
    skewness = numeric_df.skew().abs()
    return skewness[skewness > umbral].index.tolist()


class SkewLogTransformer(BaseEstimator, TransformerMixin):
    """Transformador sklearn: log1p en columnas con skew alto.

    Detecta columnas con skew > umbral durante .fit()
    y aplica log1p solo a esas mismas columnas en .transform().
    """

    def __init__(self, umbral: float = 0.75):
        self.umbral = umbral
        self.skew_cols_: list = []

    def fit(self, X: pd.DataFrame, y=None):
        self.skew_cols_ = detectar_columnas_skew(X, umbral=self.umbral)
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        df = X.copy()
        for col in self.skew_cols_:
            if col in df.columns:
                df[f"{col}_log"] = np.log1p(df[col].clip(lower=0))
        return df


class OneHotTransformer(BaseEstimator, TransformerMixin):
    """Transformador sklearn: One-Hot Encoding sobre columnas dummy."""

    def __init__(self, columnas: list | None = None):
        self.columnas = columnas or PREPROCESSING_CONFIG["columnas_dummy"]
        self.dummy_cols_: list = []

    def fit(self, X: pd.DataFrame, y=None):
        self.dummy_cols_ = [c for c in self.columnas if c in X.columns]
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        df = X.copy()
        if self.dummy_cols_:
            dummies = pd.get_dummies(df[self.dummy_cols_], drop_first=True)
            df = pd.concat([df.drop(columns=self.dummy_cols_), dummies], axis=1)
        return df


def pipeline_preprocesamiento_pca(
    df_raw: pd.DataFrame,
    target_variance: float = 0.85,
    save_path: str | None = "models/pipeline_riesgo.pkl",
) -> tuple:
    """Pipeline completo: log1p -> One-Hot -> StandardScaler -> PCA.

    Construye y entrena un Pipeline sklearn, lo exporta con joblib,
    y devuelve los DataFrames transformados.

    Parameters
    ----------
    df_raw : pd.DataFrame
        DataFrame con features geologicas.
    target_variance : float, optional
        Fraccion de varianza a retener en PCA, por defecto 0.85.
    save_path : str or None, optional
        Ruta para guardar el pipeline con joblib.
        Si None, no se guarda.

    Returns
    -------
    tuple
        (df_pca, pipeline, df_scaled)
    """
    config = PREPROCESSING_CONFIG
    exclude = set(config["columnas_excluir"])
    numeric_cols = [
        c
        for c in df_raw.select_dtypes(include=[np.number]).columns
        if c not in exclude
    ]

    pipeline = Pipeline(
        [
            ("log_skew", SkewLogTransformer(umbral=0.75)),
            ("onehot", OneHotTransformer()),
            (
                "scaler",
                ColumnTransformer(
                    [
                        (
                            "scaler",
                            StandardScaler(),
                            make_column_selector(dtype_include=np.number),
                        )
                    ],
                    remainder="passthrough",
                ),
            ),
            ("pca", PCA(random_state=42)),
        ]
    )

    X_prep = df_raw[numeric_cols].copy()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        X_prep = X_prep.fillna(X_prep.median())

    pipeline.fit(X_prep)

    pca = pipeline.named_steps["pca"]
    cum_var = np.cumsum(pca.explained_variance_ratio_)

    n_keep = int(np.searchsorted(cum_var, target_variance) + 1)

    pipeline.set_params(pca__n_components=n_keep)
    pipeline.fit(X_prep)

    X_full = pipeline.transform(X_prep)
    df_pca = pd.DataFrame(
        X_full,
        columns=[f"PC{i+1}" for i in range(n_keep)],
        index=df_raw.index,
    )

    X_after_log = pipeline.named_steps["log_skew"].transform(X_prep)
    X_after_dummies = pipeline.named_steps["onehot"].transform(X_after_log)
    X_scaled = pipeline.named_steps["scaler"].transform(X_after_dummies)

    df_scaled = pd.DataFrame(
        X_scaled,
        columns=[f"V{i}" for i in range(X_scaled.shape[1])],
        index=df_raw.index,
    )

    if save_path:
        os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
        joblib.dump(pipeline, save_path, compress=3)

    return df_pca, pipeline, df_scaled


def cargar_pipeline(path: str) -> Pipeline:
    return joblib.load(path)


def transformar_nuevos_datos(
    pipeline: Pipeline, df_nuevos: pd.DataFrame
) -> np.ndarray:
    config = PREPROCESSING_CONFIG
    exclude = set(config["columnas_excluir"])
    numeric_cols = [
        c
        for c in df_nuevos.select_dtypes(include=[np.number]).columns
        if c not in exclude
    ]
    X = df_nuevos[numeric_cols].copy()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        X = X.fillna(X.median())
    return pipeline.transform(X)
