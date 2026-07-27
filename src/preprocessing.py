"""
Modular preprocessing and dimensionality reduction pipeline.

Includes an sklearn Pipeline for joblib export.
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


def detect_skew_columns(df: pd.DataFrame, threshold: float = 0.75) -> list:
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.empty:
        return []
    skewness = numeric_df.skew().abs()
    return skewness[skewness > threshold].index.tolist()


class SkewLogTransformer(BaseEstimator, TransformerMixin):
    """Applies log1p to columns with high skewness.

    Detects columns with skew > threshold during .fit()
    and applies log1p only to those columns in .transform().
    """

    def __init__(self, threshold: float = 0.75):
        self.threshold = threshold
        self.skew_cols_: list = []

    def fit(self, X: pd.DataFrame, y=None):
        self.skew_cols_ = detect_skew_columns(X, threshold=self.threshold)
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        df = X.copy()
        for col in self.skew_cols_:
            if col in df.columns:
                df[f"{col}_log"] = np.log1p(df[col].clip(lower=0))
        return df.drop(columns=[c for c in self.skew_cols_ if c in df.columns])


class OneHotTransformer(BaseEstimator, TransformerMixin):
    """Applies One-Hot Encoding on categorical columns."""

    def __init__(self, columns: list | None = None):
        self.columns = columns or PREPROCESSING_CONFIG["dummy_columns"]
        self.dummy_cols_: list = []
        self.dummy_cols_used_: list = []

    def fit(self, X: pd.DataFrame, y=None):
        self.dummy_cols_ = [c for c in self.columns if c in X.columns]
        if self.dummy_cols_:
            dummies = pd.get_dummies(X[self.dummy_cols_])
            drop_col = dummies.columns[0]
            self.dummy_cols_used_ = [c for c in dummies.columns if c != drop_col]
        else:
            self.dummy_cols_used_ = []
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        df = X.copy()
        if self.dummy_cols_:
            dummies = pd.get_dummies(df[self.dummy_cols_])
            dummies = dummies.reindex(columns=self.dummy_cols_used_, fill_value=0)
            df = pd.concat([df.drop(columns=self.dummy_cols_), dummies], axis=1)
        return df


def preprocessing_pca_pipeline(
    df_raw: pd.DataFrame,
    target_variance: float = 0.85,
    save_path: str | None = "models/pipeline_riesgo.joblib",
) -> tuple:
    """Full pipeline: log1p -> One-Hot -> StandardScaler -> PCA.

    Builds and trains an sklearn Pipeline, exports it with joblib,
    and returns the transformed DataFrames.

    Parameters
    ----------
    df_raw : pd.DataFrame
        DataFrame with geological features.
    target_variance : float, optional
        Fraction of variance to retain in PCA, default 0.85.
    save_path : str or None, optional
        Path to save the pipeline with joblib.
        If None, the pipeline is not saved.

    Returns
    -------
    tuple
        (df_pca, pipeline, df_scaled)
    """
    config = PREPROCESSING_CONFIG
    exclude = set(config["exclude_columns"])
    numeric_cols = [
        c for c in df_raw.select_dtypes(include=[np.number]).columns if c not in exclude
    ]
    dummy_cols = [c for c in config["dummy_columns"] if c in df_raw.columns]
    feature_cols = numeric_cols + dummy_cols

    pipeline = Pipeline(
        [
            ("log_skew", SkewLogTransformer(threshold=0.75)),
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

    X_prep = df_raw[feature_cols].copy()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        numeric_for_median = X_prep.select_dtypes(include=[np.number]).columns
        X_prep[numeric_for_median] = X_prep[numeric_for_median].fillna(
            X_prep[numeric_for_median].median()
        )

    pipeline.fit(X_prep)

    pca = pipeline.named_steps["pca"]
    cum_var = np.cumsum(pca.explained_variance_ratio_)

    n_keep = int(np.searchsorted(cum_var, target_variance) + 1)

    pipeline.set_params(pca__n_components=n_keep)
    pipeline.fit(X_prep)

    X_full = pipeline.transform(X_prep)
    df_pca = pd.DataFrame(
        X_full,
        columns=[f"PC{i + 1}" for i in range(n_keep)],
        index=df_raw.index,
    )

    X_after_log = pipeline.named_steps["log_skew"].transform(X_prep)
    X_after_dummies = pipeline.named_steps["onehot"].transform(X_after_log)
    X_scaled = pipeline.named_steps["scaler"].transform(X_after_dummies)

    try:
        scaled_names = pipeline.named_steps["scaler"].get_feature_names_out()
    except Exception:
        scaled_names = [f"V{i}" for i in range(X_scaled.shape[1])]

    df_scaled = pd.DataFrame(
        X_scaled,
        columns=scaled_names,
        index=df_raw.index,
    )

    if save_path:
        os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
        joblib.dump(pipeline, save_path, compress=3)

    return df_pca, pipeline, df_scaled


def load_pipeline(path: str) -> Pipeline:
    return joblib.load(path)


def transform_new_data(pipeline: Pipeline, df_new: pd.DataFrame) -> np.ndarray:
    config = PREPROCESSING_CONFIG
    exclude = set(config["exclude_columns"])
    numeric_cols = [
        c for c in df_new.select_dtypes(include=[np.number]).columns if c not in exclude
    ]
    dummy_cols = [c for c in config["dummy_columns"] if c in df_new.columns]
    feature_cols = numeric_cols + dummy_cols
    X = df_new[feature_cols].copy()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        numeric_for_median = X.select_dtypes(include=[np.number]).columns
        X[numeric_for_median] = X[numeric_for_median].fillna(
            X[numeric_for_median].median()
        )
    return pipeline.transform(X)
