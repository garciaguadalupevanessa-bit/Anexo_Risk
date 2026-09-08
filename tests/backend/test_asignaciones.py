"""Pruebas del módulo de asignaciones — Fase C.

Cubre:
- Creación de asignaciones con validación de reglas de negocio
- Transiciones de estado (asignado -> en_curso -> completado | cancelado)
- Deducción de disponibilidad del recurso
- Actualización de covered_quantity en necesidades
- Cierre automático de necesidades al cubrir toda la cantidad
- Errores: recurso no disponible, cantidad insuficiente, necesidad cerrada
- Listado con filtros
- Resumen de asignaciones por necesidad
"""
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from db import database
from modules.asignaciones.models import (
    AssignmentValidationError,
    InsufficientQuantityError,
    create_assignment,
    get_assignment,
    get_assignments_for_need,
    list_assignments,
    update_assignment_status,
)
from modules.asignaciones.schemas import AssignmentCreate, AssignmentStatus
from modules.asignaciones.services import (
    assign_resource_to_need,
    get_assignment_summary,
    transition_assignment_status,
)
from modules.necesidades.schemas import NeedCreate
from modules.necesidades.services import create_need, get_need
from modules.recursos.models import create_resource, get_resource


@pytest.fixture(autouse=True)
def temporary_database():
    """Crea una base de datos SQLite aislada para cada prueba."""
    previous_path = database.DATABASE_PATH
    with TemporaryDirectory() as temp_directory:
        database.DATABASE_PATH = str(Path(temp_directory) / "nexo_test.db")
        database.init_db()
        try:
            yield
        finally:
            database.DATABASE_PATH = previous_path


def _create_test_need(quantity: int = 50) -> dict:
    """Crea una necesidad de prueba con quantity configurado via SQL directo."""
    need = NeedCreate(
        titulo="Agua potable",
        tipo="agua",
        descripcion="Se necesita agua para 100 personas",
        latitud=39.4699,
        longitud=-0.3763,
    )
    created = create_need(need)
    # quantity es una columna de migración 011; se establece directamente
    with database.get_cursor() as cur:
        cur.execute(
            "UPDATE necesidades SET quantity = ? WHERE id = ?",
            (quantity, created["id"]),
        )
    return get_need(created["id"])


def _create_test_resource(**overrides) -> dict:
    """Crea un recurso de prueba, creando la organización FK si es necesario."""
    # Crear organización FK si no existe
    with database.get_cursor() as cur:
        cur.execute("SELECT id FROM organizations LIMIT 1")
        row = cur.fetchone()
        if row is None:
            cur.execute(
                "INSERT INTO organizations (name, type) VALUES (?, ?)",
                ("Org Test", "municipio"),
            )
            org_id = cur.lastrowid
        else:
            org_id = row["id"]

    defaults = {
        "org_id": org_id,
        "resource_type": "suministros",
        "name": "Camión de agua",
        "description": "Camión cisterna 5000L",
        "quantity": 10,
        "latitud": 39.47,
        "longitud": -0.38,
    }
    defaults.update(overrides)
    return create_resource(**defaults)


# --- Tests de creación de asignación ---

class TestAssignmentCreation:
    def test_create_assignment_successfully(self):
        """Asignar un recurso disponible a una necesidad abierta."""
        need = _create_test_need()
        resource = _create_test_resource()

        assignment = assign_resource_to_need(
            need_id=need["id"],
            resource_id=resource["id"],
            quantity_assigned=5,
        )

        assert assignment["need_id"] == need["id"]
        assert assignment["resource_id"] == resource["id"]
        assert assignment["quantity_assigned"] == 5
        assert assignment["status"] == "asignado"

    def test_assignment_decrements_resource_availability(self):
        """La asignación decrementa available_quantity del recurso."""
        need = _create_test_need()
        resource = _create_test_resource(quantity=10)

        assign_resource_to_need(
            need_id=need["id"],
            resource_id=resource["id"],
            quantity_assigned=3,
        )

        updated_resource = get_resource(resource["id"])
        assert updated_resource["available_quantity"] == 7

    def test_assignment_sets_resource_status_to_asignado_when_fully_consumed(self):
        """Cuando se agota el recurso, su status cambia a 'asignado'."""
        need = _create_test_need()
        resource = _create_test_resource(quantity=5)

        assign_resource_to_need(
            need_id=need["id"],
            resource_id=resource["id"],
            quantity_assigned=5,
        )

        updated_resource = get_resource(resource["id"])
        assert updated_resource["available_quantity"] == 0
        assert updated_resource["status"] == "asignado"

    def test_assignment_updates_need_covered_quantity(self):
        """La asignación incrementa covered_quantity de la necesidad."""
        need = _create_test_need(quantity=50)
        resource = _create_test_resource(quantity=20)

        assign_resource_to_need(
            need_id=need["id"],
            resource_id=resource["id"],
            quantity_assigned=20,
        )

        updated_need = get_need(need["id"])
        assert updated_need["covered_quantity"] == 20

    def test_assignment_closes_need_when_fully_covered(self):
        """Si covered >= quantity, la necesidad se marca como cubierta."""
        need = _create_test_need(quantity=10)
        resource = _create_test_resource(quantity=10)

        assign_resource_to_need(
            need_id=need["id"],
            resource_id=resource["id"],
            quantity_assigned=10,
        )

        updated_need = get_need(need["id"])
        assert updated_need["estado"] == "cubierta"
        assert updated_need["covered_quantity"] == 10

    def test_multiple_assignments_accumulate_covered_quantity(self):
        """Múltiples asignaciones acumulan covered_quantity."""
        need = _create_test_need(quantity=50)
        resource1 = _create_test_resource(name="Recurso 1", quantity=20)
        resource2 = _create_test_resource(name="Recurso 2", quantity=20)

        assign_resource_to_need(
            need_id=need["id"],
            resource_id=resource1["id"],
            quantity_assigned=15,
        )
        assign_resource_to_need(
            need_id=need["id"],
            resource_id=resource2["id"],
            quantity_assigned=20,
        )

        updated_need = get_need(need["id"])
        assert updated_need["covered_quantity"] == 35


# --- Tests de errores ---

class TestAssignmentErrors:
    def test_rejects_assignment_to_closed_need(self):
        """No se puede asignar recursos a una necesidad cubierta."""
        from modules.necesidades.schemas import NeedStatus
        need = _create_test_need()
        resource = _create_test_resource()

        # Cerrar la necesidad
        from modules.necesidades.models import update_need_status
        update_need_status(need["id"], NeedStatus.COVERED)

        with pytest.raises(AssignmentValidationError, match="abiertas"):
            assign_resource_to_need(
                need_id=need["id"],
                resource_id=resource["id"],
                quantity_assigned=1,
            )

    def test_rejects_assignment_with_unavailable_resource(self):
        """No se puede asignar un recurso que no está disponible."""
        need = _create_test_need()
        resource = _create_test_resource()

        # Cambiar estado del recurso
        from modules.recursos.models import update_resource
        update_resource(resource["id"], status="en_mantenimiento")

        with pytest.raises(AssignmentValidationError, match="disponibles"):
            assign_resource_to_need(
                need_id=need["id"],
                resource_id=resource["id"],
                quantity_assigned=1,
            )

    def test_rejects_assignment_exceeding_available_quantity(self):
        """No se puede asignar más de lo disponible."""
        need = _create_test_need(quantity=100)
        resource = _create_test_resource(quantity=5)

        with pytest.raises(InsufficientQuantityError, match="5 disponibles"):
            assign_resource_to_need(
                need_id=need["id"],
                resource_id=resource["id"],
                quantity_assigned=10,
            )

    def test_rejects_assignment_to_nonexistent_need(self):
        """Error si la necesidad no existe."""
        resource = _create_test_resource()

        with pytest.raises(ValueError, match="no encontrada"):
            assign_resource_to_need(
                need_id=9999,
                resource_id=resource["id"],
                quantity_assigned=1,
            )

    def test_rejects_assignment_with_nonexistent_resource(self):
        """Error si el recurso no existe."""
        need = _create_test_need()

        with pytest.raises(ValueError, match="no encontrado"):
            assign_resource_to_need(
                need_id=need["id"],
                resource_id=9999,
                quantity_assigned=1,
            )


# --- Tests de transiciones de estado ---

class TestAssignmentTransitions:
    def test_transition_asignado_to_en_curso(self):
        """Transición válida: asignado -> en_curso."""
        need = _create_test_need()
        resource = _create_test_resource()
        assignment = assign_resource_to_need(
            need_id=need["id"],
            resource_id=resource["id"],
            quantity_assigned=5,
        )

        updated = transition_assignment_status(
            assignment_id=assignment["id"],
            new_status="en_curso",
        )

        assert updated["status"] == "en_curso"

    def test_transition_en_curso_to_completado(self):
        """Transición válida: en_curso -> completado."""
        need = _create_test_need()
        resource = _create_test_resource()
        assignment = assign_resource_to_need(
            need_id=need["id"],
            resource_id=resource["id"],
            quantity_assigned=5,
        )

        transition_assignment_status(assignment_id=assignment["id"], new_status="en_curso")
        completed = transition_assignment_status(
            assignment_id=assignment["id"],
            new_status="completado",
        )

        assert completed["status"] == "completado"

    def test_transition_asignado_to_cancelado(self):
        """Transición válida: asignado -> cancelado."""
        need = _create_test_need()
        resource = _create_test_resource()
        assignment = assign_resource_to_need(
            need_id=need["id"],
            resource_id=resource["id"],
            quantity_assigned=5,
        )

        cancelled = transition_assignment_status(
            assignment_id=assignment["id"],
            new_status="cancelado",
        )

        assert cancelled["status"] == "cancelado"

    def test_transition_en_curso_to_cancelado(self):
        """Transición válida: en_curso -> cancelado."""
        need = _create_test_need()
        resource = _create_test_resource()
        assignment = assign_resource_to_need(
            need_id=need["id"],
            resource_id=resource["id"],
            quantity_assigned=5,
        )

        transition_assignment_status(assignment_id=assignment["id"], new_status="en_curso")
        cancelled = transition_assignment_status(
            assignment_id=assignment["id"],
            new_status="cancelado",
        )

        assert cancelled["status"] == "cancelado"

    def test_rejects_invalid_transition_completado_to_anything(self):
        """No se puede cambiar desde completado."""
        need = _create_test_need()
        resource = _create_test_resource()
        assignment = assign_resource_to_need(
            need_id=need["id"],
            resource_id=resource["id"],
            quantity_assigned=5,
        )

        transition_assignment_status(assignment_id=assignment["id"], new_status="en_curso")
        transition_assignment_status(assignment_id=assignment["id"], new_status="completado")

        with pytest.raises(AssignmentValidationError, match="completado"):
            transition_assignment_status(
                assignment_id=assignment["id"],
                new_status="cancelado",
            )

    def test_rejects_invalid_transition_cancelado_to_anything(self):
        """No se puede cambiar desde cancelado."""
        need = _create_test_need()
        resource = _create_test_resource()
        assignment = assign_resource_to_need(
            need_id=need["id"],
            resource_id=resource["id"],
            quantity_assigned=5,
        )

        transition_assignment_status(assignment_id=assignment["id"], new_status="cancelado")

        with pytest.raises(AssignmentValidationError, match="cancelado"):
            transition_assignment_status(
                assignment_id=assignment["id"],
                new_status="en_curso",
            )

    def test_rejects_invalid_transition_completado_to_asignado(self):
        """No se puede reasignar desde completado."""
        need = _create_test_need()
        resource = _create_test_resource()
        assignment = assign_resource_to_need(
            need_id=need["id"],
            resource_id=resource["id"],
            quantity_assigned=5,
        )

        transition_assignment_status(assignment_id=assignment["id"], new_status="en_curso")
        transition_assignment_status(assignment_id=assignment["id"], new_status="completado")

        with pytest.raises(AssignmentValidationError):
            transition_assignment_status(
                assignment_id=assignment["id"],
                new_status="asignado",
            )


# --- Tests de restauración de disponibilidad ---

class TestResourceRestoration:
    def test_cancel_restores_resource_availability(self):
        """Cancelar una asignación restaura la disponibilidad del recurso."""
        need = _create_test_need(quantity=50)
        resource = _create_test_resource(quantity=10)

        assignment = assign_resource_to_need(
            need_id=need["id"],
            resource_id=resource["id"],
            quantity_assigned=5,
        )

        # Verificar decremento
        assert get_resource(resource["id"])["available_quantity"] == 5

        # Cancelar
        transition_assignment_status(
            assignment_id=assignment["id"],
            new_status="cancelado",
        )

        # Verificar restauración
        assert get_resource(resource["id"])["available_quantity"] == 10

    def test_complete_restores_resource_availability(self):
        """Completar una asignación restaura la disponibilidad del recurso."""
        need = _create_test_need(quantity=50)
        resource = _create_test_resource(quantity=10)

        assignment = assign_resource_to_need(
            need_id=need["id"],
            resource_id=resource["id"],
            quantity_assigned=5,
        )

        # Verificar decremento
        assert get_resource(resource["id"])["available_quantity"] == 5

        # Completar
        transition_assignment_status(assignment_id=assignment["id"], new_status="en_curso")
        transition_assignment_status(assignment_id=assignment["id"], new_status="completado")

        # Verificar restauración
        assert get_resource(resource["id"])["available_quantity"] == 10
        assert get_resource(resource["id"])["status"] == "disponible"


# --- Tests de listado ---

class TestAssignmentListing:
    def test_list_all_assignments(self):
        """Listar todas las asignaciones."""
        need = _create_test_need()
        resource = _create_test_resource()
        assign_resource_to_need(
            need_id=need["id"],
            resource_id=resource["id"],
            quantity_assigned=5,
        )

        all_assignments = list_assignments()
        assert len(all_assignments) >= 1

    def test_list_assignments_filtered_by_need(self):
        """Filtrar asignaciones por necesidad."""
        need1 = _create_test_need()
        need2 = _create_test_need()
        resource = _create_test_resource()

        assign_resource_to_need(need_id=need1["id"], resource_id=resource["id"], quantity_assigned=2)
        assign_resource_to_need(need_id=need2["id"], resource_id=resource["id"], quantity_assigned=3)

        filtered = list_assignments(need_id=need1["id"])
        assert len(filtered) == 1
        assert filtered[0]["need_id"] == need1["id"]

    def test_list_assignments_filtered_by_status(self):
        """Filtrar asignaciones por estado."""
        need = _create_test_need()
        resource = _create_test_resource()

        assignment = assign_resource_to_need(
            need_id=need["id"],
            resource_id=resource["id"],
            quantity_assigned=5,
        )
        transition_assignment_status(assignment_id=assignment["id"], new_status="en_curso")

        asignados = list_assignments(status="asignado")
        en_curso = list_assignments(status="en_curso")

        assert len(asignados) == 0
        assert len(en_curso) == 1

    def test_get_assignment_by_id(self):
        """Obtener una asignación por ID."""
        need = _create_test_need()
        resource = _create_test_resource()
        assignment = assign_resource_to_need(
            need_id=need["id"],
            resource_id=resource["id"],
            quantity_assigned=5,
        )

        fetched = get_assignment(assignment["id"])
        assert fetched is not None
        assert fetched["need_id"] == need["id"]

    def test_get_assignment_summary(self):
        """Obtener el resumen de asignaciones de una necesidad."""
        need = _create_test_need(quantity=50)
        resource1 = _create_test_resource(name="Recurso 1", quantity=10)
        resource2 = _create_test_resource(name="Recurso 2", quantity=15)

        assign_resource_to_need(need_id=need["id"], resource_id=resource1["id"], quantity_assigned=10)
        assign_resource_to_need(need_id=need["id"], resource_id=resource2["id"], quantity_assigned=15)

        summary = get_assignment_summary(need["id"])
        assert summary["total_assigned"] == 25
        assert summary["assignments_count"] == 2
        assert summary["by_status"]["asignado"] == 25


# --- Tests de Pydantic schemas ---

class TestAssignmentSchemas:
    def test_valid_assignment_create(self):
        """Schema válido se acepta."""
        schema = AssignmentCreate(need_id=1, resource_id=1, quantity_assigned=5)
        assert schema.need_id == 1
        assert schema.quantity_assigned == 5

    def test_rejects_zero_need_id(self):
        """Rechaza need_id <= 0."""
        with pytest.raises(Exception):
            AssignmentCreate(need_id=0, resource_id=1)

    def test_rejects_zero_resource_id(self):
        """Rechaza resource_id <= 0."""
        with pytest.raises(Exception):
            AssignmentCreate(need_id=1, resource_id=0)

    def test_rejects_zero_quantity(self):
        """Rechaza quantity_assigned <= 0."""
        with pytest.raises(Exception):
            AssignmentCreate(need_id=1, resource_id=1, quantity_assigned=0)

    def test_rejects_negative_quantity(self):
        """Rechaza quantity_assigned negativo."""
        with pytest.raises(Exception):
            AssignmentCreate(need_id=1, resource_id=1, quantity_assigned=-1)

    def test_default_quantity_is_one(self):
        """La cantidad por defecto es 1."""
        schema = AssignmentCreate(need_id=1, resource_id=1)
        assert schema.quantity_assigned == 1


# --- Tests de SQL injection ---

class TestSQLInjection:
    def test_notes_field_prevents_sql_injection(self):
        """El campo notes se parametriza correctamente."""
        need = _create_test_need()
        resource = _create_test_resource()

        assignment = assign_resource_to_need(
            need_id=need["id"],
            resource_id=resource["id"],
            quantity_assigned=5,
            notes="test'); DROP TABLE need_assignments; --",
        )

        fetched = get_assignment(assignment["id"])
        assert fetched["notes"] == "test'); DROP TABLE need_assignments; --"

        # Verificar que la tabla sigue existiendo
        all_assignments = list_assignments()
        assert len(all_assignments) >= 1
