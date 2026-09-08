-- Migration 016: Formal creation of feedback_loop table
-- This table was previously created dynamically by models/feedback.py.
-- This migration brings it into the formal migration system.
--
-- Idempotent: Uses CREATE TABLE IF NOT EXISTS.
-- Compatible with existing data: The table may already exist with data
-- from feedback.py's init_feedback_table().

CREATE TABLE IF NOT EXISTS feedback_loop (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),

    -- Prediction (from Anexo_Risk or GeoRisk)
    prediction_source TEXT NOT NULL,        -- 'anexo_risk' | 'georisk'
    model_version TEXT,
    predicted_level TEXT,                    -- 'critica' | 'alta' | 'moderada' | 'informativa'
    predicted_score REAL,
    prediction_time TEXT NOT NULL,           -- ISO 8601

    -- H3 spatial reference
    h3_index TEXT,
    lat REAL,
    lon REAL,

    -- Operational context at prediction time
    needs_open_at_prediction INTEGER,
    resources_available_at_prediction INTEGER,

    -- Operational outcome (filled after resolution)
    incident_id TEXT,
    outcome_time TEXT,                       -- ISO 8601
    incident_closed INTEGER DEFAULT 0,       -- 0/1
    needs_created INTEGER DEFAULT 0,
    needs_resolved INTEGER DEFAULT 0,
    resource_gap_at_outcome INTEGER DEFAULT 0,
    response_duration_hours REAL,            -- hours from prediction to outcome
    escalation_occurred INTEGER DEFAULT 0,   -- 0/1

    -- Metadata
    metadata TEXT                            -- JSON for extensibility
);

CREATE INDEX IF NOT EXISTS idx_feedback_h3
    ON feedback_loop(h3_index);

CREATE INDEX IF NOT EXISTS idx_feedback_prediction_time
    ON feedback_loop(prediction_time);
