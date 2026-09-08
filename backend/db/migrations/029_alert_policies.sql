-- 029: Alert policies — rules for when to notify entities

CREATE TABLE IF NOT EXISTS alert_policies (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    hazard_types_json TEXT,
    min_severity TEXT DEFAULT 'naranja',
    min_risk_score REAL DEFAULT 0.5,
    target_node_types_json TEXT,
    target_region_ids_json TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    is_dry_run INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS alert_policy_evaluations (
    id TEXT PRIMARY KEY,
    policy_id TEXT NOT NULL,
    incident_id TEXT,
    event_id TEXT,
    eligible_nodes_json TEXT,
    notifications_sent INTEGER DEFAULT 0,
    is_dry_run INTEGER NOT NULL DEFAULT 1,
    evaluated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (policy_id) REFERENCES alert_policies(id)
);

CREATE INDEX IF NOT EXISTS idx_alert_policies_active ON alert_policies(is_active);
CREATE INDEX IF NOT EXISTS idx_alert_evaluations_policy ON alert_policy_evaluations(policy_id);
