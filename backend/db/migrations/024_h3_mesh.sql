-- 024: H3 operational mesh — per-cell aggregation and spatial queries

CREATE TABLE IF NOT EXISTS h3_cells (
    h3_index TEXT NOT NULL,
    resolution INTEGER NOT NULL,
    event_count INTEGER NOT NULL DEFAULT 0,
    incident_count INTEGER NOT NULL DEFAULT 0,
    avg_severity REAL DEFAULT 0.0,
    max_severity REAL DEFAULT 0.0,
    avg_risk_score REAL DEFAULT 0.0,
    entity_types_json TEXT,
    sources_json TEXT,
    last_event_at TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (h3_index, resolution)
);

CREATE INDEX IF NOT EXISTS idx_h3_cells_resolution ON h3_cells(resolution);
CREATE INDEX IF NOT EXISTS idx_h3_cells_event_count ON h3_cells(event_count DESC);
