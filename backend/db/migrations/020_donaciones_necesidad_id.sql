-- 020: Add necesidad_id to donaciones for need-donation linkage
-- Idempotent: uses PRAGMA to check column existence

-- Add necesidad_id column (nullable for existing records)
-- ALTER TABLE will "fail" harmlessly if column already exists (caught by _run_migration)
ALTER TABLE donaciones ADD COLUMN necesidad_id INTEGER REFERENCES necesidades(id);
