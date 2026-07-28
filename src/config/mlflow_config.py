MLFLOW_EXPERIMENT = "georisk_preprocessing"
MLFLOW_TRACKING_URI = "sqlite:///mlflow.db"
ENABLE_TRACKING = True
REGISTER_MODELS = True
ARTIFACT_PATH = "pipeline_riesgo"

RUN_NAME_TEMPLATE = "{source} {n_samples}x{n_features} -> {n_pc} PC ({var_pct:.0f}% var)"

FIGURES_DIR = "outputs/figures"
MODELS_DIR = "models"

DEFAULT_TAGS = {
    "project": "georisk_finder",
    "dataset": "grid_features",
    "environment": "development",
    "pipeline_version": "1.0.0",
}

EXPLAINED_VARIANCE_THRESHOLD = 0.85
RANDOM_STATE = 42
H3_RESOLUTION = 3
SKEW_THRESHOLD = 0.75
PCA_SOLVER = "auto"

FIGURES_DIR = "outputs/figures"
MODELS_DIR = "models"
