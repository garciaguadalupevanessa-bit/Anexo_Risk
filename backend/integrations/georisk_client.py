"""GeoRisk Finder integration client.

Provides optional integration with GeoRisk Finder's scientific risk analysis.
Anexo_Risk operates normally when GeoRisk is unavailable.

Circuit breaker: opens after 3 consecutive failures, resets after 60s.
Cache: 15 minutes per H3 cell.
"""
from __future__ import annotations

import time
import logging
from typing import Any

import httpx

from config import GEORISK_BASE_URL, GEORISK_TIMEOUT_SECONDS, GEORISK_CACHE_TTL_SECONDS

# Store real exception classes before any patching (used in except clauses)
_HttpxTimeout = httpx.TimeoutException
_HttpxHTTPStatusError = httpx.HTTPStatusError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Circuit breaker state
# ---------------------------------------------------------------------------
_cb_failures = 0
_cb_open_until = 0.0
_CB_THRESHOLD = 3
_CB_RESET_SECONDS = 60

# ---------------------------------------------------------------------------
# In-memory cache  {cache_key: (expires_at, data)}
# ---------------------------------------------------------------------------
_cache: dict[str, tuple[float, Any]] = {}


def _cache_get(key: str) -> Any | None:
    entry = _cache.get(key)
    if entry is None:
        return None
    expires_at, data = entry
    if time.time() > expires_at:
        _cache.pop(key, None)
        return None
    return data


def _cache_set(key: str, data: Any) -> None:
    _cache[key] = (time.time() + GEORISK_CACHE_TTL_SECONDS, data)


def _cb_record_success() -> None:
    global _cb_failures, _cb_open_until
    _cb_failures = 0
    _cb_open_until = 0.0


def _cb_record_failure() -> None:
    global _cb_failures, _cb_open_until
    _cb_failures += 1
    if _cb_failures >= _CB_THRESHOLD:
        _cb_open_until = time.time() + _CB_RESET_SECONDS
        logger.warning("GeoRisk circuit breaker OPEN — skipping for %ds", _CB_RESET_SECONDS)


def _cb_allow() -> bool:
    if _cb_failures < _CB_THRESHOLD:
        return True
    if time.time() > _cb_open_until:
        return True  # half-open: allow one test request
    return False


def is_georisk_available() -> bool:
    """Quick check: is the circuit breaker closed or half-open?"""
    return _cb_allow()


def get_circuit_status() -> dict:
    """Return circuit breaker status for observability."""
    if _cb_failures < _CB_THRESHOLD:
        return {"state": "closed", "failures": _cb_failures}
    if time.time() > _cb_open_until:
        return {"state": "half_open", "failures": _cb_failures}
    return {"state": "open", "failures": _cb_failures, "retry_after_s": int(_cb_open_until - time.time())}


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------
def _get(path: str, params: dict | None = None) -> dict | None:
    """GET from GeoRisk with timeout, circuit breaker, and cache."""
    if not _cb_allow():
        logger.info("GeoRisk circuit open — returning None for %s", path)
        return None

    cache_key = f"georisk:{path}:{params}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    url = f"{GEORISK_BASE_URL}{path}"
    try:
        resp = httpx.get(url, params=params, timeout=GEORISK_TIMEOUT_SECONDS)
        resp.raise_for_status()
        data = resp.json()
        _cb_record_success()
        _cache_set(cache_key, data)
        return data
    except _HttpxTimeout:
        _cb_record_failure()
        logger.warning("GeoRisk timeout: %s", path)
        return None
    except _HttpxHTTPStatusError as exc:
        _cb_record_failure()
        logger.warning("GeoRisk HTTP %d: %s", exc.response.status_code, path)
        return None
    except Exception as exc:
        _cb_record_failure()
        logger.warning("GeoRisk error: %s — %s", path, exc)
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def get_cell_risk(h3_index: str) -> dict | None:
    """Get scientific risk profile for an H3 cell from GeoRisk.

    Returns None if GeoRisk is unavailable or the cell is not found.
    """
    data = _get(f"/api/cell/{h3_index}")
    if data is None:
        return None
    # Normalize to our contract
    return {
        "h3_index": h3_index,
        "risk_score": data.get("risk_score", 0),
        "risk_level": data.get("risk_level", "unknown"),
        "model_version": data.get("model_version", "georisk-unknown"),
        "cluster_id": data.get("cluster_id"),
        "cluster_label": data.get("cluster_label", ""),
        "features": data.get("features", {}),
        "explanation": data.get("explanation", ""),
        "confidence": data.get("confidence", 0),
        "generated_at": data.get("generated_at", ""),
        "source": "georisk",
    }


def get_cell_events(h3_index: str) -> dict | None:
    """Get nearby hazard events for an H3 cell from GeoRisk."""
    return _get(f"/api/events/{h3_index}")


def get_ranking(limit: int = 10) -> list[dict] | None:
    """Get top risk cells from GeoRisk."""
    data = _get("/api/ranking", params={"limit": limit})
    if data is None:
        return None
    return data if isinstance(data, list) else data.get("cells", [])


def get_alerts() -> list[dict] | None:
    """Get live alerts from GeoRisk."""
    data = _get("/api/alerts")
    if data is None:
        return None
    return data if isinstance(data, list) else data.get("alerts", [])
