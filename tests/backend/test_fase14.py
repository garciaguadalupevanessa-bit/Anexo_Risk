"""Tests for FASE 14 — Live UX Dashboard.

Tests cover:
- Dashboard data aggregation
- Source health summary
- Node status summary
- Network status summary
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
os.environ.setdefault("TESTING", "true")
os.environ.setdefault("JWT_SECRET_KEY", "test-fase14")
os.environ.setdefault("ANEXO_ADMIN_KEY", "test-fase14")

from fastapi.testclient import TestClient
from main import app
from db.database import init_db

client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    yield


class TestLiveDashboard:
    def test_dashboard_returns_data(self):
        """Dashboard returns aggregated data."""
        resp = client.get("/api/live-dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert "timestamp" in data
        assert "active_incidents" in data
        assert "active_events" in data
        assert "source_health" in data
        assert "node_status" in data
        assert "network_status" in data
        assert "h3_coverage" in data

    def test_dashboard_source_health(self):
        """Source health has sources list."""
        resp = client.get("/api/live-dashboard")
        data = resp.json()
        assert "sources" in data["source_health"]
        assert "total_sources" in data["source_health"]

    def test_dashboard_node_status(self):
        """Node status has by_type and total."""
        resp = client.get("/api/live-dashboard")
        data = resp.json()
        assert "by_type" in data["node_status"]
        assert "total_nodes" in data["node_status"]

    def test_dashboard_network_status(self):
        """Network status has by_status and counts."""
        resp = client.get("/api/live-dashboard")
        data = resp.json()
        assert "by_status" in data["network_status"]
        assert "total_links" in data["network_status"]

    def test_dashboard_with_region(self):
        """Dashboard works with region filter."""
        resp = client.get("/api/live-dashboard?region_id=madrid")
        assert resp.status_code == 200
        assert resp.json()["region_id"] == "madrid"

    def test_dashboard_h3_coverage(self):
        """H3 coverage includes cells_with_data."""
        resp = client.get("/api/live-dashboard")
        data = resp.json()
        assert "cells_with_data" in data["h3_coverage"]
