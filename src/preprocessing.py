"""
Pipeline modular de preprocesamiento y reducción de dimensionalidad.

Funciones:
    - pipeline_preprocesamiento_pca()
    - detectar_columnas_skew()
    - transformar_log1p()
    - codificar_categoricas()
"""

import warnings

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from .config import PREPROCESSING_CONFIG


def detectar_columnas_skew(
    df: pd.DataFrame, umbral: float = 0.75
) -> list:
    """Identifica columnas numéricas con asimetría significativa.

    Parameters
    ----------
    df : pd.DataFrame
        Datos numéricos.
    umbral : float, optional
        Valor absoluto de skewness a partir del cual se aplica log1p,
        por defecto 0.75.

    Returns
    -------
    list
        Nombres de columnas con |skew| > umbral.
    """
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.empty:
        return []
    skewness = numeric_df.skew().abs()
    return skewness[skewness > umbral].index.tolist()


def transformar_log1p(
    df: pd.DataFrame, columnas: list | None = None
) -> pd.DataFrame:
    """Aplica np.log1p a columnas especificadas (o detecta automáticas).

    Sobre columnas con skewness alto. La transformación log(1+x)
    preserva ceros reales y reduce el impacto de outliers extremos
    (terremotos, superciclones) sin eliminarlos.
    """
    df = df.copy()
    cols = columnas or detectar_columnas_skew(df)
    for col in cols:
        if col in df.columns and df[col].dtype in [np.float64, np.int64]:
            df[f"{col}_log"] = np.log1p(df[col].clip(lower=0))
    return df


def codificar_categoricas(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica One-Hot Encoding a columnas categóricas.

    Usa pd.get_dummies(drop_first=True) para evitar multicolinealidad.
    """
    df = df.copy()
    dummy_cols = [
        col
        for col in PREPROCESSING_CONFIG["columnas_dummy"]
        if col in df.columns
    ]
    if not dummy_cols:
        return df
    dummies = pd.get_dummies(df[dummy_cols], drop_first=True)
    df = pd.concat([df.drop(columns=dummy_cols), dummies], axis=1)
    return df


def pipeline_preprocesamiento_pca(
    df_raw: pd.DataFrame,
    target_variance: float = 0.85,
    columnas_features: list | None = None,
) -> tuple:
    """Pipeline completo: transformación logarítmica → One-Hot → Escalado → PCA.

    Parameters
    ----------
    df_raw : pd.DataFrame
        DataFrame de entrada con las columnas físicas de riesgo geológico.
    target_variance : float, optional
        Fracción de varianza a retener en PCA, por defecto 0.85.
    columnas_features : list or None, optional
        Lista explícita de columnas a usar como features.
        Si es None, se usan todas las numéricas excluyendo 'exclude_cols'.

    Returns
    -------
    tuple
        (df_pca, pca_model, scaler_model, df_scaled, df_preprocesado)

        - df_pca: DataFrame con las componentes principales
        - pca_model: objeto PCA entrenado
        - scaler_model: objeto StandardScaler entrenado
        - df_scaled: matriz escalada como DataFrame
        - df_preprocesado: DataFrame transformado pre-PCA
    """
    df = df_raw.copy()

    # 1. Log-transform
    skew_cols = detectar_columnas_skew(df)
    df = transformar_log1p(df, skew_cols)

    # 2. Codificación categórica
    df = codificar_categoricas(df)

    # 3. Seleccionar columnas para escalado
    exclude = set(PREPROCESSING_CONFIG["columnas_excluir"])
    if columnas_features:
        feature_cols = [
            c for c in columnas_features if c in df.columns
        ]
    else:
        feature_cols = [
            c
            for c in df.select_dtypes(include=[np.number]).columns
            if c not in exclude
        ]

    if not feature_cols:
        raise ValueError(
            "No se encontraron columnas numéricas para escalar. "
            f"Verifica que df_raw tenga features numéricas. "
            f"Columnas disponibles: {list(df_raw.columns)}"
        )

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        X = df[feature_cols].fillna(df[feature_cols].median())

    # 4. StandardScaler
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    df_scaled = pd.DataFrame(
        X_scaled, columns=feature_cols, index=df.index
    )

    # 5. PCA
    n_components = min(X_scaled.shape[0], X_scaled.shape[1])
    pca = PCA(n_components=n_components, random_state=42)
    X_pca = pca.fit_transform(X_scaled)

    # Retener componentes hasta alcanzar target_variance
    cum_var = np.cumsum(pca.explained_variance_ratio_)
    n_keep = int(np.searchsorted(cum_var, target_variance) + 1)
    X_pca_reduced = X_pca[:, :n_keep]

    df_pca = pd.DataFrame(
        X_pca_reduced,
        columns=[f"PC{i+1}" for i in range(n_keep)],
        index=df.index,
    )

    return df_pca, pca, scaler, df_scaled, df
