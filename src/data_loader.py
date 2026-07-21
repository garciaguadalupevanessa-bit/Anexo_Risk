"""
Combined data loader for real geological risk data.

Reads cleaned CSVs exported by Person 2 (EDA), maps column names
to the pipeline schema, and spatially aggregates cyclones, volcanoes,
and Spain seismic events via H3 hexagonal binning.

Joel (Person 3): replace the CSV-based loaders below with your final
H3 grid implementation. Keep the same return schema (see config.py
for expected column names and types).
"""

import os

import numpy as np
import pandas as pd

from .config import PREPROCESSING_CONFIG
from .h3_aggregator import merge_h3_datasets


def _safe_read_csv(path: str, **kwargs) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame()
    return pd.read_csv(path, **kwargs)


def _coerce_numeric(df: pd.DataFrame, exclude: set = None) -> pd.DataFrame:
    exclude = exclude or set()
    for col in df.select_dtypes(include=["object"]).columns:
        if col not in exclude:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def load_ciclones(path: str, mapping: dict) -> pd.DataFrame:
    df = _safe_read_csv(path, low_memory=False)
    if df.empty:
        return df
    rename = {v: k for k, v in mapping.items() if v in df.columns}
    rename["LAT"] = "lat"
    rename["LON"] = "lon"
    df = df.rename(columns=rename)
    keep = {"lat", "lon", "viento_max_ciclones", "presion_min_ciclones"}
    valid = list(keep.intersection(df.columns))
    df = df[valid].dropna(subset=["lat", "lon"])
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df = _coerce_numeric(df)
    return df.dropna(subset=["lat", "lon"])


def load_volcanes(path: str, mapping: dict) -> pd.DataFrame:
    df = _safe_read_csv(path)
    if df.empty:
        return df
    rename = {}
    for pipe_col, src_col in mapping.items():
        if src_col in df.columns:
            rename[src_col] = pipe_col
    rename["latitude"] = "lat"
    rename["longitude"] = "lon"
    rename["volcanoName"] = "volcano_name"
    df = df.rename(columns=rename)
    keep = {"lat", "lon", "elevacion_volcan", "tipo_volcan", "volcano_name"}
    valid = list(keep.intersection(df.columns))
    df = df[valid].dropna(subset=["lat", "lon"])
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    return df.dropna(subset=["lat", "lon"])


def load_espana(path: str, mapping: dict) -> pd.DataFrame:
    df = _safe_read_csv(path)
    if df.empty:
        return df
    df = df.rename(
        columns={
            "magnitude": "magnitud_max_sismo",
            "depth_km": "profundidad_media_sismo",
            "latitude": "lat",
            "longitude": "lon",
        }
    )
    keep = {"lat", "lon", "magnitud_max_sismo", "profundidad_media_sismo"}
    valid = list(keep.intersection(df.columns))
    df = df[valid].dropna(subset=["lat", "lon", "magnitud_max_sismo"])
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    return df.dropna(subset=["lat", "lon"])


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


def load_combined_data() -> pd.DataFrame:
    config = PREPROCESSING_CONFIG
    mapping = config["column_mapping"]
    res = config["h3_resolution"]
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sources = config["data_sources"]

    ciclones = load_ciclones(os.path.join(base_dir, sources["ciclones"]), mapping)
    volcanes = load_volcanes(os.path.join(base_dir, sources["volcanes"]), mapping)
    espana = load_espana(os.path.join(base_dir, sources["espana"]), mapping)

    datasets = [
        ("cic_", ciclones, {"viento_max_ciclones": "max", "presion_min_ciclones": "min"}),
        ("esp_", espana, {"magnitud_max_sismo": "max", "profundidad_media_sismo": "mean"}),
        ("vol_", volcanes, {"elevacion_volcan": "max"}),
    ]

    merged = merge_h3_datasets(datasets, res)

    if merged is None or merged.empty:
        return _generate_synthetic_fallback()

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
        if drop_col in merged.columns:
            merged = merged.drop(columns=[drop_col])

    merged = merged.drop(columns=["_h3_key"], errors="ignore")

    merged["frecuencia_eventos_sismicos"] = (
        merged.get("esp_magnitud_max_sismo", pd.Series(dtype=float)).notna().astype(int)
    )

    wind_col = merged.get("cic_viento_max_ciclones", pd.Series(dtype=float))
    merged["categoria_tormenta"] = wind_col.apply(_classify_storm_category)

    strip_prefix = {
        "cic_viento_max_ciclones": "viento_max_ciclones",
        "cic_presion_min_ciclones": "presion_min_ciclones",
        "esp_magnitud_max_sismo": "magnitud_max_sismo",
        "esp_profundidad_media_sismo": "profundidad_media_sismo",
        "vol_elevacion_volcan": "elevacion_volcan",
        "vol_tipo_volcan": "tipo_volcan",
        "vol_volcano_name": "volcano_name",
    }
    merged = merged.rename(columns=strip_prefix)

    if merged.empty:
        return _generate_synthetic_fallback()

    merged = merged.fillna({
        "viento_max_ciclones": 0,
        "presion_min_ciclones": 1013,
        "magnitud_max_sismo": 0,
        "profundidad_media_sismo": 0,
        "elevacion_volcan": 0,
    })

    return merged


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
