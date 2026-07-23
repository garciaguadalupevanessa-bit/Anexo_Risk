"""
Pipeline configuration — single source of truth for schema alignment.

Expected output columns from load_combined_data():

  Feature columns (numeric, used in PCA):
    viento_max_ciclones       max wind speed (knots)
    presion_min_ciclones      min central pressure (mb)
    magnitud_max_sismo        max earthquake magnitude
    profundidad_media_sismo   mean earthquake depth (km)
    elevacion_volcan          volcano elevation (m)
    frecuencia_eventos_sismicos  earthquake count per cell
    categoria_tormenta        Saffir-Simpson category (dummy-encoded)

  Coordinate columns (excluded from PCA, passed through):
    lat, lon

  Columns silently dropped:
    h3_index, cell_id, volcano_name, region, country

If you add new features (Joel, Person 3 add new features), register the
source column name in the appropriate source_mapping below and the
pipeline will pick them up automatically.
"""

PREPROCESSING_CONFIG = {
    "source_mapping": {
        "ciclones": {
            "viento_max_ciclones": "wind",
            "presion_min_ciclones": "pressure",
        },
        "volcanes": {
            "elevacion_volcan": "elevation",
        },
        "espana": {
            "magnitud_max_sismo": "magnitude",
            "profundidad_media_sismo": "depth_km",
        },
    },
    "dummy_columns": [
        "categoria_tormenta",
    ],
    "exclude_columns": [
        "lat",
        "lon",
        "h3_index",
        "cell_id",
        "volcano_name",
        "region",
        "country",
    ],
    "target_variance": 0.85,
    "random_state": 42,
    "data_sources": {
        "ciclones": "data/processed/ciclones_clean.csv",
        "volcanes": "data/processed/volcanes_clean.csv",
        "espana": "data/processed/espana_clean.csv",
    },
    "h3_resolution": 4,
}
