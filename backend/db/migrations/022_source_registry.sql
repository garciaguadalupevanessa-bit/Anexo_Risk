-- 022: Source registry — central catalog of all data sources

CREATE TABLE IF NOT EXISTS source_registry (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    scope TEXT DEFAULT 'global',
    source_type TEXT DEFAULT 'api',
    data_types TEXT,
    supports_point INTEGER DEFAULT 0,
    supports_bbox INTEGER DEFAULT 0,
    supports_region INTEGER DEFAULT 0,
    update_interval_seconds INTEGER DEFAULT 300,
    authentication TEXT DEFAULT 'none',
    license TEXT,
    status TEXT DEFAULT 'active',
    last_successful_fetch TEXT,
    last_failure TEXT,
    last_error TEXT,
    latency_ms REAL,
    freshness_seconds REAL,
    cache_ttl_seconds INTEGER DEFAULT 300,
    endpoint_url TEXT,
    metadata_json TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_source_registry_status ON source_registry(status);
CREATE INDEX IF NOT EXISTS idx_source_registry_scope ON source_registry(scope);
