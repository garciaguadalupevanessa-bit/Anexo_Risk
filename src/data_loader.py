import os
import warnings
import h3
import numpy as np
import pandas as pd

from src.config import PREPROCESSING_CONFIG

_GRID_FEATURES_PATH = "data/processed/grid_features.csv"


def _safe_read_csv(path: str, **kwargs) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=Warning)
        return pd.read_csv(path, **kwargs)


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


def _generate_synthetic_fallback() -> pd.DataFrame:
    np.random.seed(42)
    n = 500
    lat = np.random.uniform(-60, 60, n)
    lon = np.random.uniform(-180, 180, n)
    cell_ids = [h3.latlng_to_cell(la, lo, 3) for la, lo in zip(lat, lon)]
    return pd.DataFrame(
        {
            "cell_id": cell_ids,
            "lat": lat,
            "lon": lon,
            "eq_count": np.random.poisson(5, n).astype(float),
            "eq_mag_mean": np.random.exponential(2.0, n) + 3.0,
            "eq_mag_max": np.random.exponential(2.0, n) + 4.0,
            "eq_depth_mean": np.random.lognormal(2.0, 0.8, n),
            "eq_energy_log": np.random.uniform(5, 12, n),
            "eq_days_since_last_major": np.random.exponential(500, n),
            "cyclone_count": np.random.poisson(3, n).astype(float),
            "wind_mean": np.random.gamma(3, 10, n) + 30,
            "wind_max": np.random.gamma(4, 12, n) + 40,
            "pressure_min_mean": np.random.normal(980, 25, n),
            "dist_nearest_volcano_km": np.random.lognormal(4.5, 1.5, n),
            "volcano_count": np.random.poisson(0.5, n).astype(float),
            "categoria_tormenta": np.random.choice(
                ["TD", "TS", "C1", "C2", "C3", "C4", "C5"], n
            ),
        }
    )


def load_combined_data(force_synthetic: bool = False) -> pd.DataFrame:
    config = PREPROCESSING_CONFIG
    if force_synthetic:
        return _generate_synthetic_fallback()

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, _GRID_FEATURES_PATH)
    df = _safe_read_csv(path)

    if df.empty:
        return _generate_synthetic_fallback()

    # Derive storm category from wind_mean
    if "wind_mean" in df.columns:
        df["categoria_tormenta"] = df["wind_mean"].apply(_classify_storm_category)
    else:
        df["categoria_tormenta"] = "TD"

    # Fill NaN: distinguish no-event cells from event-with-missing-intensity
    _FILL_DEFAULTS = {
        "eq_count": 0,
        "eq_mag_mean": 0,
        "eq_mag_max": 0,
        "eq_depth_mean": 0,
        "eq_energy_log": 0,
        "eq_days_since_last_major": 99999,
        "cyclone_count": 0,
        "wind_mean": 0,
        "wind_max": 0,
        "pressure_min_mean": 1013,
        "dist_nearest_volcano_km": 0,
        "volcano_count": 0,
    }

    for col, default in _FILL_DEFAULTS.items():
        if col not in df.columns:
            df[col] = default
            continue

        if col in ("wind_mean", "wind_max", "pressure_min_mean") and "cyclone_count" in df.columns:
            has_cyclone = df["cyclone_count"] > 0
            global_mean = df.loc[has_cyclone & df[col].notna(), col].mean()
            if pd.notna(global_mean):
                df.loc[has_cyclone & df[col].isna(), col] = global_mean

        df[col] = df[col].fillna(default)

    return df
