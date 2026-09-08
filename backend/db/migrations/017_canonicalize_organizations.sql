-- Migration 017: Canonicalize duplicate organizations

UPDATE operational_users SET organization_id = 1 WHERE organization_id IN (2,3,4,5,6,7,8);
UPDATE resources SET organization_id = 1 WHERE organization_id IN (2,3,4,5,6,7,8);
UPDATE necesidades SET responsible_organization_id = 1 WHERE responsible_organization_id IN (2,3,4,5,6,7,8);
DELETE FROM organizations WHERE id IN (2,3,4,5,6,7,8);
CREATE UNIQUE INDEX IF NOT EXISTS idx_organizations_name_region ON organizations(name, region);
