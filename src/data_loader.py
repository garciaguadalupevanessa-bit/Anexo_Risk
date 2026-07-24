import os
import warnings
import h3
import numpy as np
import pandas as pd

from src.config import PREPROCESSING_CONFIG
from src.features.grid import build_global_grid
from src.features.engineering import (
    compute_seismic_features,
    compute_cyclone_features,
    compute_volcanic_features,
)

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
    cell_ids = [h3.latlng_to_cell(la, lo, 4) for la, lo in zip(lat, lon)]
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
    res = config["h3_resolution"]
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    ciclones = _safe_read_csv(
        os.path.join(base_dir, "data/processed/ciclones_clean.csv"),
        low_memory=False,
    )
    volcanes = _safe_read_csv(
        os.path.join(base_dir, "data/processed/volcanes_clean.csv"),
    )
    espana = _safe_read_csv(
        os.path.join(base_dir, "data/processed/espana_clean.csv"),
    )

    if any(df.empty for df in [ciclones, volcanes, espana]):
        return _generate_synthetic_fallback()

    _normalise_ign_coords(espana)

    seismic = compute_seismic_features(espana, resolution=res)
    cyclone = compute_cyclone_features(ciclones, resolution=res)

    union_cells = pd.concat(
        [seismic[["cell_id"]], cyclone[["cell_id"]]]
    ).drop_duplicates().reset_index(drop=True)
    union_cells[["lat", "lon"]] = union_cells["cell_id"].apply(
        lambda c: pd.Series(h3.cell_to_latlng(c))
    )

    volcanic = compute_volcanic_features(union_cells, volcanes)

    result = union_cells.merge(seismic, on="cell_id", how="left")
    result = result.merge(cyclone, on="cell_id", how="left")
    result = result.merge(volcanic, on="cell_id", how="left")

    result["categoria_tormenta"] = result["wind_mean"].apply(_classify_storm_category)

    result.fillna(
        {
            "eq_count": 0,
            "eq_mag_mean": 0,
            "eq_mag_max": 0,
            "eq_depth_mean": 0,
            "eq_energy_log": 0,
            "eq_days_since_last_major": -1,
            "cyclone_count": 0,
            "wind_mean": 0,
            "wind_max": 0,
            "pressure_min_mean": 1013,
            "dist_nearest_volcano_km": 0,
            "volcano_count": 0,
        },
        inplace=True,
    )

    return result
