import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from src.features.grid import assign_events_to_cells


def compute_seismic_features(
    events_df,
    resolution=3,
    major_mag_threshold=6.0,
    window_start='1900-01-01',
    window_end='2025-12-31',
):
    """A partir de sismos individuales (lat, lon, magnitude, depth_km, timestamp),
    devuelve una fila por celda con las variables de riesgo sísmico agregadas.
    """
    df = events_df.copy()

    # Persona 1 exporta 'timestamp' con tz UTC (pd.to_datetime(..., utc=True)).
    # Normalizamos a naive-UTC para poder comparar con window_start/window_end
    # (strings sin tz) sin que pandas lance TypeError por mezclar tz-aware/naive.
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True).dt.tz_convert(None)

    df = df[(df['timestamp'] >= window_start) & (df['timestamp'] <= window_end)]

    df = assign_events_to_cells(df, resolution=resolution)
    now = df['timestamp'].max()

    def agg(group):
        major = group[group['magnitude'] >= major_mag_threshold]
        days_since_major = (
            (now - major['timestamp'].max()).days if not major.empty else np.nan
        )
        # Energía sísmica (relación de Gutenberg-Richter): log10(E) = 1.5*M + 4.8
        energy = 10 ** (1.5 * group['magnitude'] + 4.8)
        return pd.Series({
            'eq_count': len(group),
            'eq_mag_mean': group['magnitude'].mean(),
            'eq_mag_max': group['magnitude'].max(),
            'eq_depth_mean': group['depth_km'].mean(),
            'eq_energy_log': np.log10(energy.sum()),
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

    Ventana por defecto: 1970-2025 (más corta que la de sismos), porque la
    cobertura satelital que da consistencia global a IBTrACS no empieza hasta
    los años 60-70.

    cyclone_count y eq_count se escalan de forma independiente antes del
    PCA/clustering, así que la diferencia de ventana entre ambas no distorsiona
    la comparación entre celdas.
    """
    df = events_df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True).dt.tz_convert(None)
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
    y cuántos volcanes caen dentro de esa celda
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
    result['volcano_count'] = 0  # placeholder - afinar con radio real de la celda H3 si se necesita más precisión
    return result