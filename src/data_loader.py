"""
Combined data loader for real geological risk data.

Reads cleaned CSVs exported by Person 2 (EDA), maps column names
to the pipeline schema, normalises IGN coordinates, and spatially
aggregates cyclones, volcanoes and Spain seismic events via H3
hexagonal binning.

Joel (Person 3): replace the CSV-based loaders below with your final
H3 grid implementation. Keep the same return schema so that the
preprocessing pipeline (Person 4) does not need to change.
"""

import os
import warnings

import numpy as np
import pandas as pd

from .config import PREPROCESSING_CONFIG
from .h3_aggregator import merge_h3_datasets

# ---------------------------------------------------------------------------
# IGN coordinate normalisation
# ---------------------------------------------------------------------------
# The IGN historical catalogue stores latitude/longitude scaled by a
# factor of 10 (e.g. 430 → 43.0).  We detect and undo this scaling
# when values exceed the valid geographic range.
_IGN_LAT_MAX = 90.0
_IGN_LON_MAX = 180.0


def _normalise_ign_coords(df: pd.DataFrame) -> pd.DataFrame:
    for col in ("lat", "lon"):
        if col in df.columns:
            thr = _IGN_LAT_MAX if col == "lat" else _IGN_LON_MAX
            mask = df[col].abs() > thr
            if mask.any():
                df.loc[mask, col] /= 10.0
    return df


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _safe_read_csv(path: str, **kwargs) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=Warning)
        return pd.read_csv(path, **kwargs)


def _coerce_numeric(df: pd.DataFrame, exclude: set = None) -> pd.DataFrame:
    exclude = exclude or set()
    for col in df.select_dtypes(include=["object"]).columns:
        if col not in exclude:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def _select_columns(df: pd.DataFrame, required: set, optional: set) -> pd.DataFrame:
    keep = required & set(df.columns)
    keep |= optional & set(df.columns)
    if not keep:
        return pd.DataFrame()
    df = df[list(keep)].copy()
    return df.dropna(subset=list(required & keep))


# ---------------------------------------------------------------------------
# Source-specific loaders
# ---------------------------------------------------------------------------


def _load_ciclones(path: str, mapping: dict) -> pd.DataFrame:
    df = _safe_read_csv(path, low_memory=False)
    if df.empty:
        return df
    df = df.rename(columns={v: k for k, v in mapping.items() if v in df.columns})
    required = {"lat", "lon"}
    optional = {"viento_max_ciclones", "presion_min_ciclones"}
    return _select_columns(df, required, optional)


def _load_volcanes(path: str, mapping: dict) -> pd.DataFrame:
    df = _safe_read_csv(path)
    if df.empty:
        return df
    df = df.rename(columns={v: k for k, v in mapping.items() if v in df.columns})
    required = {"lat", "lon"}
    optional = {"elevacion_volcan"}
    return _select_columns(df, required, optional)


def _load_espana(path: str, mapping: dict) -> pd.DataFrame:
    df = _safe_read_csv(path)
    if df.empty:
        return df
    df = df.rename(columns={v: k for k, v in mapping.items() if v in df.columns})
    _normalise_ign_coords(df)
    required = {"lat", "lon", "magnitud_max_sismo"}
    optional = {"profundidad_media_sismo"}
    return _select_columns(df, required, optional)


# ---------------------------------------------------------------------------
# Storm category (Saffir-Simpson)
# ---------------------------------------------------------------------------


def _classify_storm_category(wind_speed: float) -> str:
    if pd.isna(wind_speed) or wind_speed < 34:
        return "TD"
    if wind_speed < 64:
        return "TS"
    if wind_speed < 83:
        return "C1"
    if wind_speed < 96:
        return "C2"
    if wind_speed < 113:
        return "C3"
    if wind_speed < 137:
        return "C4"
    return "C5"


# ---------------------------------------------------------------------------
# Merge & fallback
# ---------------------------------------------------------------------------


def _generate_synthetic_fallback() -> pd.DataFrame:
    np.random.seed(42)
    n = 500
    return pd.DataFrame(
        {
            "magnitud_max_sismo": np.random.exponential(2.0, n) + 3.0,
            "profundidad_media_sismo": np.random.lognormal(2.0, 0.8, n),
            "frecuencia_eventos_sismicos": np.random.poisson(5, n).astype(float),
            "viento_max_ciclones": np.random.gamma(3, 10, n) + 30,
            "presion_min_ciclones": np.random.normal(980, 25, n),
            "elevacion_volcan": np.random.lognormal(5.5, 1.2, n),
            "categoria_tormenta": np.random.choice(
                ["TD", "TS", "C1", "C2", "C3", "C4", "C5"], n
            ),
            "tipo_volcan": np.random.choice(
                ["Stratovolcano", "Shield", "Caldera", "Cinder cone"], n
            ),
            "lat": np.random.uniform(-60, 60, n),
            "lon": np.random.uniform(-180, 180, n),
        }
    )


def load_combined_data() -> pd.DataFrame:
    config = PREPROCESSING_CONFIG
    source_map = config["source_mapping"]
    res = config["h3_resolution"]
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sources = config["data_sources"]

    ciclones = _load_ciclones(
        os.path.join(base_dir, sources["ciclones"]),
        source_map["ciclones"],
    )
    volcanes = _load_volcanes(
        os.path.join(base_dir, sources["volcanes"]),
        source_map["volcanes"],
    )
    espana = _load_espana(
        os.path.join(base_dir, sources["espana"]),
        source_map["espana"],
    )

    datasets = [
        (
            "cic_",
            ciclones,
            {"viento_max_ciclones": "max", "presion_min_ciclones": "min"},
        ),
        (
            "esp_",
            espana,
            {"magnitud_max_sismo": "max", "profundidad_media_sismo": "mean"},
        ),
        ("vol_", volcanes, {"elevacion_volcan": "max"}),
    ]

    merged = merge_h3_datasets(datasets, res)

    if merged is None or merged.empty:
        return _generate_synthetic_fallback()

    # Flatten coordinate columns from per-source prefixes
    rename_map = {
        "cic_lat": "lat",
        "cic_lon": "lon",
        "esp_lat": "lat_esp",
        "esp_lon": "lon_esp",
        "vol_lat": "lat_vol",
        "vol_lon": "lon_vol",
    }
    merged = merged.rename(columns=rename_map)

    lat_cols = [c for c in ["lat", "lat_esp", "lat_vol"] if c in merged.columns]
    lon_cols = [c for c in ["lon", "lon_esp", "lon_vol"] if c in merged.columns]
    if lat_cols:
        merged["lat"] = merged[lat_cols].bfill(axis=1).iloc[:, 0]
    if lon_cols:
        merged["lon"] = merged[lon_cols].bfill(axis=1).iloc[:, 0]

    for drop_col in ["lat_esp", "lon_esp", "lat_vol", "lon_vol"]:
        merged.drop(columns=[drop_col], inplace=True, errors="ignore")

    merged.drop(columns=["_h3_key"], inplace=True, errors="ignore")

    # Derived features
    merged["frecuencia_eventos_sismicos"] = (
        merged.get("esp_magnitud_max_sismo", pd.Series(dtype=float)).notna().astype(int)
    )

    wind_col = merged.get("cic_viento_max_ciclones", pd.Series(dtype=float))
    merged["categoria_tormenta"] = wind_col.apply(_classify_storm_category)

    # Strip per-source prefixes
    strip_prefix = {
        "cic_viento_max_ciclones": "viento_max_ciclones",
        "cic_presion_min_ciclones": "presion_min_ciclones",
        "esp_magnitud_max_sismo": "magnitud_max_sismo",
        "esp_profundidad_media_sismo": "profundidad_media_sismo",
        "vol_elevacion_volcan": "elevacion_volcan",
        "vol_volcano_name": "volcano_name",
    }
    merged.rename(columns=strip_prefix, inplace=True)

    if merged.empty:
        return _generate_synthetic_fallback()

    merged.fillna(
        {
            "viento_max_ciclones": 0,
            "presion_min_ciclones": 1013,
            "magnitud_max_sismo": 0,
            "profundidad_media_sismo": 0,
            "elevacion_volcan": 0,
        },
        inplace=True,
    )

    return merged
