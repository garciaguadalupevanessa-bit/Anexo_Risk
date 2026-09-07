-- Migración 010: Recursos para gestión operacional
-- Anexo Risk — Fase B: Modelo de producto

CREATE TABLE IF NOT EXISTS resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL,
    type TEXT NOT NULL CHECK (type IN (
        'vehiculo',
        'ambulancia',
        'bombero',
        'equipo_rescate',
        'suministros',
        'personal',
        'refugio',
        'generador',
        'comunicaciones',
        'otro'
    )),
    name TEXT NOT NULL,
    description TEXT,
    quantity INTEGER NOT NULL DEFAULT 1,
    available_quantity INTEGER NOT NULL DEFAULT 1,
    latitud REAL,
    longitud REAL,
    status TEXT NOT NULL DEFAULT 'disponible' CHECK (status IN (
        'disponible',
        'asignado',
        'en_mantenimiento',
        'retirado'
    )),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (organization_id) REFERENCES organizations(id)
);

CREATE INDEX IF NOT EXISTS idx_resources_org ON resources(organization_id);
CREATE INDEX IF NOT EXISTS idx_resources_type ON resources(type);
CREATE INDEX IF NOT EXISTS idx_resources_status ON resources(status);
CREATE INDEX IF NOT EXISTS idx_resources_location ON resources(latitud, longitud);
