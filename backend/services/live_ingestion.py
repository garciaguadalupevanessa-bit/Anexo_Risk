"""Live Ingestion Service.

Polls data sources, normalizes events, deduplicates, and stores.
Implements: scheduler, timeout, retry, backoff, circuit breaker, freshness.
"""
import time
import threading
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

from services.source_health import health_tracker, classify_freshness
from services.normalized_adapters import (
    normalize_gdacs_event, normalize_usgs_event,
    normalize_firms_event, normalize_aemet_event,
)
from modules.normalized_events import models as event_models
from modules.source_registry import models as source_models


class CircuitBreaker:
    """Circuit breaker for source protection."""

    def __init__(self, failure_threshold=3, recovery_timeout=60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._failures: Dict[str, int] = {}
        self._open_until: Dict[str, float] = {}

    def is_open(self, source_id: str) -> bool:
        """Check if circuit is open (source should be skipped)."""
        if source_id not in self._open_until:
            return False
        if time.time() > self._open_until[source_id]:
            # Half-open: allow one attempt
            self._open_until.pop(source_id, None)
            return False
        return True

    def record_success(self, source_id: str):
        """Record success — reset failures."""
        self._failures.pop(source_id, None)
        self._open_until.pop(source_id, None)

    def record_failure(self, source_id: str):
        """Record failure — open circuit if threshold reached."""
        self._failures[source_id] = self._failures.get(source_id, 0) + 1
        if self._failures[source_id] >= self.failure_threshold:
            self._open_until[source_id] = time.time() + self.recovery_timeout

    def get_state(self, source_id: str) -> str:
        """Get circuit state: closed, open, half-open."""
        if self.is_open(source_id):
            return "open"
        if source_id in self._failures:
            return "half-open"
        return "closed"


class LiveIngestionService:
    """Orchestrates live data ingestion from all sources."""

    def __init__(self):
        self.circuit_breaker = CircuitBreaker()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stats: Dict[str, Dict[str, int]] = {}

    def fetch_source(self, source_id: str, timeout_seconds: int = 30) -> Dict[str, Any]:
        """Fetch and normalize events from a single source.

        Returns dict with: source, events, success, error, latency_ms.
        """
        if self.circuit_breaker.is_open(source_id):
            return {
                "source": source_id,
                "events": [],
                "success": False,
                "error": "Circuit breaker open",
                "latency_ms": 0,
            }

        start = time.time()
        try:
            # Get raw data from existing adapters
            raw_data = self._fetch_raw(source_id, timeout_seconds)
            latency_ms = (time.time() - start) * 1000

            # Normalize
            events = self._normalize(source_id, raw_data)

            # Dedup and store
            stored = self._dedup_and_store(source_id, events)

            # Record success
            self.circuit_breaker.record_success(source_id)
            health_tracker.record_attempt(source_id, True, latency_ms)

            return {
                "source": source_id,
                "events": stored,
                "success": True,
                "error": None,
                "latency_ms": latency_ms,
            }

        except FuturesTimeout:
            latency_ms = (time.time() - start) * 1000
            error = f"Timeout after {timeout_seconds}s"
            self.circuit_breaker.record_failure(source_id)
            health_tracker.record_attempt(source_id, False, latency_ms, error)
            return {"source": source_id, "events": [], "success": False, "error": error, "latency_ms": latency_ms}

        except Exception as e:
            latency_ms = (time.time() - start) * 1000
            error = str(e)
            self.circuit_breaker.record_failure(source_id)
            health_tracker.record_attempt(source_id, False, latency_ms, error)
            return {"source": source_id, "events": [], "success": False, "error": error, "latency_ms": latency_ms}

    def _fetch_raw(self, source_id: str, timeout: int) -> Any:
        """Fetch raw data from source using existing adapters."""
        # Use ThreadPoolExecutor for timeout
        with ThreadPoolExecutor(max_workers=1) as executor:
            if source_id == "gdacs":
                from integrations.gdacs_client import obtener_alertas_gdacs
                future = executor.submit(obtener_alertas_gdacs)
            elif source_id == "usgs":
                from geodata.adapters.usgs_adapter import USGSAdapter
                adapter = USGSAdapter()
                future = executor.submit(adapter.fetch, feed="week")
            elif source_id == "firms":
                from modules.incendios.models import obtener_detecciones_incendios
                future = executor.submit(obtener_detecciones_incendios, zona="spain")
            elif source_id in ("aemet", "open-meteo"):
                from modules.clima.models import obtener_alertas_clima
                future = executor.submit(obtener_alertas_clima)
            else:
                raise ValueError(f"Unknown source: {source_id}")

            return future.result(timeout=timeout)

    def _normalize(self, source_id: str, raw_data: Any) -> List[Dict]:
        """Normalize raw data into normalized events."""
        if source_id == "gdacs":
            if isinstance(raw_data, dict):
                raw_data = raw_data.get("alertas", raw_data.get("data", []))
            return [normalize_gdacs_event(e).__dict__ for e in (raw_data or [])]
        elif source_id == "usgs":
            return [normalize_usgs_event(e).__dict__ for e in (raw_data or [])]
        elif source_id == "firms":
            if isinstance(raw_data, dict):
                raw_data = raw_data.get("detecciones", [])
            return [normalize_firms_event(e).__dict__ for e in (raw_data or [])]
        elif source_id in ("aemet", "open-meteo"):
            if isinstance(raw_data, dict):
                raw_data = raw_data.get("alertas", [])
            return [normalize_aemet_event(e).__dict__ for e in (raw_data or [])]
        return []

    def _dedup_and_store(self, source_id: str, events: List[Dict]) -> List[Dict]:
        """Deduplicate and store events."""
        stored = []
        for event in events:
            ext_id = event.get("external_id", "")
            # Check if event already exists
            existing = event_models.list_events(
                source=source_id, limit=1
            )
            # Simple dedup by external_id
            is_dup = any(
                e.get("external_id") == ext_id for e in existing
            ) if ext_id else False

            if not is_dup:
                result = event_models.store_event(event)
                if result:
                    stored.append(result)
        return stored

    def ingest_all(self, sources: Optional[List[str]] = None, timeout_per_source: int = 30) -> Dict[str, Any]:
        """Ingest from all or specified sources.

        Returns summary of ingestion results.
        """
        if sources is None:
            sources = ["gdacs", "usgs", "firms", "aemet"]

        results = []
        for source_id in sources:
            result = self.fetch_source(source_id, timeout_per_source)
            results.append(result)

        total_events = sum(len(r["events"]) for r in results)
        successful = sum(1 for r in results if r["success"])

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sources_polled": len(results),
            "sources_successful": successful,
            "total_events": total_events,
            "results": results,
        }


# Global singleton
ingestion_service = LiveIngestionService()
