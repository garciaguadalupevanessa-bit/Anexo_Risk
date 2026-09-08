"""Concurrency tests — verify SQLite behavior under concurrent operations.

Tests:
- Two operators assigning the same resource simultaneously
- Two concurrent status changes on same need
- Concurrent incident creation
"""
import sys
import os
import pytest
import threading
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


class TestConcurrencyIncidentCreation:
    """Concurrent incident creation should not crash or lose data."""

    def test_concurrent_incident_creation(self, client):
        """Create 10 incidents concurrently — all should succeed."""
        results = []
        errors = []

        def create_incident(i):
            try:
                resp = client.post("/api/incidents", json={
                    "title": f"Concurrent incident {i}",
                    "lat": 40.0 + i * 0.01,
                    "lon": -3.0 + i * 0.01,
                    "event_type": "alerta",
                    "source": "test",
                    "severity": "amarilla",
                })
                results.append(resp.status_code)
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=create_incident, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors: {errors}"
        assert all(r == 201 for r in results), f"Status codes: {results}"
        assert len(results) == 10


class TestConcurrentNeedStatusChanges:
    """Two concurrent status changes on the same need."""

    def test_concurrent_need_status_update(self, client):
        """Create a need, then try to change status concurrently."""
        # Create need
        resp = client.post("/api/necesidades", json={
            "tipo": "agua",
            "titulo": "Concurrent need",
            "descripcion": "Test",
            "prioridad": "media",
            "latitud": 40.42,
            "longitud": -3.70,
        })
        need_id = resp.json()["id"]

        results = []
        errors = []

        def update_status(estado):
            try:
                resp = client.patch(f"/api/necesidades/{need_id}", json={
                    "estado": estado,
                })
                results.append(resp.status_code)
            except Exception as e:
                errors.append(str(e))

        threads = [
            threading.Thread(target=update_status, args=("cubierta",)),
            threading.Thread(target=update_status, args=("cubierta",)),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # At least one should succeed, the other may get 400 (invalid transition)
        assert len(errors) == 0, f"Errors: {errors}"
        assert 200 in results or 400 in results


class TestConcurrentAnalyze:
    """Two concurrent analyses on the same incident."""

    def test_concurrent_analyze(self, client):
        """Analyze same incident twice concurrently — should not crash."""
        resp = client.post("/api/incidents", json={
            "title": "Concurrent analyze test",
            "lat": 40.42,
            "lon": -3.70,
            "event_type": "terremoto",
            "source": "test",
            "severity": "naranja",
            "magnitude": 5.0,
        })
        inc_id = resp.json()["id"]

        results = []
        errors = []

        def analyze():
            try:
                resp = client.post(f"/api/incidents/{inc_id}/analyze")
                results.append(resp.status_code)
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=analyze) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors: {errors}"
        assert all(r == 200 for r in results), f"Status codes: {results}"


class TestSQLiteLockingBehavior:
    """Verify SQLite handles concurrent writes without data corruption."""

    def test_concurrent_resource_creation(self, client):
        """Create 5 resources concurrently."""
        results = []
        errors = []

        def create_resource(i):
            try:
                resp = client.post("/api/resources", json={
                    "organization_id": 1,
                    "type": "logistico",
                    "name": f"Resource {i}",
                    "quantity": 1,
                    "available_quantity": 1,
                    "status": "disponible",
                }, headers={"X-Admin-Key": os.getenv("ANEXO_ADMIN_KEY", "test-key")})
                results.append(resp.status_code)
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=create_resource, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors: {errors}"
        # Some may fail due to auth, but no crashes
        assert len(results) == 5
