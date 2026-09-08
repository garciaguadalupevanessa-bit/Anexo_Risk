-- 026: Network links — roads, corridors, routes with status

CREATE TABLE IF NOT EXISTS network_links (
    id TEXT PRIMARY KEY,
    external_id TEXT,
    link_type TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    start_node_id TEXT,
    end_node_id TEXT,
    start_lat REAL,
    start_lon REAL,
    end_lat REAL,
    end_lon REAL,
    h3_start TEXT,
    h3_end TEXT,
    distance_km REAL,
    estimated_time_min REAL,
    status TEXT DEFAULT 'open',
    capacity INTEGER,
    restrictions_json TEXT,
    source TEXT DEFAULT 'manual',
    metadata_json TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT,
    FOREIGN KEY (start_node_id) REFERENCES operational_nodes(id),
    FOREIGN KEY (end_node_id) REFERENCES operational_nodes(id)
);

CREATE INDEX IF NOT EXISTS idx_network_links_type ON network_links(link_type);
CREATE INDEX IF NOT EXISTS idx_network_links_status ON network_links(status);
CREATE INDEX IF NOT EXISTS idx_network_links_start ON network_links(start_node_id);
CREATE INDEX IF NOT EXISTS idx_network_links_end ON network_links(end_node_id);
CREATE INDEX IF NOT EXISTS idx_network_links_h3_start ON network_links(h3_start);
