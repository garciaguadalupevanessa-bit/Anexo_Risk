"""
Fixtures de pruebas con datos sintéticos realistas para el pipeline.
"""

import numpy as np
import pandas as pd
import pytest


@pytest.fixture(scope="module")
def sample_df() -> pd.DataFrame:
    """DataFrame sintético con 200 muestras de 7 variables geológicas."""
    np.random.seed(42)
    n = 200

    df = pd.DataFrame(
        {
            "magnitud_max_sismo": np.random.exponential(2.0, n) + 3.0,
            "profundidad_media_sismo": np.random.lognormal(2.0, 0.8, n),
            "frecuencia_eventos_sismicos": np.random.poisson(5, n).astype(
                float
            ),
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
    return df


@pytest.fixture
def small_df() -> pd.DataFrame:
    """DataFrame mínimo de 30 filas para tests rápidos."""
    np.random.seed(99)
    n = 30
    return pd.DataFrame(
        {
            "magnitud_max_sismo": np.random.exponential(1.5, n) + 2.5,
            "viento_max_ciclones": np.random.gamma(2, 8, n) + 25,
            "categoria_tormenta": np.random.choice(
                ["TS", "C1", "C2"], n
            ),
            "lat": np.random.uniform(-30, 30, n),
            "lon": np.random.uniform(-120, 120, n),
        }
    )
