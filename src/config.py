"""
Parametrizable preprocessing pipeline configuration.

Single point of change when Persona 3 delivers the final schema.
"""

PREPROCESSING_CONFIG = {
    "column_mapping": {
        "magnitud_max_sismo": None,
        "profundidad_media_sismo": None,
        "frecuencia_eventos_sismicos": None,
        "viento_max_ciclones": None,
        "presion_min_ciclones": None,
        "categoria_tormenta": None,
        "elevacion_volcan": None,
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
}
