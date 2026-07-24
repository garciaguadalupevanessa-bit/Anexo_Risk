import numpy as np
import pandas as pd
import pytest


@pytest.fixture(scope="module")
def sample_df() -> pd.DataFrame:
    """Synthetic DataFrame with 200 samples of geological features."""
    np.random.seed(42)
    n = 200

    df = pd.DataFrame(
        {
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
            "lat": np.random.uniform(-60, 60, n),
            "lon": np.random.uniform(-180, 180, n),
        }
    )
    return df


@pytest.fixture
def small_h3_df() -> pd.DataFrame:
    """Minimal DataFrame with coordinates for H3 aggregation tests."""
    np.random.seed(7)
    n = 20
    return pd.DataFrame(
        {
            "viento": np.random.gamma(3, 10, n) + 30,
            "magnitud": np.random.exponential(1.5, n) + 2.0,
            "lat": np.random.uniform(-10, 10, n),
            "lon": np.random.uniform(-10, 10, n),
        }
    )


@pytest.fixture
def small_df() -> pd.DataFrame:
    """Minimal DataFrame with 30 rows for fast tests."""
    np.random.seed(99)
    n = 30
    return pd.DataFrame(
        {
            "eq_mag_max": np.random.exponential(1.5, n) + 2.5,
            "wind_max": np.random.gamma(2, 8, n) + 25,
            "categoria_tormenta": np.random.choice(["TS", "C1", "C2"], n),
            "lat": np.random.uniform(-30, 30, n),
            "lon": np.random.uniform(-120, 120, n),
        }
    )
