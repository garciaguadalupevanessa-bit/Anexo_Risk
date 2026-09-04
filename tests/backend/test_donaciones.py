"""Pruebas pytest de las capas de persistencia, servicios y validación
del módulo de donaciones (schemas, modelos y rutas)."""
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from pydantic import ValidationError

from db import database
from modules.donaciones.models import (
    create_donation,
    get_donation,
    list_donations,
    update_status,
)
from modules.donaciones.schemas import (
    DonationCreate,
    DonationResponse,
    DonationResource,
    DonationStatus,
    DonationStatusUpdate,
    DonationType,
)


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


def build_valid_donation(**changes) -> DonationCreate:
    """Construye datos válidos y permite variar un campo en cada prueba."""

    payload = {
        "tipo": "recursos",
        "recurso": "Agua",
        "cantidad": "10 litros",
        "descripcion": "Agua potable para emergencia",
        "contacto": "Juan Perez",
        "dni": "12345678Z",
        "latitud": 39.4699,
        "longitud": -0.3763,
    }
    payload.update(changes)
    return DonationCreate(**payload)


# ── 1. Schema validation ───────────────────────────────────────────────


def test_donation_create_with_valid_data():
    """DonationCreate acepta datos completos y válidos."""

    donation = build_valid_donation()

    assert donation.donation_type == DonationType.RESOURCES
    assert donation.resource == DonationResource.WATER
    assert donation.quantity == "10 litros"
    assert donation.contact == "Juan Perez"
    assert donation.dni == "12345678Z"
    assert donation.latitud == 39.4699
    assert donation.longitud == -0.3763


def test_donation_create_missing_required_fields():
    """Rechaza la creación si faltan campos obligatorios (contacto)."""

    with pytest.raises(ValidationError):
        DonationCreate(
            tipo="recursos",
            recurso="Agua",
        )


def test_donation_create_invalid_types():
    """Rechaza valores que no coinciden con los enums."""

    with pytest.raises(ValidationError):
        DonationCreate(
            tipo="invalido",
            recurso="Agua",
            contacto="Juan",
        )

    with pytest.raises(ValidationError):
        DonationCreate(
            tipo="recursos",
            recurso="invalido",
            contacto="Juan",
        )


def test_donation_create_extra_fields_are_forbidden():
    """El modelo no acepta campos inesperados."""

    with pytest.raises(ValidationError):
        DonationCreate(
            tipo="recursos",
            recurso="Agua",
            contacto="Juan",
            campo_extra="no permitido",
        )


# ── 2. Coordinate validation ──────────────────────────────────────────


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("latitud", 90.1),
        ("latitud", -90.1),
        ("longitud", 180.1),
        ("longitud", -180.1),
    ],
)
def test_coordinates_out_of_range_are_rejected(field, value):
    """Latitud y longitud deben respetar sus rangos geográficos."""

    with pytest.raises(ValidationError):
        build_valid_donation(**{field: value})


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("latitud", float("nan")),
        ("latitud", float("inf")),
        ("latitud", float("-inf")),
        ("longitud", float("nan")),
        ("longitud", float("inf")),
        ("longitud", float("-inf")),
    ],
)
def test_coordinates_reject_nan_and_inf(field, value):
    """allow_inf_nan=False impide NaN e Infinito."""

    with pytest.raises(ValidationError):
        build_valid_donation(**{field: value})


def test_boundary_coordinates_are_accepted():
    """Los valores extremospermitidos (±90, ±180) se aceptan."""

    donation = build_valid_donation(latitud=90.0, longitud=180.0)
    assert donation.latitud == 90.0
    assert donation.longitud == 180.0

    donation = build_valid_donation(latitud=-90.0, longitud=-180.0)
    assert donation.latitud == -90.0
    assert donation.longitud == -180.0


# ── 3. Create donation ────────────────────────────────────────────────


def test_create_donation_persists_record():
    """La creación devuelve una fila completa recuperable por su id."""

    donation = build_valid_donation()
    created = create_donation(donation)

    assert created["id"] > 0
    assert created["tipo"] == "ofrecida"
    assert created["recurso"] == "Agua"
    assert created["cantidad"] == "10 litros"
    assert created["descripcion"] == "Agua potable para emergencia"
    assert created["contacto"] == "Juan Perez"
    assert created["dni"] == "12345678Z"
    assert created["estado"] == "activa"

    retrieved = get_donation(created["id"])
    assert retrieved == created


# ── 4. List donations ─────────────────────────────────────────────────


def test_list_donations_returns_all():
    """GET /api/donaciones devuelve la lista de donaciones registradas."""

    create_donation(build_valid_donation())
    create_donation(
        build_valid_donation(
            recurso="Mantas",
            descripcion="Mantas para refugiados",
        )
    )

    donations = list_donations()

    assert len(donations) == 2
    assert all(isinstance(d["id"], int) for d in donations)


def test_list_donations_filters_by_type():
    """El filtro por tipo devuelve solo las donaciones coincidentes."""

    create_donation(build_valid_donation(tipo="recursos"))
    create_donation(
        build_valid_donation(
            tipo="servicios",
            recurso="Transporte",
            contacto="Maria Lopez",
        )
    )

    resources = list_donations(donation_type=DonationType.RESOURCES)
    services = list_donations(donation_type=DonationType.SERVICES)

    assert len(resources) == 1
    assert resources[0]["tipo"] == "ofrecida"
    assert len(services) == 1
    assert services[0]["tipo"] == "ofrecida"


# ── 5. Get donation by ID ─────────────────────────────────────────────


def test_get_donation_by_id():
    """GET /api/donaciones/{id} devuelve la donación correcta."""

    created = create_donation(build_valid_donation())
    retrieved = get_donation(created["id"])

    assert retrieved is not None
    assert retrieved["id"] == created["id"]
    assert retrieved["contacto"] == "Juan Perez"


def test_get_donation_nonexistent_returns_none():
    """Una donación inexistente devuelve None."""

    assert get_donation(999) is None


# ── 6. Update donation status ─────────────────────────────────────────


def test_update_donation_status_to_delivered():
    """PATCH /api/donaciones/{id}/estado actualiza el estado."""

    created = create_donation(build_valid_donation())
    updated = update_status(created["id"], DonationStatus.DELIVERED)

    assert updated is not None
    assert updated["estado"] == "entregada"


def test_update_donation_status_nonexistent_returns_none():
    """Actualizar una donación inexistente devuelve None."""

    result = update_status(999, DonationStatus.DELIVERED)
    assert result is None


def test_donation_status_update_schema_rejects_invalid_status():
    """DonationStatusUpdate rechaza estados no válidos."""

    with pytest.raises(ValidationError):
        DonationStatusUpdate(estado="cancelada")

    with pytest.raises(ValidationError):
        DonationStatusUpdate(estado="pendiente")


# ── 7. Donation with coordinates ──────────────────────────────────────


def test_donation_stores_coordinates_correctamente():
    """Las coordenadas se guardan y recuperan con precisión."""

    donation = build_valid_donation(latitud=37.3891, longitud=-5.9845)
    created = create_donation(donation)

    assert created["latitud"] == pytest.approx(37.3891)
    assert created["longitud"] == pytest.approx(-5.9845)

    retrieved = get_donation(created["id"])
    assert retrieved["latitud"] == pytest.approx(37.3891)
    assert retrieved["longitud"] == pytest.approx(-5.9845)


# ── 8. Donation without coordinates ───────────────────────────────────


def test_donation_without_coordinates():
    """Las coordenadas son opcionales; si se omiten son None."""

    donation = DonationCreate(
        tipo="recursos",
        recurso="Mantas",
        cantidad="5",
        descripcion="Mantas para familias",
        contacto="Ana Garcia",
    )

    assert donation.latitud is None
    assert donation.longitud is None

    created = create_donation(donation)

    assert created["latitud"] is None
    assert created["longitud"] is None


# ── Edge cases ────────────────────────────────────────────────────────


def test_donation_text_is_normalized():
    """El contacto se limpia de espacios extraños al inicio/fin."""

    donation = build_valid_donation(contacto="  Juan Perez  ")
    created = create_donation(donation)

    assert created["contacto"] == "Juan Perez"


def test_donation_with_empty_optional_fields():
    """quantity y description pueden ser cadenas vacías por defecto."""

    donation = DonationCreate(
        tipo="recursos",
        recurso="Agua",
        contacto="Carlos Ruiz",
    )

    assert donation.quantity == ""
    assert donation.description == ""

    created = create_donation(donation)
    assert created["cantidad"] == ""
    assert created["descripcion"] == ""


def test_donation_dni_optional_for_non_time_type():
    """El DNI es opcional cuando el tipo no es 'tiempo'."""

    donation = build_valid_donation(dni=None)
    assert donation.dni is None

    created = create_donation(donation)
    assert created["dni"] is None


def test_donation_time_type_requires_dni():
    """El tipo 'tiempo' exige un DNI obligatorio."""

    with pytest.raises(ValidationError):
        DonationCreate(
            tipo="tiempo",
            recurso="Transporte",
            contacto="Maria Lopez",
            dni=None,
        )


def test_models_use_parameterized_queries():
    """El contenido similar a SQL se guarda literalmente sin alterar la tabla."""

    description = "Agua'); DROP TABLE donaciones; --"
    created = create_donation(build_valid_donation(descripcion=description))

    assert created["descripcion"] == description
    with database.get_cursor() as cursor:
        total = cursor.execute("SELECT COUNT(*) FROM donaciones").fetchone()[0]
    assert total == 1


def test_donation_response_matches_json_contract():
    """El contrato JSON conserva los nombres en español."""

    created = create_donation(build_valid_donation())

    response = DonationResponse.model_validate(created).model_dump(
        mode="json",
        by_alias=True,
    )

    assert isinstance(response["id"], int)
    assert response["tipo"] == "ofrecida"
    assert response["recurso"] == "Agua"
    assert response["estado"] == "activa"
    assert "creado_en" in response
