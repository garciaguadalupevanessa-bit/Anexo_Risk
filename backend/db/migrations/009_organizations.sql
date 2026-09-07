-- Migración 009: Organizaciones y usuarios operacionales
-- Anexo Risk — Fase B: Modelo de producto

CREATE TABLE IF NOT EXISTS organizations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN (
        'municipio',
        'proteccion_civil',
        '112',
        'bomberos',
        'policia',
        'ong',
        'hospital',
        'organismo_autonomico',
        'otro'
    )),
    region TEXT,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS operational_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL,
    username TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN (
        'operador',
        'coordinador_recursos',
        'analista',
        'administrador'
    )),
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (organization_id) REFERENCES organizations(id)
);

CREATE INDEX IF NOT EXISTS idx_organizations_type ON organizations(type);
CREATE INDEX IF NOT EXISTS idx_organizations_region ON organizations(region);
CREATE INDEX IF NOT EXISTS idx_operational_users_org ON operational_users(organization_id);
CREATE INDEX IF NOT EXISTS idx_operational_users_role ON operational_users(role);
