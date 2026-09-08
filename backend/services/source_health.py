"""Source Health tracking service.

Tracks health status, freshness, and metrics for all data sources.
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from modules.source_registry import models as source_models


class SourceHealthTracker:
    """Tracks health status for all sources."""

    def __init__(self):
        self._health: Dict[str, Dict[str, Any]] = {}

    def record_attempt(self, source_id: str, success: bool, latency_ms: float = None, error: str = None):
        """Record a fetch attempt for a source."""
        now = datetime.now(timezone.utc).isoformat()
        if source_id not in self._health:
            self._health[source_id] = {
                "status": "active",
                "last_attempt": now,
                "last_success": None,
                "last_failure": None,
                "error_count": 0,
                "success_count": 0,
                "latency_ms": None,
                "last_error": None,
            }
        h = self._health[source_id]
        h["last_attempt"] = now
        h["latency_ms"] = latency_ms

        if success:
            h["status"] = "active"
            h["last_success"] = now
            h["last_failure"] = None
            h["last_error"] = None
            h["error_count"] = 0
            h["success_count"] = h.get("success_count", 0) + 1
        else:
            h["error_count"] = h.get("error_count", 0) + 1
            h["last_failure"] = now
            h["last_error"] = error
            if h["error_count"] >= 3:
                h["status"] = "degraded"
            elif h["error_count"] >= 5:
                h["status"] = "unavailable"

        # Update source registry
        status = "active" if success else ("degraded" if h["error_count"] >= 3 else "active")
        source_models.update_source_status(
            source_id, status,
            last_fetch=now if success else None,
            error=error,
            latency_ms=latency_ms,
        )

    def get_health(self, source_id: str) -> Optional[Dict[str, Any]]:
        """Get health status for a source."""
        return self._health.get(source_id)

    def get_all_health(self) -> Dict[str, Dict[str, Any]]:
        """Get health status for all sources."""
        return dict(self._health)

    def get_freshness(self, source_id: str) -> Optional[float]:
        """Get seconds since last successful fetch."""
        h = self._health.get(source_id)
        if not h or not h.get("last_success"):
            return None
        try:
            last = datetime.fromisoformat(h["last_success"])
            now = datetime.now(timezone.utc)
            return (now - last).total_seconds()
        except (ValueError, TypeError):
            return None

    def get_status(self, source_id: str) -> str:
        """Get current status string for a source."""
        h = self._health.get(source_id)
        if not h:
            return "unknown"
        return h.get("status", "unknown")


# Global singleton
health_tracker = SourceHealthTracker()


def get_source_freshness_summary():
    """Get freshness summary for all sources."""
    sources = source_models.list_sources(status="active")
    result = []
    for src in sources:
        freshness = health_tracker.get_freshness(src["id"])
        status = health_tracker.get_status(src["id"])
        h = health_tracker.get_health(src["id"])
        result.append({
            "id": src["id"],
            "name": src["name"],
            "scope": src["scope"],
            "status": status,
            "freshness_seconds": freshness,
            "last_success": h.get("last_success") if h else None,
            "latency_ms": h.get("latency_ms") if h else None,
            "error_count": h.get("error_count", 0) if h else 0,
        })
    return result


def classify_freshness(freshness_seconds: Optional[float], source_status: str) -> str:
    """Classify freshness into operational status.

    LIVE: < 5 minutes
    FRESH: < 15 minutes
    STALE: < 60 minutes
    DEGRADED: < 24 hours or source degraded
    UNAVAILABLE: > 24 hours or source unavailable
    """
    if source_status in ("degraded", "unavailable"):
        return source_status
    if freshness_seconds is None:
        return "unavailable"
    if freshness_seconds < 300:
        return "live"
    if freshness_seconds < 900:
        return "fresh"
    if freshness_seconds < 3600:
        return "stale"
    if freshness_seconds < 86400:
        return "degraded"
    return "unavailable"
