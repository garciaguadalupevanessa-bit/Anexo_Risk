"""
Carga de datos combinados (placeholder sintético).

Reemplazar con la implementación real de Persona 3 cuando
los datasets (USGS, IBTrACS, Volcanoes) estén integrados.
"""

import numpy as np
import pandas as pd


def cargar_datos_combinados() -> pd.DataFrame:
    """Retorna un DataFrame sintético con features geológicas.

    Cuando Persona 3 entregue el módulo de integración,
    reemplazar el cuerpo de esta función por la carga real
    desde H3 + USGS + IBTrACS + Volcanoes.
    """
    np.random.seed(42)
    n = 500

    return pd.DataFrame(
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
