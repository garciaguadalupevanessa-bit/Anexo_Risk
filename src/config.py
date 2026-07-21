"""
Pipeline configuration — single point of change for schema alignment.

Joel (Person 3):
  Your H3 grid output must contain columns matching the keys in
  `column_mapping` below (the right-hand side is the current CSV
  column name; the left-hand side is what the pipeline expects).
  If your final schema uses different names, update `column_mapping`
  here — that's the only file you need to touch for naming changes.

  The preprocessing pipeline consumes the following columns from the
  unified DataFrame produced by load_combined_data():

  Feature columns (numeric, used in PCA):
    viento_max_ciclones   — max wind speed (knots)
    presion_min_ciclones  — min central pressure (mb)
    magnitud_max_sismo    — max earthquake magnitude
    profundidad_media_sismo — mean earthquake depth (km)
    elevacion_volcan      — volcano elevation (m)
    frecuencia_eventos_sismicos — earthquake count per cell
    categoria_tormenta    — Saffir-Simpson category (dummy-encoded)
    tipo_volcan           — volcano type (dummy-encoded, optional)

  Coordinate columns (excluded from PCA, passed through):
    lat, lon

  Other columns in this list are silently dropped:
    h3_index, cell_id, volcano_name, region, country

  If you add new features, add them to column_mapping here and
  the pipeline will pick them up automatically.
"""

PREPROCESSING_CONFIG = {
    "column_mapping": {
        "viento_max_ciclones": "USA_WIND",
        "presion_min_ciclones": "USA_PRES",
        "elevacion_volcan": "elevation",
        "tipo_volcan": "type",
        "magnitud_max_sismo": "magnitude",
        "profundidad_media_sismo": "depth_km",
        "lat": "latitude",
        "lon": "longitude",
    },
    "log1p_columns": [
        "magnitud",
        "profundidad",
        "frecuencia",
        "viento",
    ],
    "dummy_columns": [
        "categoria_tormenta",
        "tipo_volcan",
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
