-- 025: Operational nodes — hospitals, fire stations, shelters, logistics bases

CREATE TABLE IF NOT EXISTS operational_nodes (
    id TEXT PRIMARY KEY,
    external_id TEXT,
    node_type TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    h3_index TEXT,
    address TEXT,
    city TEXT,
    province TEXT,
    country_code TEXT,
    capacity INTEGER,
    current_occupancy INTEGER DEFAULT 0,
    capabilities_json TEXT,
    status TEXT DEFAULT 'active',
    is_active INTEGER NOT NULL DEFAULT 1,
    source TEXT DEFAULT 'manual',
    metadata_json TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_operational_nodes_type ON operational_nodes(node_type);
CREATE INDEX IF NOT EXISTS idx_operational_nodes_h3 ON operational_nodes(h3_index);
CREATE INDEX IF NOT EXISTS idx_operational_nodes_status ON operational_nodes(status, is_active);
CREATE INDEX IF NOT EXISTS idx_operational_nodes_country ON operational_nodes(country_code);
