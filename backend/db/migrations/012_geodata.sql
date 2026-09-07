-- Migración 012: Tablas geoespaciales para GeoData Engine
-- Anexo Risk — Fase C: GeoData Engine + GeoPandas + H3

-- Eventos geoespaciales normalizados (sismos, ciclones, volcanes, incendios)
CREATE TABLE IF NOT EXISTS geodata_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL CHECK (source IN (
        'usgs',
        'ibtracs',
        'smithsonian',
        'firms',
        'gdacs',
        'copernicus',
        'custom'
    )),
    event_type TEXT NOT NULL CHECK (event_type IN (
        'terremoto',
        'ciclon',
        'volcan',
        'incendio',
        'inundacion',
        'otro'
    )),
    external_id TEXT,
    title TEXT,
    description TEXT,
    severity REAL,
    magnitude REAL,
    depth REAL,
    brightness REAL,
    frp REAL,
    confidence REAL,
    latitud REAL NOT NULL,
    longitud REAL NOT NULL,
    event_time TEXT,
    h3_index TEXT,
    h3_resolution INTEGER DEFAULT 7,
    raw_data TEXT,
    fetched_at TEXT NOT NULL DEFAULT (datetime('now')),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Celdas H3 para agregación espacial
CREATE TABLE IF NOT EXISTS spatial_cells (
    h3_index TEXT PRIMARY KEY,
    resolution INTEGER NOT NULL,
    centroid_lat REAL NOT NULL,
    centroid_lon REAL NOT NULL,
    risk_score REAL DEFAULT 0,
    event_count INTEGER DEFAULT 0,
    population_exposed INTEGER DEFAULT 0,
    needs_count INTEGER DEFAULT 0,
    resources_count INTEGER DEFAULT 0,
    last_updated TEXT DEFAULT (datetime('now'))
);

-- Índices para consultas geoespaciales
CREATE INDEX IF NOT EXISTS idx_geodata_source ON geodata_events(source);
CREATE INDEX IF NOT EXISTS idx_geodata_type ON geodata_events(event_type);
CREATE INDEX IF NOT EXISTS idx_geodata_h3 ON geodata_events(h3_index);
CREATE INDEX IF NOT EXISTS idx_geodata_time ON geodata_events(event_time);
CREATE INDEX IF NOT EXISTS idx_geodata_location ON geodata_events(latitud, longitud);
CREATE INDEX IF NOT EXISTS idx_spatial_cells_resolution ON spatial_cells(resolution);
CREATE INDEX IF NOT EXISTS idx_spatial_cells_risk ON spatial_cells(risk_score DESC);
