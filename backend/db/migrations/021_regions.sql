-- 021: Regions / AOI engine
-- Supports: world, country, region, province, municipality, locality, point, radius, bbox, polygon

CREATE TABLE IF NOT EXISTS regions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    level TEXT NOT NULL DEFAULT 'municipality',
    parent_id TEXT,
    country_code TEXT,
    h3_resolution INTEGER DEFAULT 3,
    geometry_type TEXT,
    geometry_json TEXT,
    bbox_min_lat REAL,
    bbox_min_lon REAL,
    bbox_max_lat REAL,
    bbox_max_lon REAL,
    center_lat REAL,
    center_lon REAL,
    radius_km REAL,
    is_active INTEGER NOT NULL DEFAULT 1,
    source TEXT DEFAULT 'manual',
    metadata_json TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_regions_level ON regions(level);
CREATE INDEX IF NOT EXISTS idx_regions_country ON regions(country_code);
CREATE INDEX IF NOT EXISTS idx_regions_parent ON regions(parent_id);
CREATE INDEX IF NOT EXISTS idx_regions_active ON regions(is_active);

CREATE TABLE IF NOT EXISTS region_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    region_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    is_enabled INTEGER NOT NULL DEFAULT 1,
    priority INTEGER DEFAULT 0,
    config_json TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (region_id) REFERENCES regions(id) ON DELETE CASCADE,
    UNIQUE(region_id, source_id)
);

CREATE INDEX IF NOT EXISTS idx_region_sources_region ON region_sources(region_id);
