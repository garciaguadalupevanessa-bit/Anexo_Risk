-- 027: Accessibility cache — stores computed reachability between nodes

CREATE TABLE IF NOT EXISTS accessibility_cache (
    origin_node_id TEXT NOT NULL,
    destination_node_id TEXT NOT NULL,
    is_reachable INTEGER NOT NULL DEFAULT 0,
    shortest_distance_km REAL,
    shortest_time_min REAL,
    path_link_ids_json TEXT,
    blocking_count INTEGER DEFAULT 0,
    computed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (origin_node_id, destination_node_id)
);

CREATE INDEX IF NOT EXISTS idx_accessibility_origin ON accessibility_cache(origin_node_id);
CREATE INDEX IF NOT EXISTS idx_accessibility_reachable ON accessibility_cache(is_reachable);
