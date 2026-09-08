-- 028: Action areas — computed per-incident affected zones

CREATE TABLE IF NOT EXISTS action_areas (
    id TEXT PRIMARY KEY,
    incident_id TEXT,
    event_id TEXT,
    area_type TEXT NOT NULL,
    hazard_type TEXT,
    radius_km REAL,
    buffer_geometry_json TEXT,
    h3_cells_json TEXT,
    risk_level TEXT,
    severity_float REAL,
    is_active INTEGER NOT NULL DEFAULT 1,
    computed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_action_areas_incident ON action_areas(incident_id);
CREATE INDEX IF NOT EXISTS idx_action_areas_hazard ON action_areas(hazard_type);
CREATE INDEX IF NOT EXISTS idx_action_areas_h3 ON action_areas(h3_cells_json);
