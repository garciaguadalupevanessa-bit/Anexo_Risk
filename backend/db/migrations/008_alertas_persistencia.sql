CREATE TABLE IF NOT EXISTS alertas (
    id TEXT PRIMARY KEY,
    external_id TEXT,
    source TEXT NOT NULL DEFAULT 'GDACS',
    tipo TEXT NOT NULL DEFAULT 'otro',
    titulo TEXT NOT NULL DEFAULT '',
    descripcion TEXT NOT NULL DEFAULT '',
    severidad TEXT NOT NULL DEFAULT 'GREEN',
    risk_level TEXT NOT NULL DEFAULT 'low',
    status TEXT NOT NULL DEFAULT 'active',
    is_active INTEGER NOT NULL DEFAULT 1,
    zone TEXT,
    pais TEXT NOT NULL DEFAULT '',
    lat REAL,
    lon REAL,
    fecha TEXT,
    enlace TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_alertas_source ON alertas(source);
CREATE INDEX IF NOT EXISTS idx_alertas_severidad ON alertas(severidad);
CREATE INDEX IF NOT EXISTS idx_alertas_pais ON alertas(pais);
CREATE INDEX IF NOT EXISTS idx_alertas_external_id ON alertas(external_id);
