-- 023: Normalized events table — stores events from all adapters in common format

CREATE TABLE IF NOT EXISTS normalized_events (
    id TEXT PRIMARY KEY,
    external_id TEXT,
    entity_type TEXT NOT NULL,
    source TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    timestamp TEXT,
    updated_at TEXT,
    severity TEXT,
    severity_float REAL,
    lat REAL,
    lon REAL,
    geometry_type TEXT,
    geometry_json TEXT,
    country TEXT,
    region TEXT,
    status TEXT DEFAULT 'active',
    is_active INTEGER NOT NULL DEFAULT 1,
    h3_index TEXT,
    magnitude REAL,
    depth REAL,
    confidence REAL,
    raw_metadata_json TEXT,
    provenance_json TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_normalized_events_source ON normalized_events(source);
CREATE INDEX IF NOT EXISTS idx_normalized_events_entity ON normalized_events(entity_type);
CREATE INDEX IF NOT EXISTS idx_normalized_events_h3 ON normalized_events(h3_index);
CREATE INDEX IF NOT EXISTS idx_normalized_events_timestamp ON normalized_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_normalized_events_status ON normalized_events(status, is_active);
CREATE INDEX IF NOT EXISTS idx_normalized_events_severity ON normalized_events(severity);
