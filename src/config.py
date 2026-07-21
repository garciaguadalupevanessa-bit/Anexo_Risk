"""
Configuración parametrizable del pipeline de preprocesamiento.

Único punto de cambio cuando Persona 3 entregue el schema definitivo.
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
    "columnas_log1p": [
        "magnitud",
        "profundidad",
        "frecuencia",
        "viento",
    ],
    "columnas_dummy": [
        "categoria_tormenta",
        "tipo_volcan",
    ],
    "columnas_excluir": [
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
