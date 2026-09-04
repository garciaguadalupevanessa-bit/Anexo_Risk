"""Pruebas pytest del módulo de voluntariado: schemas, models, services y routes."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from db import database
from modules.voluntariado import models, services
from modules.voluntariado.models import InvalidVolunteerTransition
from modules.voluntariado.schemas import (
    VolunteerActionResponse,
    VolunteerCreate,
    VolunteerFrontendCreate,
    VolunteerFrontendResponse,
    VolunteerFrontendRegistrationResponse,
    VolunteerStatus,
    _validate_dni,
)

# ---------------------------------------------------------------------------
# Fixture de base de datos temporal
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def temporary_database():
    """Crea una base de datos SQLite aislada para cada prueba."""
    previous_path = database.DATABASE_PATH
    with TemporaryDirectory() as temp_directory:
        database.DATABASE_PATH = str(Path(temp_directory) / "nexo_test.db")
        database.init_db()
        models._schema_ready = False
        try:
            yield
        finally:
            database.DATABASE_PATH = previous_path
            models._schema_ready = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def build_valid_volunteer_create(**changes) -> VolunteerCreate:
    payload = {
        "nombre": "María García López",
        "contacto": "maria@example.com",
        "habilidades": "Primeros auxilios, conducción",
        "disponibilidad": "inmediata",
    }
    payload.update(changes)
    return VolunteerCreate(**payload)


def build_valid_frontend_create(**changes) -> VolunteerFrontendCreate:
    payload = {
        "first_name": "María",
        "last_name": "García López",
        "dni": "12345678Z",
        "birth_date": "1990-05-15",
        "phone": "612345678",
        "locality": "Valencia",
        "tasks": ["donation_sorting"],
        "transportation": "needs_transport",
    }
    payload.update(changes)
    return VolunteerFrontendCreate(**payload)


def create_pending_volunteer(**overrides) -> dict:
    """Inserta un voluntario pendiente directamente en la BD."""
    defaults = {
        "name": "María García López",
        "contact": "maria@example.com",
        "skills": "Primeros auxilios",
        "availability": "inmediata",
        "admin_token": "test_admin_token_abc",
        "volunteer_token": "test_volunteer_token_xyz",
    }
    defaults.update(overrides)
    return models.create_volunteer_pending(**defaults)


def approve_and_get(id_: int) -> dict:
    return services.approve_volunteer(id_, via_api=True)


# ---------------------------------------------------------------------------
# 1. Schema validation — VolunteerCreate
# ---------------------------------------------------------------------------

class TestVolunteerCreateSchema:
    def test_valid_create(self):
        v = build_valid_volunteer_create()
        assert v.name == "María García López"
        assert v.contact == "maria@example.com"

    def test_strips_whitespace(self):
        v = build_valid_volunteer_create(nombre="  Pedro  Ruiz  ")
        assert v.name == "Pedro  Ruiz"

    @pytest.mark.parametrize(
        "field",
        ["nombre", "contacto", "habilidades"],
    )
    def test_missing_required_fields(self, field):
        with pytest.raises(ValidationError):
            build_valid_volunteer_create(**{field: ""})

    def test_rejects_extra_fields(self):
        with pytest.raises(ValidationError):
            VolunteerCreate(
                nombre="Ana",
                contacto="ana@test.com",
                habilidades="cargar",
                campo_extra="no",
            )


# ---------------------------------------------------------------------------
# 2. Schema validation — VolunteerFrontendCreate
# ---------------------------------------------------------------------------

class TestVolunteerFrontendCreateSchema:
    def test_valid_frontend_create(self):
        v = build_valid_frontend_create()
        assert v.first_name == "María"
        assert v.last_name == "García López"
        assert v.tasks[0].value == "donation_sorting"

    def test_dni_normalized_uppercase(self):
        v = build_valid_frontend_create(dni="12345678z")
        assert v.dni == "12345678Z"

    def test_rejects_future_birth_date(self):
        with pytest.raises(ValidationError):
            build_valid_frontend_create(birth_date="2099-01-01")

    def test_vehicle_type_required_with_own_vehicle(self):
        with pytest.raises(ValidationError):
            build_valid_frontend_create(
                transportation="own_vehicle",
                vehicle_type=None,
            )

    def test_vehicle_type_set_with_own_vehicle(self):
        v = build_valid_frontend_create(
            transportation="own_vehicle",
            vehicle_type="car",
        )
        assert v.vehicle_type.value == "car"

    def test_vehicle_type_none_with_needs_transport(self):
        v = build_valid_frontend_create(
            transportation="needs_transport",
            vehicle_type="car",
        )
        assert v.vehicle_type is None

    def test_tasks_must_be_nonempty(self):
        with pytest.raises(ValidationError):
            build_valid_frontend_create(tasks=[])

    def test_rejects_extra_fields(self):
        with pytest.raises(ValidationError):
            build_valid_frontend_create(hack="yes")

    def test_strips_whitespace(self):
        v = build_valid_frontend_create(
            first_name="  Ana  ",
            locality="  Madrid  ",
        )
        assert v.first_name == "Ana"
        assert v.locality == "Madrid"

    @pytest.mark.parametrize(
        "field",
        ["first_name", "last_name", "phone", "locality"],
    )
    def test_min_length_rejected(self, field):
        with pytest.raises(ValidationError):
            build_valid_frontend_create(**{field: "a"})


# ---------------------------------------------------------------------------
# 3. DNI validation
# ---------------------------------------------------------------------------

class TestDNIValidation:
    def test_valid_dni(self):
        assert _validate_dni("12345678Z") == "12345678Z"

    def test_valid_dni_lowercase(self):
        assert _validate_dni("12345678z") == "12345678Z"

    def test_wrong_control_letter(self):
        with pytest.raises(ValueError, match="letra de control"):
            _validate_dni("12345678A")

    def test_too_short(self):
        with pytest.raises(ValueError, match="8 números"):
            _validate_dni("1234567Z")

    def test_too_long(self):
        with pytest.raises(ValueError, match="8 números"):
            _validate_dni("123456789Z")

    def test_letters_in_number_part(self):
        with pytest.raises(ValueError, match="8 números"):
            _validate_dni("12345ABZ")

    def test_no_letter(self):
        with pytest.raises(ValueError, match="8 números"):
            _validate_dni("12345678")

    @pytest.mark.parametrize(
        "dni",
        ["00000000T", "99999999R", "12345678Z"],
    )
    def test_various_valid_dnis(self, dni):
        result = _validate_dni(dni)
        assert len(result) == 9


# ---------------------------------------------------------------------------
# 4. Token generation
# ---------------------------------------------------------------------------

class TestTokenGeneration:
    def test_tokens_are_unique(self):
        import secrets
        t1 = secrets.token_urlsafe(32)
        t2 = secrets.token_urlsafe(32)
        assert t1 != t2

    def test_pending_volunteer_stores_tokens(self):
        v = create_pending_volunteer(
            admin_token="admin_tok_123",
            volunteer_token="vol_tok_456",
        )
        # The raw DB row (not public) contains tokens
        raw = models.get_volunteer(v["id"])
        assert raw["admin_token"] == "admin_tok_123"
        assert raw["volunteer_token"] == "vol_tok_456"

    def test_public_row_strips_tokens(self):
        v = create_pending_volunteer()
        public = models._public_volunteer_row(v)
        assert "admin_token" not in public
        assert "volunteer_token" not in public


# ---------------------------------------------------------------------------
# 5. Create volunteer — registration flow
# ---------------------------------------------------------------------------

class TestCreateVolunteer:
    @patch("modules.voluntariado.email_service.send_admin_new_volunteer_email")
    def test_register_legacy_creates_pending(self, mock_email):
        data = build_valid_volunteer_create()
        result = services.register_volunteer(data, documents=[])
        assert result["estado"] == "pendiente"
        assert result["nombre"] == "María García López"
        mock_email.assert_called_once()

    def test_register_frontend_creates_pending(self):
        data = build_valid_frontend_create()
        with patch("modules.voluntariado.email_service.send_admin_new_volunteer_email"):
            result = services.register_volunteer_from_frontend(data)
        assert result["first_name"] == "María"
        assert result["dni"] == "12345678Z"
        assert result["phone"] == "612345678"
        assert result["status"] == "available"
        # Verify the raw DB row is indeed pending
        raw = models.get_volunteer(result["id"])
        assert raw["estado"] == "pendiente"

    def test_create_via_models_directly(self):
        v = create_pending_volunteer()
        assert v["id"] > 0
        assert v["estado"] == "pendiente"
        assert v["disponible"] == 0

    def test_full_name_correctly_joined(self):
        data = build_valid_frontend_create(first_name="Carlos", last_name="Ruiz")
        with patch("modules.voluntariado.email_service.send_admin_new_volunteer_email"):
            result = services.register_volunteer_from_frontend(data)
        assert result["full_name"] == "Carlos Ruiz"

    def test_dni_stored_normalized(self):
        data = build_valid_frontend_create(dni="87654321x")
        with patch("modules.voluntariado.email_service.send_admin_new_volunteer_email"):
            result = services.register_volunteer_from_frontend(data)
        assert result["dni"] == "87654321X"

    def test_tasks_json_stored(self):
        data = build_valid_frontend_create(
            tasks=["donation_sorting", "supply_distribution"],
        )
        with patch("modules.voluntariado.email_service.send_admin_new_volunteer_email"):
            result = services.register_volunteer_from_frontend(data)
        stored = models.get_volunteer(result["id"])
        import json
        tasks = json.loads(stored["tasks"])
        assert "donation_sorting" in tasks
        assert "supply_distribution" in tasks

    def test_availability_slots_stored(self):
        from datetime import datetime, timezone
        data = build_valid_frontend_create(
            availability_slots=[{"starts_at": "2099-12-01T10:00:00"}],
        )
        with patch("modules.voluntariado.email_service.send_admin_new_volunteer_email"):
            result = services.register_volunteer_from_frontend(data)
        stored = models.get_volunteer(result["id"])
        import json
        slots = json.loads(stored["availability_slots"])
        assert len(slots) == 1
        assert slots[0]["starts_at"] == "2099-12-01T10:00:00"


# ---------------------------------------------------------------------------
# 6. List volunteers — GET /api/voluntarios
# ---------------------------------------------------------------------------

class TestListVolunteers:
    def test_list_empty_when_no_approved(self):
        create_pending_volunteer()
        result = models.list_volunteers()
        assert result == []

    def test_list_approved_only(self):
        v = create_pending_volunteer()
        approve_and_get(v["id"])
        result = models.list_volunteers()
        assert len(result) == 1
        assert result[0]["id"] == v["id"]

    def test_list_excludes_pending(self):
        create_pending_volunteer()
        create_pending_volunteer(name="Otro", contact="otro@test.com")
        assert models.list_volunteers() == []

    def test_list_excludes_rejected(self):
        v = create_pending_volunteer()
        services.reject_volunteer(v["id"], via_api=True)
        assert models.list_volunteers() == []

    def test_list_filters_by_skill(self):
        v1 = create_pending_volunteer(skills="conducción")
        v2 = create_pending_volunteer(name="B", contact="b@t.com", skills="cocina")
        approve_and_get(v1["id"])
        approve_and_get(v2["id"])

        result = models.list_volunteers(skill="conducción")
        assert len(result) == 1
        assert result[0]["habilidades"] == "conducción"

    def test_list_filters_by_availability(self):
        v1 = create_pending_volunteer()
        v2 = create_pending_volunteer(name="B", contact="b@t.com")
        approve_and_get(v1["id"])
        approve_and_get(v2["id"])
        models.update_volunteer_availability(v2["id"], is_available=False)

        result = models.list_volunteers(is_available=True)
        assert len(result) == 1
        assert result[0]["disponible"] is True

    def test_list_for_frontend(self):
        v = create_pending_volunteer()
        approve_and_get(v["id"])
        result = models.list_volunteers_for_frontend()
        assert len(result) == 1
        assert "full_name" in result[0]
        assert "status" in result[0]

    def test_list_for_frontend_filters_by_coordination_status(self):
        v = create_pending_volunteer()
        approve_and_get(v["id"])

        result = models.list_volunteers_for_frontend(coordination_status="available")
        assert len(result) == 1

        result = models.list_volunteers_for_frontend(coordination_status="resting")
        assert len(result) == 0


# ---------------------------------------------------------------------------
# 7. List pending — GET /api/voluntarios/pendientes
# ---------------------------------------------------------------------------

class TestListPending:
    def test_list_pending_empty(self):
        assert models.list_pending_volunteers() == []

    def test_list_pending_shows_unapproved(self):
        v = create_pending_volunteer()
        pending = models.list_pending_volunteers()
        assert len(pending) == 1
        assert pending[0]["id"] == v["id"]

    def test_list_pending_excludes_approved(self):
        v = create_pending_volunteer()
        approve_and_get(v["id"])
        assert models.list_pending_volunteers() == []

    def test_list_pending_excludes_rejected(self):
        v = create_pending_volunteer()
        services.reject_volunteer(v["id"], via_api=True)
        assert models.list_pending_volunteers() == []

    def test_list_pending_includes_documents(self):
        v = create_pending_volunteer()
        pending = models.list_pending_volunteers()
        assert "admin_token" not in pending[0]
        assert "volunteer_token" not in pending[0]


# ---------------------------------------------------------------------------
# 8. Approve volunteer — POST /api/voluntarios/{id}/aprobar
# ---------------------------------------------------------------------------

class TestApproveVolunteer:
    def test_approve_pending(self):
        v = create_pending_volunteer()
        result = approve_and_get(v["id"])
        assert result["estado"] == "aprobado"
        assert result["mensaje"] == "Voluntario aprobado correctamente."

    def test_approve_sets_available(self):
        v = create_pending_volunteer()
        approve_and_get(v["id"])
        updated = models.get_volunteer(v["id"])
        assert updated["disponible"] == 1

    def test_approve_clears_admin_token(self):
        v = create_pending_volunteer()
        approve_and_get(v["id"])
        updated = models.get_volunteer(v["id"])
        assert updated["admin_token"] == ""

    def test_approve_with_valid_token(self):
        v = create_pending_volunteer(admin_token="secret123")
        result = services.approve_volunteer(
            v["id"], admin_token="secret123", via_api=False
        )
        assert result["estado"] == "aprobado"

    def test_approve_with_wrong_token(self):
        v = create_pending_volunteer(admin_token="secret123")
        result = services.approve_volunteer(
            v["id"], admin_token="wrong", via_api=False
        )
        assert result.get("error") == "not_found"

    def test_approve_nonexistent(self):
        result = services.approve_volunteer(9999, via_api=True)
        assert result.get("error") == "not_found"

    @patch("modules.voluntariado.email_service.send_volunteer_approved_email")
    def test_approve_sends_email(self, mock_email):
        v = create_pending_volunteer()
        approve_and_get(v["id"])
        mock_email.assert_called_once()

    def test_approve_sets_coordination_available(self):
        v = create_pending_volunteer()
        approve_and_get(v["id"])
        updated = models.get_volunteer(v["id"])
        assert updated["coordination_status"] == "available"


# ---------------------------------------------------------------------------
# 9. Reject volunteer — POST /api/voluntarios/{id}/rechazar
# ---------------------------------------------------------------------------

class TestRejectVolunteer:
    def test_reject_pending(self):
        v = create_pending_volunteer()
        result = services.reject_volunteer(v["id"], via_api=True)
        assert result["estado"] == "rechazado"
        assert result["mensaje"] == "Solicitud de voluntariado rechazada."

    def test_reject_sets_unavailable(self):
        v = create_pending_volunteer()
        services.reject_volunteer(v["id"], via_api=True)
        updated = models.get_volunteer(v["id"])
        assert updated["disponible"] == 0

    def test_reject_clears_admin_token(self):
        v = create_pending_volunteer()
        services.reject_volunteer(v["id"], via_api=True)
        updated = models.get_volunteer(v["id"])
        assert updated["admin_token"] == ""

    def test_reject_with_valid_token(self):
        v = create_pending_volunteer(admin_token="tok_reject")
        result = services.reject_volunteer(
            v["id"], admin_token="tok_reject", via_api=False
        )
        assert result["estado"] == "rechazado"

    def test_reject_with_wrong_token(self):
        v = create_pending_volunteer(admin_token="tok_reject")
        result = services.reject_volunteer(
            v["id"], admin_token="wrong", via_api=False
        )
        assert result.get("error") == "not_found"

    def test_reject_nonexistent(self):
        result = services.reject_volunteer(9999, via_api=True)
        assert result.get("error") == "not_found"

    @patch("modules.voluntariado.email_service.send_volunteer_rejected_email")
    def test_reject_sends_email(self, mock_email):
        v = create_pending_volunteer()
        services.reject_volunteer(v["id"], via_api=True)
        mock_email.assert_called_once()


# ---------------------------------------------------------------------------
# 10. Status transitions — valid and invalid
# ---------------------------------------------------------------------------

class TestStatusTransitions:
    def test_approve_pending_succeeds(self):
        v = create_pending_volunteer()
        result = approve_and_get(v["id"])
        assert result["estado"] == "aprobado"

    def test_reject_pending_succeeds(self):
        v = create_pending_volunteer()
        result = services.reject_volunteer(v["id"], via_api=True)
        assert result["estado"] == "rechazado"

    def test_approve_already_approved_fails(self):
        v = create_pending_volunteer()
        approve_and_get(v["id"])
        result = services.approve_volunteer(v["id"], via_api=True)
        assert result.get("error") == "invalid_transition"

    def test_reject_already_approved_fails(self):
        v = create_pending_volunteer()
        approve_and_get(v["id"])
        result = services.reject_volunteer(v["id"], via_api=True)
        assert result.get("error") == "invalid_transition"

    def test_approve_already_rejected_fails(self):
        v = create_pending_volunteer()
        services.reject_volunteer(v["id"], via_api=True)
        result = services.approve_volunteer(v["id"], via_api=True)
        assert result.get("error") == "invalid_transition"

    def test_reject_already_rejected_fails(self):
        v = create_pending_volunteer()
        services.reject_volunteer(v["id"], via_api=True)
        result = services.reject_volunteer(v["id"], via_api=True)
        assert result.get("error") == "invalid_transition"

    def test_invalid_transition_raises_in_models(self):
        v = create_pending_volunteer()
        approve_and_get(v["id"])
        with pytest.raises(InvalidVolunteerTransition):
            models.approve_volunteer_record(v["id"])

    def test_invalid_transition_reject_raises_in_models(self):
        v = create_pending_volunteer()
        approve_and_get(v["id"])
        with pytest.raises(InvalidVolunteerTransition):
            models.reject_volunteer_record(v["id"])

    def test_invalid_transition_availability_update(self):
        v = create_pending_volunteer()
        with pytest.raises(InvalidVolunteerTransition):
            models.update_volunteer_availability(v["id"], is_available=True)

    def test_invalid_transition_coordination_update(self):
        v = create_pending_volunteer()
        with pytest.raises(InvalidVolunteerTransition):
            models.update_coordination_status(v["id"], "assigned")


# ---------------------------------------------------------------------------
# 11. Coordination status updates
# ---------------------------------------------------------------------------

class TestCoordinationStatus:
    def test_update_to_assigned(self):
        v = create_pending_volunteer()
        approve_and_get(v["id"])
        result = models.update_coordination_status(v["id"], "assigned")
        assert result["status"] == "assigned"

    def test_update_to_resting(self):
        v = create_pending_volunteer()
        approve_and_get(v["id"])
        result = models.update_coordination_status(v["id"], "resting")
        assert result["status"] == "resting"
        volunteer = models.get_volunteer(v["id"])
        assert volunteer["disponible"] == 0

    def test_update_to_available(self):
        v = create_pending_volunteer()
        approve_and_get(v["id"])
        models.update_coordination_status(v["id"], "resting")
        result = models.update_coordination_status(v["id"], "available")
        assert result["status"] == "available"
        volunteer = models.get_volunteer(v["id"])
        assert volunteer["disponible"] == 1

    def test_reject_pending_fails_coordination_update(self):
        v = create_pending_volunteer()
        with pytest.raises(InvalidVolunteerTransition):
            models.update_coordination_status(v["id"], "assigned")

    def test_nonexistent_volunteer_returns_none(self):
        result = models.update_coordination_status(9999, "available")
        assert result is None


# ---------------------------------------------------------------------------
# 12. Availability update
# ---------------------------------------------------------------------------

class TestAvailabilityUpdate:
    def test_toggle_availability(self):
        v = create_pending_volunteer()
        approve_and_get(v["id"])
        updated = models.update_volunteer_availability(v["id"], is_available=False)
        assert updated["disponible"] is False

    def test_availability_via_service_with_token(self):
        v = create_pending_volunteer(volunteer_token="vol_tok")
        approve_and_get(v["id"])
        result = services.update_availability(
            v["id"], is_available=False, volunteer_token="vol_tok"
        )
        assert result["disponible"] is False

    def test_availability_wrong_token_returns_none(self):
        v = create_pending_volunteer(volunteer_token="vol_tok")
        approve_and_get(v["id"])
        result = services.update_availability(
            v["id"], is_available=False, volunteer_token="wrong"
        )
        assert result is None

    def test_availability_pending_volunteer_fails(self):
        v = create_pending_volunteer()
        with pytest.raises(InvalidVolunteerTransition):
            models.update_volunteer_availability(v["id"], is_available=True)

    def test_availability_nonexistent_returns_none(self):
        result = models.update_volunteer_availability(9999, is_available=True)
        assert result is None


# ---------------------------------------------------------------------------
# 13. Edge cases and security
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_sql_injection_in_name(self):
        malicious = "Robert'); DROP TABLE voluntarios; --"
        v = create_pending_volunteer(name=malicious)
        assert v["nombre"] == malicious
        with database.get_cursor() as cursor:
            total = cursor.execute("SELECT COUNT(*) FROM voluntarios").fetchone()[0]
        assert total == 1

    def test_single_word_name_splits_correctly(self):
        v = create_pending_volunteer(name="SoloNombre")
        first, last = models._split_legacy_name("SoloNombre")
        assert first == "SoloNombre"
        assert last == ""

    def test_empty_name_splits(self):
        first, last = models._split_legacy_name("")
        assert first == ""
        assert last == ""

    def test_whitespace_name_splits(self):
        first, last = models._split_legacy_name("   ")
        assert first == ""
        assert last == ""

    def test_json_list_loads_none(self):
        assert models._loads_json_list(None) == []

    def test_json_list_loads_empty_string(self):
        assert models._loads_json_list("") == []

    def test_json_list_loads_invalid_json(self):
        assert models._loads_json_list("not json") == []

    def test_json_list_loads_non_list(self):
        assert models._loads_json_list(42) == []

    def test_json_list_loads_valid_list(self):
        assert models._loads_json_list(["a", "b"]) == ["a", "b"]

    def test_response_model_validates(self):
        v = create_pending_volunteer()
        approve_and_get(v["id"])
        approved = models.get_volunteer(v["id"])
        public = models._public_volunteer_row(approved)
        resp = VolunteerActionResponse(
            id=public["id"],
            estado=public["estado"],
            mensaje="test",
        )
        assert resp.id > 0


# ---------------------------------------------------------------------------
# 14. Enum coverage
# ---------------------------------------------------------------------------

class TestEnums:
    def test_volunteer_status_values(self):
        assert VolunteerStatus.PENDING.value == "pendiente"
        assert VolunteerStatus.APPROVED.value == "aprobado"
        assert VolunteerStatus.REJECTED.value == "rechazado"

    def test_all_tasks_valid(self):
        from modules.voluntariado.schemas import VolunteerTask
        for task in VolunteerTask:
            assert isinstance(task.value, str)

    def test_all_certifications_valid(self):
        from modules.voluntariado.schemas import VolunteerCertification
        for cert in VolunteerCertification:
            assert isinstance(cert.value, str)

    def test_transportation_types(self):
        from modules.voluntariado.schemas import TransportationType
        assert TransportationType.OWN_VEHICLE.value == "own_vehicle"
        assert TransportationType.NEEDS_TRANSPORT.value == "needs_transport"

    def test_vehicle_types(self):
        from modules.voluntariado.schemas import VehicleType
        assert VehicleType.CAR.value == "car"
        assert VehicleType.VAN.value == "van"
        assert VehicleType.FOUR_BY_FOUR.value == "four_by_four"

    def test_coordination_statuses(self):
        from modules.voluntariado.schemas import CoordinationStatus
        assert CoordinationStatus.AVAILABLE.value == "available"
        assert CoordinationStatus.ASSIGNED.value == "assigned"
        assert CoordinationStatus.RESTING.value == "resting"
