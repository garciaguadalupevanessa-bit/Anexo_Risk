-- Migración 011: Necesidades extendidas con gestión de recursos
-- Anexo Risk — Fase B: Modelo de producto

-- Extender tabla necesidades existente con columnas nuevas
-- NOTA: SQLite no permite defaults no constantes en ALTER TABLE
ALTER TABLE necesidades ADD COLUMN incident_id TEXT;
ALTER TABLE necesidades ADD COLUMN priority_score REAL;
ALTER TABLE necesidades ADD COLUMN quantity INTEGER;
ALTER TABLE necesidades ADD COLUMN covered_quantity INTEGER;
ALTER TABLE necesidades ADD COLUMN assigned_resource_id INTEGER;
ALTER TABLE necesidades ADD COLUMN responsible_organization_id INTEGER;
ALTER TABLE necesidades ADD COLUMN updated_at TEXT;

-- Tabla de asignaciones de recursos a necesidades
CREATE TABLE IF NOT EXISTS need_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    need_id INTEGER NOT NULL,
    resource_id INTEGER NOT NULL,
    quantity_assigned INTEGER NOT NULL DEFAULT 1,
    assigned_by INTEGER REFERENCES operational_users(id),
    assigned_at TEXT NOT NULL DEFAULT (datetime('now')),
    status TEXT NOT NULL DEFAULT 'asignado' CHECK (status IN (
        'asignado',
        'en_curso',
        'completado',
        'cancelado'
    )),
    notes TEXT,
    FOREIGN KEY (need_id) REFERENCES necesidades(id),
    FOREIGN KEY (resource_id) REFERENCES resources(id)
);

CREATE INDEX IF NOT EXISTS idx_need_assignments_need ON need_assignments(need_id);
CREATE INDEX IF NOT EXISTS idx_need_assignments_resource ON need_assignments(resource_id);
CREATE INDEX IF NOT EXISTS idx_need_assignments_status ON need_assignments(status);
CREATE INDEX IF NOT EXISTS idx_necesidades_priority ON necesidades(priority_score);
CREATE INDEX IF NOT EXISTS idx_necesidades_incident ON necesidades(incident_id);
