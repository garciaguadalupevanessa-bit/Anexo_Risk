-- Migración 013: Risk Engine y versionado de modelos ML
-- Anexo Risk — Fase G: Risk Engine + Fase H: ML

-- Scores de riesgo por celda H3
CREATE TABLE IF NOT EXISTS risk_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    h3_index TEXT NOT NULL,
    severity_score REAL DEFAULT 0,
    exposure_score REAL DEFAULT 0,
    weather_score REAL DEFAULT 0,
    event_density_score REAL DEFAULT 0,
    needs_score REAL DEFAULT 0,
    trend_score REAL DEFAULT 0,
    ml_risk_score REAL,
    ml_confidence REAL,
    combined_score REAL NOT NULL,
    priority_level TEXT CHECK (priority_level IN (
        'critico',
        'alto',
        'medio',
        'bajo',
        'informativo'
    )),
    factors TEXT,
    calculated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (h3_index) REFERENCES spatial_cells(h3_index)
);

-- Versionado de modelos ML
CREATE TABLE IF NOT EXISTS model_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT NOT NULL,
    version TEXT NOT NULL,
    description TEXT,
    training_date TEXT,
    dataset_version TEXT,
    metrics TEXT,
    feature_importance TEXT,
    model_path TEXT,
    status TEXT NOT NULL DEFAULT 'trained' CHECK (status IN (
        'trained',
        'validated',
        'production',
        'deprecated'
    )),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Historial de predicciones
CREATE TABLE IF NOT EXISTS prediction_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_version_id INTEGER NOT NULL,
    h3_index TEXT NOT NULL,
    input_features TEXT,
    prediction REAL,
    confidence REAL,
    actual_value REAL,
    predicted_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (model_version_id) REFERENCES model_versions(id),
    FOREIGN KEY (h3_index) REFERENCES spatial_cells(h3_index)
);

-- Índices para risk engine
CREATE INDEX IF NOT EXISTS idx_risk_scores_h3 ON risk_scores(h3_index);
CREATE INDEX IF NOT EXISTS idx_risk_scores_priority ON risk_scores(priority_level);
CREATE INDEX IF NOT EXISTS idx_risk_scores_combined ON risk_scores(combined_score DESC);
CREATE INDEX IF NOT EXISTS idx_model_versions_name ON model_versions(model_name);
CREATE INDEX IF NOT EXISTS idx_model_versions_status ON model_versions(status);
CREATE INDEX IF NOT EXISTS idx_prediction_history_model ON prediction_history(model_version_id);
CREATE INDEX IF NOT EXISTS idx_prediction_history_h3 ON prediction_history(h3_index);
