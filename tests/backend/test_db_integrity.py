"""
Database Integrity Tests — Anexo_Risk
Verifies schema integrity, constraints, data consistency, and migration tracking.

These tests check:
- Foreign key relationships
- NOT NULL constraints
- UNIQUE constraints
- CHECK constraints
- Data consistency (quantities, timestamps, coordinates)
- Migration tracking
- Index existence
- Orphaned records
"""

import pytest
import sqlite3
import os
from pathlib import Path

# Test database path
TEST_DB = Path(__file__).parent.parent.parent / "backend" / "anexo_risk.db"


def get_db_connection():
    """Get a database connection for testing."""
    conn = sqlite3.connect(TEST_DB)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_all_tables(conn):
    """Get all table names."""
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    return [row[0] for row in cursor.fetchall()]


def get_table_columns(conn, table_name):
    """Get column names for a table."""
    cursor = conn.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cursor.fetchall()]


def get_foreign_keys(conn, table_name):
    """Get foreign key definitions for a table."""
    cursor = conn.execute(f"PRAGMA foreign_key_list({table_name})")
    return [
        {"from": row[3], "table": row[2], "to": row[4]}
        for row in cursor.fetchall()
    ]


def get_indexes(conn, table_name):
    """Get index definitions for a table."""
    cursor = conn.execute(f"PRAGMA index_list({table_name})")
    return [
        {"name": row[1], "unique": row[2] == 1}
        for row in cursor.fetchall()
    ]


# ============================================================================
# SCHEMA TESTS
# ============================================================================

class TestSchema:
    """Test schema structure and integrity."""

    def test_all_expected_tables_exist(self):
        """All expected tables should exist."""
        conn = get_db_connection()
        tables = get_all_tables(conn)

        expected = [
            "necesidades",
            "resources",
            "need_assignments",
            "alertas",
            "donaciones",
            "organizations",
            "operational_users",
            "voluntarios",
            "personas",
            "geodata_events",
            "spatial_cells",
            "risk_scores",
            "model_versions",
            "prediction_history",
            "sync_operations",
            "sync_log",
            "schema_migrations",
        ]

        for table in expected:
            assert table in tables, f"Missing table: {table}"

        conn.close()

    def test_necesidades_columns(self):
        """necesidades should have expected columns."""
        conn = get_db_connection()
        columns = get_table_columns(conn, "necesidades")

        required = [
            "id",
            "titulo",
            "descripcion",
            "prioridad",
            "estado",
            "latitud",
            "longitud",
            "creado_en",
        ]

        for col in required:
            assert col in columns, f"necesidades missing column: {col}"

        conn.close()

    def test_resources_columns(self):
        """resources should have expected columns."""
        conn = get_db_connection()
        columns = get_table_columns(conn, "resources")

        required = [
            "id",
            "name",
            "type",
            "quantity",
            "available_quantity",
            "status",
            "latitud",
            "longitud",
        ]

        for col in required:
            assert col in columns, f"resources missing column: {col}"

        conn.close()

    def test_need_assignments_columns(self):
        """need_assignments should have expected columns."""
        conn = get_db_connection()
        columns = get_table_columns(conn, "need_assignments")

        required = [
            "id",
            "need_id",
            "resource_id",
            "quantity_assigned",
            "status",
            "assigned_at",
            "updated_at",
        ]

        for col in required:
            assert col in columns, f"need_assignments missing column: {col}"

        conn.close()

    def test_alertas_columns(self):
        """alertas should have expected columns."""
        conn = get_db_connection()
        columns = get_table_columns(conn, "alertas")

        required = [
            "id",
            "titulo",
            "descripcion",
            "severidad",
            "source",
            "lat",
            "lon",
            "created_at",
        ]

        for col in required:
            assert col in columns, f"alertas missing column: {col}"

        conn.close()

    def test_organizations_columns(self):
        """organizations should have expected columns."""
        conn = get_db_connection()
        columns = get_table_columns(conn, "organizations")

        required = ["id", "name", "type"]

        for col in required:
            assert col in columns, f"organizations missing column: {col}"

        conn.close()


# ============================================================================
# FOREIGN KEY TESTS
# ============================================================================

class TestForeignKeys:
    """Test foreign key relationships."""

    def test_resources_has_organization_fk(self):
        """resources should have FK to organizations."""
        conn = get_db_connection()
        fks = get_foreign_keys(conn, "resources")

        org_fk = [fk for fk in fks if fk["table"] == "organizations"]
        assert len(org_fk) == 1, "resources should have FK to organizations"

        conn.close()

    def test_need_assignments_has_need_fk(self):
        """need_assignments should have FK to necesidades."""
        conn = get_db_connection()
        fks = get_foreign_keys(conn, "need_assignments")

        need_fk = [fk for fk in fks if fk["table"] == "necesidades"]
        assert len(need_fk) == 1, "need_assignments should have FK to necesidades"

        conn.close()

    def test_need_assignments_has_resource_fk(self):
        """need_assignments should have FK to resources."""
        conn = get_db_connection()
        fks = get_foreign_keys(conn, "need_assignments")

        resource_fk = [fk for fk in fks if fk["table"] == "resources"]
        assert len(resource_fk) == 1, "need_assignments should have FK to resources"

        conn.close()

    def test_operational_users_has_organization_fk(self):
        """operational_users should have FK to organizations."""
        conn = get_db_connection()
        fks = get_foreign_keys(conn, "operational_users")

        org_fk = [fk for fk in fks if fk["table"] == "organizations"]
        assert len(org_fk) == 1, "operational_users should have FK to organizations"

        conn.close()

    def test_voluntario_documentos_has_voluntario_fk(self):
        """voluntario_documentos should have FK to voluntarios."""
        conn = get_db_connection()
        fks = get_foreign_keys(conn, "voluntario_documentos")

        vol_fk = [fk for fk in fks if fk["table"] == "voluntarios"]
        assert len(vol_fk) == 1, "voluntario_documentos should have FK to voluntarios"

        conn.close()


# ============================================================================
# DATA INTEGRITY TESTS
# ============================================================================

class TestDataIntegrity:
    """Test data consistency and integrity."""

    def test_no_orphaned_need_assignments_need(self):
        """All need_assignments should reference existing needs."""
        conn = get_db_connection()
        cursor = conn.execute(
            """
            SELECT na.id, na.need_id 
            FROM need_assignments na 
            LEFT JOIN necesidades n ON na.need_id = n.id 
            WHERE n.id IS NULL
            """
        )
        orphans = cursor.fetchall()
        conn.close()

        assert len(orphans) == 0, f"Found orphaned assignments: {orphans}"

    def test_no_orphaned_need_assignments_resource(self):
        """All need_assignments should reference existing resources."""
        conn = get_db_connection()
        cursor = conn.execute(
            """
            SELECT na.id, na.resource_id 
            FROM need_assignments na 
            LEFT JOIN resources r ON na.resource_id = r.id 
            WHERE r.id IS NULL
            """
        )
        orphans = cursor.fetchall()
        conn.close()

        assert len(orphans) == 0, f"Found orphaned assignments: {orphans}"

    def test_no_orphaned_resources_organization(self):
        """All resources should reference existing organizations."""
        conn = get_db_connection()
        cursor = conn.execute(
            """
            SELECT r.id, r.organization_id 
            FROM resources r 
            LEFT JOIN organizations o ON r.organization_id = o.id 
            WHERE r.organization_id IS NOT NULL AND o.id IS NULL
            """
        )
        orphans = cursor.fetchall()
        conn.close()

        assert len(orphans) == 0, f"Found orphaned resources: {orphans}"

    def test_no_negative_quantities(self):
        """No negative quantities in resources."""
        conn = get_db_connection()
        cursor = conn.execute(
            "SELECT id, name, quantity, available_quantity FROM resources WHERE quantity < 0 OR available_quantity < 0"
        )
        negatives = cursor.fetchall()
        conn.close()

        assert len(negatives) == 0, f"Found negative quantities: {negatives}"

    def test_available_not_exceeds_total(self):
        """available_quantity should not exceed quantity."""
        conn = get_db_connection()
        cursor = conn.execute(
            "SELECT id, name, quantity, available_quantity FROM resources WHERE available_quantity > quantity"
        )
        violations = cursor.fetchall()
        conn.close()

        assert len(violations) == 0, f"Found available > total: {violations}"

    def test_assignment_quantity_not_exceeds_available(self):
        """quantity_assigned should not exceed available_quantity."""
        conn = get_db_connection()
        cursor = conn.execute(
            """
            SELECT na.id, na.quantity_assigned, r.available_quantity, r.name
            FROM need_assignments na
            JOIN resources r ON na.resource_id = r.id
            WHERE na.quantity_assigned > r.available_quantity
            """
        )
        violations = cursor.fetchall()
        conn.close()

        assert len(violations) == 0, f"Found assignment exceeds available: {violations}"

    def test_no_null_coordinates_in_necesidades(self):
        """necesidades should have non-null coordinates."""
        conn = get_db_connection()
        cursor = conn.execute(
            "SELECT id, titulo FROM necesidades WHERE latitud IS NULL OR longitud IS NULL"
        )
        nulls = cursor.fetchall()
        conn.close()

        assert len(nulls) == 0, f"Found null coordinates: {nulls}"

    def test_no_null_coordinates_in_resources(self):
        """resources should have non-null coordinates."""
        conn = get_db_connection()
        cursor = conn.execute(
            "SELECT id, name FROM resources WHERE latitud IS NULL OR longitud IS NULL"
        )
        nulls = cursor.fetchall()
        conn.close()

        assert len(nulls) == 0, f"Found null coordinates: {nulls}"

    def test_valid_necesidades_statuses(self):
        """necesidades should have valid status values."""
        conn = get_db_connection()
        valid = {"abierta", "en_progreso", "cubierta", "cancelada"}
        cursor = conn.execute("SELECT id, estado FROM necesidades")
        invalid = [
            (row[0], row[1]) for row in cursor.fetchall() if row[1] not in valid
        ]
        conn.close()

        assert len(invalid) == 0, f"Found invalid statuses: {invalid}"

    def test_valid_resource_statuses(self):
        """resources should have valid status values."""
        conn = get_db_connection()
        valid = {"disponible", "asignado", "en_transito", "agotado", "mantenimiento"}
        cursor = conn.execute("SELECT id, status FROM resources")
        invalid = [
            (row[0], row[1]) for row in cursor.fetchall() if row[1] not in valid
        ]
        conn.close()

        assert len(invalid) == 0, f"Found invalid statuses: {invalid}"

    def test_valid_assignment_statuses(self):
        """need_assignments should have valid status values."""
        conn = get_db_connection()
        valid = {"asignada", "en_progreso", "completada", "cancelada"}
        cursor = conn.execute("SELECT id, status FROM need_assignments")
        invalid = [
            (row[0], row[1]) for row in cursor.fetchall() if row[1] not in valid
        ]
        conn.close()

        assert len(invalid) == 0, f"Found invalid statuses: {invalid}"


# ============================================================================
# TEMPORAL TESTS
# ============================================================================

class TestTemporalIntegrity:
    """Test timestamp consistency."""

    def test_necesidades_have_created_at(self):
        """All necesidades should have created_at."""
        conn = get_db_connection()
        cursor = conn.execute(
            "SELECT id, titulo FROM necesidades WHERE creado_en IS NULL"
        )
        nulls = cursor.fetchall()
        conn.close()

        assert len(nulls) == 0, f"Found necesidades without created_at: {nulls}"

    def test_resources_have_created_at(self):
        """All resources should have created_at."""
        conn = get_db_connection()
        cursor = conn.execute(
            "SELECT id, name FROM resources WHERE created_at IS NULL"
        )
        nulls = cursor.fetchall()
        conn.close()

        assert len(nulls) == 0, f"Found resources without created_at: {nulls}"

    def test_need_assignments_have_assigned_at(self):
        """All need_assignments should have assigned_at."""
        conn = get_db_connection()
        cursor = conn.execute(
            "SELECT id FROM need_assignments WHERE assigned_at IS NULL"
        )
        nulls = cursor.fetchall()
        conn.close()

        assert len(nulls) == 0, f"Found assignments without assigned_at: {nulls}"

    def test_assignment_updated_at_after_assigned_at(self):
        """updated_at should be after or equal to assigned_at."""
        conn = get_db_connection()
        cursor = conn.execute(
            """
            SELECT id, assigned_at, updated_at 
            FROM need_assignments 
            WHERE updated_at < assigned_at
            """
        )
        violations = cursor.fetchall()
        conn.close()

        assert len(violations) == 0, f"Found updated_at < assigned_at: {violations}"


# ============================================================================
# INDEX TESTS
# ============================================================================

class TestIndexes:
    """Test index existence and coverage."""

    def test_necesidades_has_priority_index(self):
        """necesidades should have priority_score index."""
        conn = get_db_connection()
        indexes = get_indexes(conn, "necesidades")
        index_names = [idx["name"] for idx in indexes]

        assert "idx_necesidades_priority" in index_names
        conn.close()

    def test_necesidades_has_incident_index(self):
        """necesidades should have incident_id index."""
        conn = get_db_connection()
        indexes = get_indexes(conn, "necesidades")
        index_names = [idx["name"] for idx in indexes]

        assert "idx_necesidades_incident" in index_names
        conn.close()

    def test_resources_has_location_index(self):
        """resources should have location index."""
        conn = get_db_connection()
        indexes = get_indexes(conn, "resources")
        index_names = [idx["name"] for idx in indexes]

        assert "idx_resources_location" in index_names
        conn.close()

    def test_resources_has_status_index(self):
        """resources should have status index."""
        conn = get_db_connection()
        indexes = get_indexes(conn, "resources")
        index_names = [idx["name"] for idx in indexes]

        assert "idx_resources_status" in index_names
        conn.close()

    def test_need_assignments_has_need_index(self):
        """need_assignments should have need_id index."""
        conn = get_db_connection()
        indexes = get_indexes(conn, "need_assignments")
        index_names = [idx["name"] for idx in indexes]

        assert "idx_need_assignments_need" in index_names
        conn.close()

    def test_need_assignments_has_resource_index(self):
        """need_assignments should have resource_id index."""
        conn = get_db_connection()
        indexes = get_indexes(conn, "need_assignments")
        index_names = [idx["name"] for idx in indexes]

        assert "idx_need_assignments_resource" in index_names
        conn.close()

    def test_alertas_has_source_index(self):
        """alertas should have source index."""
        conn = get_db_connection()
        indexes = get_indexes(conn, "alertas")
        index_names = [idx["name"] for idx in indexes]

        assert "idx_alertas_source" in index_names
        conn.close()

    def test_alertas_has_severidad_index(self):
        """alertas should have severidad index."""
        conn = get_db_connection()
        indexes = get_indexes(conn, "alertas")
        index_names = [idx["name"] for idx in indexes]

        assert "idx_alertas_severidad" in index_names
        conn.close()

    def test_alertas_has_active_location_index(self):
        """alertas should have composite (is_active, lat, lon) index."""
        conn = get_db_connection()
        indexes = get_indexes(conn, "alertas")
        index_names = [idx["name"] for idx in indexes]
        conn.close()

        assert "idx_alertas_active_location" in index_names

    def test_alertas_has_created_at_index(self):
        """alertas should have created_at index for ORDER BY."""
        conn = get_db_connection()
        indexes = get_indexes(conn, "alertas")
        index_names = [idx["name"] for idx in indexes]
        conn.close()

        assert "idx_alertas_created_at" in index_names

    def test_necesidades_has_location_index(self):
        """necesidades should have composite (latitud, longitud) index."""
        conn = get_db_connection()
        indexes = get_indexes(conn, "necesidades")
        index_names = [idx["name"] for idx in indexes]
        conn.close()

        assert "idx_necesidades_location" in index_names

    def test_necesidades_has_estado_index(self):
        """necesidades should have estado index for status filters."""
        conn = get_db_connection()
        indexes = get_indexes(conn, "necesidades")
        index_names = [idx["name"] for idx in indexes]
        conn.close()

        assert "idx_necesidades_estado" in index_names

    def test_necesidades_has_creado_en_index(self):
        """necesidades should have creado_en index for ORDER BY."""
        conn = get_db_connection()
        indexes = get_indexes(conn, "necesidades")
        index_names = [idx["name"] for idx in indexes]
        conn.close()

        assert "idx_necesidades_creado_en" in index_names

    def test_need_assignments_has_assigned_at_index(self):
        """need_assignments should have assigned_at index for ORDER BY."""
        conn = get_db_connection()
        indexes = get_indexes(conn, "need_assignments")
        index_names = [idx["name"] for idx in indexes]
        conn.close()

        assert "idx_need_assignments_assigned_at" in index_names


# ============================================================================
# ORGANIZATION CANONICALIZATION TESTS
# ============================================================================

class TestOrganizationCanonicalization:
    """Test that organizations are properly canonicalized."""

    def test_no_duplicate_organization_names(self):
        """No two organizations should have the same name and region."""
        conn = get_db_connection()
        cursor = conn.execute(
            """
            SELECT name, region, COUNT(*)
            FROM organizations
            GROUP BY name, region
            HAVING COUNT(*) > 1
            """
        )
        duplicates = cursor.fetchall()
        conn.close()

        assert len(duplicates) == 0, f"Found duplicate (name, region): {duplicates}"

    def test_all_resources_reference_canonical_org(self):
        """All resources should reference an existing organization."""
        conn = get_db_connection()
        cursor = conn.execute(
            """
            SELECT r.id, r.organization_id
            FROM resources r
            LEFT JOIN organizations o ON r.organization_id = o.id
            WHERE o.id IS NULL
            """
        )
        orphans = cursor.fetchall()
        conn.close()

        assert len(orphans) == 0, f"Found orphaned resource org references: {orphans}"

    def test_all_operational_users_reference_canonical_org(self):
        """All operational_users should reference an existing organization."""
        conn = get_db_connection()
        cursor = conn.execute(
            """
            SELECT u.id, u.organization_id
            FROM operational_users u
            LEFT JOIN organizations o ON u.organization_id = o.id
            WHERE o.id IS NULL
            """
        )
        orphans = cursor.fetchall()
        conn.close()

        assert len(orphans) == 0, f"Found orphaned user org references: {orphans}"


# ============================================================================
# MIGRATION TESTS
# ============================================================================

class TestMigrations:
    """Test migration tracking and consistency."""

    def test_migrations_table_exists(self):
        """schema_migrations table should exist."""
        conn = get_db_connection()
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations'"
        )
        result = cursor.fetchone()
        conn.close()

        assert result is not None, "schema_migrations table not found"

    def test_migrations_have_timestamps(self):
        """All migrations should have timestamp entries."""
        conn = get_db_connection()
        cursor = conn.execute("SELECT COUNT(*) FROM schema_migrations")
        count = cursor.fetchone()[0]
        conn.close()

        assert count >= 17, f"Expected at least 17 migrations, found {count}"

    def test_migration_files_match_database(self):
        """Migration files should match database entries."""
        migration_dir = Path(__file__).parent.parent.parent / "backend" / "db" / "migrations"
        migration_files = sorted([f.name for f in migration_dir.glob("*.sql") if f.stem[0].isdigit()])

        conn = get_db_connection()
        cursor = conn.execute("SELECT nombre FROM schema_migrations ORDER BY nombre")
        db_migrations = [row[0] for row in cursor.fetchall()]
        conn.close()

        # Check that all file migrations are in database
        for migration in migration_files:
            assert migration in db_migrations, f"Migration {migration} not in database"


# ============================================================================
# CONSISTENCY TESTS
# ============================================================================

class TestConsistency:
    """Test cross-table data consistency."""

    def test_need_assignment_counts_match(self):
        """Sum of quantity_assigned should not exceed available_quantity."""
        conn = get_db_connection()
        cursor = conn.execute(
            """
            SELECT r.id, r.name, r.available_quantity, COALESCE(SUM(na.quantity_assigned), 0) as total_assigned
            FROM resources r
            LEFT JOIN need_assignments na ON r.id = na.resource_id AND na.status = 'asignada'
            GROUP BY r.id
            HAVING total_assigned > r.available_quantity
            """
        )
        violations = cursor.fetchall()
        conn.close()

        assert len(violations) == 0, f"Found assignment violations: {violations}"

    def test_need_covered_matches_assignments(self):
        """need covered quantity should match sum of assignments."""
        conn = get_db_connection()
        cursor = conn.execute(
            """
            SELECT n.id, n.titulo, n.covered_quantity cubierta,
                   COALESCE(SUM(na.quantity_assigned), 0) as assigned
            FROM necesidades n
            LEFT JOIN need_assignments na ON n.id = na.need_id AND na.status = 'asignada'
            WHERE n.estado = 'cubierta'
            GROUP BY n.id
            HAVING cubierta != assigned
            """
        )
        violations = cursor.fetchall()
        conn.close()

        assert len(violations) == 0, f"Found covered/assignment mismatch: {violations}"

    def test_resource_status_consistent_with_assignments(self):
        """Resource status should be 'asignado' if it has active assignments."""
        conn = get_db_connection()
        cursor = conn.execute(
            """
            SELECT r.id, r.name, r.status
            FROM resources r
            JOIN need_assignments na ON r.id = na.resource_id
            WHERE na.status = 'asignada' AND r.status != 'asignado'
            GROUP BY r.id
            """
        )
        inconsistencies = cursor.fetchall()
        conn.close()

        assert len(inconsistencies) == 0, f"Found status inconsistencies: {inconsistencies}"


# ============================================================================
# DATA COMPLETENESS TESTS
# ============================================================================

class TestDataCompleteness:
    """Test data completeness for operational readiness."""

    def test_at_least_one_organization(self):
        """Should have at least one organization."""
        conn = get_db_connection()
        cursor = conn.execute("SELECT COUNT(*) FROM organizations")
        count = cursor.fetchone()[0]
        conn.close()

        assert count >= 1, f"Expected at least 1 organization, found {count}"

    def test_at_least_one_operational_user(self):
        """Should have at least one operational user."""
        conn = get_db_connection()
        cursor = conn.execute("SELECT COUNT(*) FROM operational_users")
        count = cursor.fetchone()[0]
        conn.close()

        assert count >= 1, f"Expected at least 1 operational user, found {count}"

    def test_alertas_have_valid_coordinates(self):
        """alertas should have valid coordinate ranges."""
        conn = get_db_connection()
        cursor = conn.execute(
            """
            SELECT id, lat, lon FROM alertas 
            WHERE lat < -90 OR lat > 90 OR lon < -180 OR lon > 180
            """
        )
        invalid = cursor.fetchall()
        conn.close()

        assert len(invalid) == 0, f"Found invalid coordinates: {invalid}"

    def test_necesidades_have_valid_coordinates(self):
        """necesidades should have valid coordinate ranges."""
        conn = get_db_connection()
        cursor = conn.execute(
            """
            SELECT id, latitud, longitud FROM necesidades 
            WHERE latitud < -90 OR latitud > 90 OR longitud < -180 OR longitud > 180
            """
        )
        invalid = cursor.fetchall()
        conn.close()

        assert len(invalid) == 0, f"Found invalid coordinates: {invalid}"

    def test_resources_have_valid_coordinates(self):
        """resources should have valid coordinate ranges."""
        conn = get_db_connection()
        cursor = conn.execute(
            """
            SELECT id, latitud, longitud FROM resources 
            WHERE latitud < -90 OR latitud > 90 OR longitud < -180 OR longitud > 180
            """
        )
        invalid = cursor.fetchall()
        conn.close()

        assert len(invalid) == 0, f"Found invalid coordinates: {invalid}"


# ============================================================================
# UNIQUE CONSTRAINT TESTS
# ============================================================================

class TestUniqueConstraints:
    """Test unique constraints on key columns."""

    def test_alertas_external_id_unique(self):
        """alertas external_id should be unique (when not null)."""
        conn = get_db_connection()
        cursor = conn.execute(
            """
            SELECT external_id, COUNT(*) 
            FROM alertas 
            WHERE external_id IS NOT NULL 
            GROUP BY external_id 
            HAVING COUNT(*) > 1
            """
        )
        duplicates = cursor.fetchall()
        conn.close()

        assert len(duplicates) == 0, f"Found duplicate external_ids: {duplicates}"

    def test_operational_users_username_unique(self):
        """operational_users username should be unique."""
        conn = get_db_connection()
        cursor = conn.execute(
            """
            SELECT username, COUNT(*) 
            FROM operational_users 
            GROUP BY username 
            HAVING COUNT(*) > 1
            """
        )
        duplicates = cursor.fetchall()
        conn.close()

        assert len(duplicates) == 0, f"Found duplicate usernames: {duplicates}"

    def test_organizations_name_unique(self):
        """organizations should have unique (name, region) constraint."""
        conn = get_db_connection()
        cursor = conn.execute(
            """
            SELECT name, region, COUNT(*)
            FROM organizations
            GROUP BY name, region
            HAVING COUNT(*) > 1
            """
        )
        duplicates = cursor.fetchall()
        conn.close()

        assert len(duplicates) == 0, f"Found duplicate (name, region): {duplicates}"

    def test_organizations_has_name_region_index(self):
        """organizations should have unique index on (name, region)."""
        conn = get_db_connection()
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='organizations' AND name='idx_organizations_name_region'"
        )
        result = cursor.fetchone()
        conn.close()

        assert result is not None, "Missing unique index idx_organizations_name_region"
