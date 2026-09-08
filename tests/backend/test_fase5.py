"""Tests for FASE 5 — Near-Real-Time Engine."""
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
os.environ.setdefault("TESTING", "true")
os.environ.setdefault("JWT_SECRET_KEY", "test-fase5")
os.environ.setdefault("ANEXO_ADMIN_KEY", "test-fase5")

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app, raise_server_exceptions=False)


class TestCircuitBreaker:
    """Test circuit breaker logic."""

    def test_closed_by_default(self):
        from services.live_ingestion import CircuitBreaker
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60)
        assert cb.get_state("test") == "closed"

    def test_opens_after_threshold(self):
        from services.live_ingestion import CircuitBreaker
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60)
        for _ in range(3):
            cb.record_failure("test")
        assert cb.get_state("test") == "open"

    def test_resets_on_success(self):
        from services.live_ingestion import CircuitBreaker
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60)
        cb.record_failure("test")
        cb.record_failure("test")
        cb.record_success("test")
        assert cb.get_state("test") == "closed"

    def test_half_open_after_recovery(self):
        from services.live_ingestion import CircuitBreaker
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)
        cb.record_failure("test")
        cb.record_failure("test")
        assert cb.is_open("test") is True
        time.sleep(0.2)
        assert cb.is_open("test") is False
        assert cb.get_state("test") == "half-open"


class TestSourceHealth:
    """Test source health tracking."""

    def test_record_success(self):
        from services.source_health import SourceHealthTracker
        tracker = SourceHealthTracker()
        tracker.record_attempt("test_src", True, latency_ms=150.0)
        h = tracker.get_health("test_src")
        assert h["status"] == "active"
        assert h["success_count"] == 1
        assert h["error_count"] == 0

    def test_record_failure(self):
        from services.source_health import SourceHealthTracker
        tracker = SourceHealthTracker()
        tracker.record_attempt("test_src", False, error="timeout")
        h = tracker.get_health("test_src")
        assert h["error_count"] == 1

    def test_degraded_after_multiple_failures(self):
        from services.source_health import SourceHealthTracker
        tracker = SourceHealthTracker()
        for _ in range(3):
            tracker.record_attempt("test_src", False, error="error")
        assert tracker.get_status("test_src") == "degraded"

    def test_freshness(self):
        from services.source_health import SourceHealthTracker
        tracker = SourceHealthTracker()
        tracker.record_attempt("test_src", True)
        freshness = tracker.get_freshness("test_src")
        assert freshness is not None
        assert freshness < 1.0

    def test_classify_freshness(self):
        from services.source_health import classify_freshness
        assert classify_freshness(60, "active") == "live"
        assert classify_freshness(600, "active") == "fresh"
        assert classify_freshness(1800, "active") == "stale"
        assert classify_freshness(50000, "active") == "degraded"
        assert classify_freshness(None, "active") == "unavailable"
        assert classify_freshness(60, "degraded") == "degraded"


class TestLiveIngestionAPI:
    """Test live ingestion API endpoints."""

    def test_freshness_endpoint(self):
        r = client.get("/api/live/freshness")
        assert r.status_code == 200
        assert "sources" in r.json()

    def test_circuit_breaker_endpoint(self):
        r = client.get("/api/live/circuit-breaker")
        assert r.status_code == 200
        assert "breakers" in r.json()

    def test_ingest_single_source(self):
        r = client.get("/api/live/ingest/usgs?timeout=10")
        assert r.status_code == 200
        assert "source" in r.json()
        assert "success" in r.json()

    def test_trigger_ingestion(self):
        r = client.post("/api/live/ingest?sources=usgs&timeout=10")
        assert r.status_code == 200
        assert "total_events" in r.json()
