-- 031: Live dashboard — aggregated operational status

CREATE TABLE IF NOT EXISTS live_dashboard_cache (
    cache_key TEXT PRIMARY KEY,
    data_json TEXT NOT NULL,
    computed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_dashboard_cache_key ON live_dashboard_cache(cache_key);
