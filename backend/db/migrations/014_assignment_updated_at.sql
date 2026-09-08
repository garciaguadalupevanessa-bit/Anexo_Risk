-- Migración 014: Añadir updated_at a need_assignments
-- Anexo Risk — Fase C: Asignación de recursos

-- NOTA: SQLite no soporta ADD COLUMN con DEFAULT basado en datetime('now')
-- La columna se maneja desde el código Python.
ALTER TABLE need_assignments ADD COLUMN updated_at TEXT;
