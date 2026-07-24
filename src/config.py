"""
Pipeline configuration — single source of truth for schema alignment.

Expected output columns from load_combined_data():

  Feature columns (numeric, used in PCA):
    eq_count                  earthquake count per cell
    eq_mag_mean               mean earthquake magnitude
    eq_mag_max                max earthquake magnitude
    eq_depth_mean             mean earthquake depth (km)
    eq_energy_log             log10 of total seismic energy
    eq_days_since_last_major  days since last M>=6 earthquake
    cyclone_count             cyclone track points per cell
    wind_mean                 mean wind speed (knots)
    wind_max                  max wind speed (knots)
    pressure_min_mean         mean min central pressure (mb)
    dist_nearest_volcano_km   distance to nearest volcano (km)
    volcano_count             number of volcanoes in cell
    categoria_tormenta        Saffir-Simpson category (dummy-encoded)

  Coordinate columns (excluded from PCA, passed through):
    lat, lon

  Columns silently dropped:
    cell_id
"""

PREPROCESSING_CONFIG = {
    "dummy_columns": [
        "categoria_tormenta",
    ],
    "exclude_columns": [
        "lat",
        "lon",
        "cell_id",
    ],
    "target_variance": 0.85,
    "random_state": 42,
    "h3_resolution": 4,
}
