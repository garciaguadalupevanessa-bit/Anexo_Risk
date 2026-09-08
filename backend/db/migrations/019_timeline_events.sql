-- Migration 019: Create timeline_events table
-- Records the operational lifecycle of an incident

CREATE TABLE IF NOT EXISTS timeline_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),

    -- Linkage
    incident_id INTEGER NOT NULL,
    need_id INTEGER,
    resource_id INTEGER,
    assignment_id INTEGER,

    -- Event
    event_type TEXT NOT NULL,       -- detected | evaluated | risk_updated | need_created | resource_assigned | in_transit | delivered | resolved | escalated | outcome_recorded
    description TEXT NOT NULL,
    actor TEXT,                     -- 'system' | 'operator:{username}' | 'georisk'

    -- Snapshot
    priority_score REAL,
    severity TEXT,
    status_snapshot TEXT,           -- status of the incident at this point

    -- Metadata
    metadata TEXT,                  -- JSON for extensibility

    FOREIGN KEY (incident_id) REFERENCES incidents(id)
);

CREATE INDEX IF NOT EXISTS idx_timeline_incident ON timeline_events(incident_id);
CREATE INDEX IF NOT EXISTS idx_timeline_event_type ON timeline_events(event_type);
CREATE INDEX IF NOT EXISTS idx_timeline_created_at ON timeline_events(created_at);
