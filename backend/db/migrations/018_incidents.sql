-- Migration 018: Create incidents table
-- Central entity for the vertical slice: incident -> decision -> need -> resource -> assignment -> timeline -> outcome

CREATE TABLE IF NOT EXISTS incidents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),

    -- Event identification
    title TEXT NOT NULL,
    description TEXT,
    event_type TEXT NOT NULL DEFAULT 'alerta',       -- alerta | incendio | terremoto | ciclon | volcan | inundacion | otro
    source TEXT NOT NULL DEFAULT 'manual',            -- manual | gdacs | usgs | firms | ibtracs | effis | aemet
    external_id TEXT,                                 -- dedup key from external sources

    -- Classification
    severity TEXT NOT NULL DEFAULT 'moderada',        -- verde | amarilla | naranja | roja
    magnitude REAL,

    -- Location
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    h3_index TEXT,
    direccion TEXT,

    -- State
    status TEXT NOT NULL DEFAULT 'detectado',         -- detectado | evaluado | en_respuesta | resuelto | cancelado
    is_active INTEGER NOT NULL DEFAULT 1,

    -- Operational linkage
    priority_score REAL,
    exposure_score REAL,

    -- Metadata
    metadata TEXT                                     -- JSON for extensibility
);

CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status);
CREATE INDEX IF NOT EXISTS idx_incidents_severity ON incidents(severity);
CREATE INDEX IF NOT EXISTS idx_incidents_event_type ON incidents(event_type);
CREATE INDEX IF NOT EXISTS idx_incidents_h3 ON incidents(h3_index);
CREATE INDEX IF NOT EXISTS idx_incidents_created_at ON incidents(created_at);
CREATE INDEX IF NOT EXISTS idx_incidents_source ON incidents(source);
CREATE INDEX IF NOT EXISTS idx_incidents_location ON incidents(lat, lon);
