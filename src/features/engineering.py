import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from src.features.grid import assign_events_to_cells


def compute_seismic_features(
    events_df,
    resolution=3,
    major_mag_threshold=6.0,
    window_start='1900-01-01',
    window_end=None,
):
    """A partir de sismos individuales (lat, lon, magnitude, depth_km, timestamp),
    devuelve una fila por celda con las variables de riesgo sísmico agregadas.

    Ventana por defecto: 1900-hoy. La cobertura global de USGS para magnitudes
    moderadas es razonablemente fiable desde 1900.
    """
    if window_end is None:
        window_end = pd.Timestamp.now(tz='UTC').tz_convert(None)

    df = events_df.copy()

    # Se exporta 'timestamp' con tz UTC (pd.to_datetime(..., utc=True)).
    # Al releer desde CSV, el texto puede variar ligeramente entre filas
    # (con/sin microsegundos), así que se usa format='mixed' para que pandas
    # infiera el formato fila a fila en vez de asumir uno único y fallar
    # (pandas >= 2.x lanza ValueError si detecta formato inconsistente sin
    # esto). Después se normaliza a naive-UTC para poder comparar con
    # window_start/window_end (strings sin tz) sin TypeError por mezclar
    # tz-aware/naive.
    df['timestamp'] = pd.to_datetime(
        df['timestamp'], utc=True, format='mixed'
    ).dt.tz_convert(None)

    df = df[(df['timestamp'] >= window_start) & (df['timestamp'] <= window_end)]

    df = assign_events_to_cells(df, resolution=resolution)
    now = df['timestamp'].max()

    def agg(group):
        major = group[group['magnitude'] >= major_mag_threshold]
        days_since_major = (
            (now - major['timestamp'].max()).days if not major.empty else np.nan
        )
        energy_sum = (10 ** (1.5 * group['magnitude'] + 4.8)).sum()
        eq_energy_log = np.log10(energy_sum) if energy_sum > 0 else np.nan
        return pd.Series({
            'eq_count': len(group),
            'eq_mag_mean': group['magnitude'].mean(),
            'eq_mag_max': group['magnitude'].max(),
            'eq_depth_mean': group['depth_km'].mean(),
            'eq_energy_log': eq_energy_log,
            'eq_days_since_last_major': days_since_major,
        })

    return df.groupby('cell_id').apply(agg, include_groups=False).reset_index()


def compute_cyclone_features(
    events_df,
    resolution=3,
    window_start='1970-01-01',
    window_end='2025-12-31',
):
    """A partir de puntos de trayectoria de ciclones, devuelve una fila por
    celda con variables agregadas.

    Columnas esperadas (según el CSV real que exporta Persona 2 tras su
    limpieza): 'lat', 'lon', 'timestamp', 'wind', 'pressure'.
    'wind'/'pressure' provienen de WMO_WIND/WMO_PRES (valor reportado por la
    agencia meteorológica oficial de cada cuenca), más fiable a nivel global
    que USA_WIND/USA_PRES.

    Ventana por defecto: 1970-2025 (más corta que la de sismos), porque la
    cobertura satelital que da consistencia global a IBTrACS no empieza hasta
    los años 60-70. El CSV de origen puede traer eventos desde 1900.
    """
    df = events_df.copy()
    df['timestamp'] = pd.to_datetime(
        df['timestamp'], utc=True, format='mixed'
    ).dt.tz_convert(None)
    df = df[(df['timestamp'] >= window_start) & (df['timestamp'] <= window_end)]

    df = assign_events_to_cells(df, resolution=resolution, lat_col='lat', lon_col='lon')

    def agg(group):
        return pd.Series({
            'cyclone_count': len(group),
            'wind_mean': group['wind'].mean(),
            'wind_max': group['wind'].max(),
            'pressure_min_mean': group['pressure'].mean(),
        })

    return df.groupby('cell_id').apply(agg, include_groups=False).reset_index()


def compute_volcanic_features(grid_df, volcanoes_df):
    """Para cada celda del grid, calcula distancia al volcán activo más cercano
    y cuántos volcanes caen dentro de esa celda (aprox., usando distancia < radio celda).
    """
    volc_coords = np.radians(volcanoes_df[['lat', 'lon']].values)
    grid_coords = np.radians(grid_df[['lat', 'lon']].values)

    tree = cKDTree(volc_coords)
    dist_rad, idx = tree.query(grid_coords)

    # Distancia great-circle aproximada a partir de la distancia euclídea en radianes
    R = 6371.0  # radio de la Tierra en km
    dist_km = dist_rad * R

    result = grid_df[['cell_id']].copy()
    result['dist_nearest_volcano_km'] = dist_km
    result['volcano_count'] = 0  # placeholder: afinar con radio real de la celda H3 si se necesita más precisión
    return result