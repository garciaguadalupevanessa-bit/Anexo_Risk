-- Migration 015: Add 6 HIGH-priority indexes for operational routes

CREATE INDEX IF NOT EXISTS idx_alertas_active_location ON alertas(is_active, lat, lon);
CREATE INDEX IF NOT EXISTS idx_alertas_created_at ON alertas(created_at);
CREATE INDEX IF NOT EXISTS idx_necesidades_location ON necesidades(latitud, longitud);
CREATE INDEX IF NOT EXISTS idx_necesidades_estado ON necesidades(estado);
CREATE INDEX IF NOT EXISTS idx_necesidades_creado_en ON necesidades(creado_en);
CREATE INDEX IF NOT EXISTS idx_need_assignments_assigned_at ON need_assignments(assigned_at);
