import h3
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
    devuelve una fila por celda con las variables de riesgo sismico agregadas.

    Ventana por defecto: 1900-hoy. La cobertura global de USGS para magnitudes
    moderadas es razonablemente fiable desde 1900.
    """
    if window_end is None:
        window_end = pd.Timestamp.now(tz='UTC').tz_convert(None)

    df = events_df.copy()

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

    Columnas esperadas (segun el CSV real que exporta Persona 2 tras su
    limpieza): 'lat', 'lon', 'timestamp', 'wind', 'pressure'.
    'wind'/'pressure' provienen de WMO_WIND/WMO_PRES (valor reportado por la
    agencia meteorologica oficial de cada cuenca), mas fiable a nivel global
    que USA_WIND/USA_PRES.

    Ventana por defecto: 1970-2025 (mas corta que la de sismos), porque la
    cobertura satelital que da consistencia global a IBTrACS no empieza hasta
    los anos 60-70. El CSV de origen puede traer eventos desde 1900.
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


def _latlon_to_unit_sphere_xyz(lat, lon):
    """Proyecta lat/lon (grados) a coordenadas cartesianas 3D sobre una
    esfera de radio unitario. Necesario para poder usar cKDTree (que solo
    calcula distancia euclidiana) de forma correcta sobre la superficie de
    la Tierra -- usar lat/lon en radianes directamente como si fueran
    coordenadas cartesianas (como hacia la version anterior) es incorrecto
    y da distancias muy distorsionadas cerca de los polos y en longitudes
    negativas (p.ej. Canarias).
    """
    lat_r = np.radians(lat)
    lon_r = np.radians(lon)
    x = np.cos(lat_r) * np.cos(lon_r)
    y = np.cos(lat_r) * np.sin(lon_r)
    z = np.sin(lat_r)
    return np.column_stack([x, y, z])


def compute_volcanic_features(grid_df, volcanoes_df):
    """Para cada celda del grid, calcula distancia al volcan activo mas
    cercano (en km, sobre la superficie terrestre real, no euclidiana) y
    cuantos volcanes caen dentro de cada celda H3.
    """
    if volcanoes_df.empty:
        result = grid_df[['cell_id']].copy()
        result['dist_nearest_volcano_km'] = np.nan
        result['volcano_count'] = 0
        return result

    # Normalizamos nombres de columnas por si vienen distinto
    # (p.ej. 'Latitude'/'Longitude') desde volcanes_clean.csv.
    volc_df = volcanoes_df.rename(columns=lambda c: c.strip().lower())
    if 'lat' not in volc_df.columns or 'lon' not in volc_df.columns:
        raise ValueError(
            f"volcanoes_df debe tener columnas 'lat'/'lon'. Columnas recibidas: "
            f"{list(volcanoes_df.columns)}"
        )

    volc_xyz = _latlon_to_unit_sphere_xyz(volc_df['lat'].values, volc_df['lon'].values)
    grid_xyz = _latlon_to_unit_sphere_xyz(grid_df['lat'].values, grid_df['lon'].values)

    tree = cKDTree(volc_xyz)
    chord_dist, idx = tree.query(grid_xyz)

    R = 6371.0
    # chord_dist es la distancia euclidiana entre dos puntos en la esfera
    # unitaria; se convierte a distancia angular (gran circulo) con la
    # formula de la cuerda, y luego a km multiplicando por R.
    central_angle = 2 * np.arcsin(np.clip(chord_dist / 2, -1, 1))
    dist_km = central_angle * R

    res = h3.get_resolution(grid_df['cell_id'].iloc[0])
    volc_cells = volc_df.apply(
        lambda r: h3.latlng_to_cell(r['lat'], r['lon'], res), axis=1
    )
    volcano_per_cell = volc_cells.value_counts()

    result = grid_df[['cell_id']].copy()
    result['dist_nearest_volcano_km'] = dist_km
    result['volcano_count'] = result['cell_id'].map(volcano_per_cell).fillna(0).astype(int)
    return result
