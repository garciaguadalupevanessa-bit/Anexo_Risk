-- 030: Federated organizations — region-scoped permissions and RBAC

ALTER TABLE organizations ADD COLUMN region_id TEXT;
ALTER TABLE organizations ADD COLUMN permissions_json TEXT;
ALTER TABLE organizations ADD COLUMN parent_org_id TEXT;
ALTER TABLE organizations ADD COLUMN federation_level TEXT DEFAULT 'local';

CREATE TABLE IF NOT EXISTS org_region_access (
    org_id INTEGER NOT NULL,
    region_id TEXT NOT NULL,
    access_level TEXT DEFAULT 'read',
    granted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (org_id, region_id)
);

CREATE INDEX IF NOT EXISTS idx_org_region_org ON org_region_access(org_id);
CREATE INDEX IF NOT EXISTS idx_org_region_region ON org_region_access(region_id);
