"""Normalized adapter contract for all data sources.

Every source adapter must implement this interface:
- fetch() → raw data from source
- normalize() → normalized events
- health() → source health status
- freshness() → how fresh is the data
- capabilities() → what the source supports
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class SourceStatus(str, Enum):
    ACTIVE = "active"
    DEGRADED = "degraded"
    STALE = "stale"
    UNAVAILABLE = "unavailable"
    DISABLED = "disabled"


class EntityType(str, Enum):
    EARTHQUAKE = "earthquake"
    FIRE = "fire"
    FLOOD = "flood"
    CYCLONE = "cyclone"
    VOLCANO = "volcano"
    WEATHER = "weather"
    ALERT = "alert"
    HOTSPOT = "hotspot"
    RISK = "risk"
    OTHER = "other"


@dataclass
class NormalizedEvent:
    """Standard event output from any adapter."""
    id: str
    external_id: str
    entity_type: EntityType
    source: str
    title: str
    description: str = ""
    timestamp: Optional[str] = None
    updated_at: Optional[str] = None
    severity: Optional[str] = None
    severity_float: Optional[float] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    geometry: Optional[Dict[str, Any]] = None
    country: Optional[str] = None
    region: Optional[str] = None
    status: str = "active"
    is_active: bool = True
    h3_index: Optional[str] = None
    magnitude: Optional[float] = None
    depth: Optional[float] = None
    confidence: Optional[float] = None
    raw_metadata: Optional[Dict[str, Any]] = None
    provenance: Optional[Dict[str, Any]] = None


@dataclass
class SourceCapabilities:
    """What a source supports."""
    supports_point: bool = False
    supports_bbox: bool = False
    supports_region: bool = False
    data_types: List[str] = field(default_factory=list)
    update_interval_seconds: int = 300
    authentication: str = "none"
    license: str = ""


@dataclass
class SourceHealth:
    """Current health of a source."""
    status: SourceStatus = SourceStatus.ACTIVE
    last_successful_fetch: Optional[str] = None
    last_failure: Optional[str] = None
    last_error: Optional[str] = None
    latency_ms: Optional[float] = None
    freshness_seconds: Optional[float] = None


class SourceAdapter(ABC):
    """Abstract base class for all source adapters."""

    def __init__(self, source_id: str, config: Optional[Dict[str, Any]] = None):
        self.source_id = source_id
        self.config = config or {}
        self._health = SourceHealth()
        self._cache = {}
        self._cache_ttl = self.config.get("cache_ttl_seconds", 300)

    @abstractmethod
    def fetch(self, **kwargs) -> Any:
        """Fetch raw data from the source.

        Args:
            **kwargs: Source-specific parameters (lat, lon, bbox, region, etc.)

        Returns:
            Raw data from the source (dict, list, or bytes).
        """
        pass

    @abstractmethod
    def normalize(self, raw_data: Any) -> List[NormalizedEvent]:
        """Transform raw data into normalized events.

        Args:
            raw_data: Output from fetch()

        Returns:
            List of NormalizedEvent objects.
        """
        pass

    def health(self) -> SourceHealth:
        """Get current source health."""
        return self._health

    def freshness(self) -> Optional[float]:
        """Seconds since last successful fetch."""
        if self._health.last_successful_fetch:
            try:
                last = datetime.fromisoformat(self._health.last_successful_fetch)
                now = datetime.now(timezone.utc)
                return (now - last).total_seconds()
            except (ValueError, TypeError):
                pass
        return None

    @abstractmethod
    def capabilities(self) -> SourceCapabilities:
        """Describe what this source supports."""
        pass

    def is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid."""
        if key not in self._cache:
            return False
        cached_at = self._cache[key].get("timestamp")
        if not cached_at:
            return False
        try:
            age = (datetime.now(timezone.utc) - datetime.fromisoformat(cached_at)).total_seconds()
            return age < self._cache_ttl
        except (ValueError, TypeError):
            return False

    def get_cached(self, key: str) -> Any:
        """Get data from cache if valid."""
        if self.is_cache_valid(key):
            return self._cache[key].get("data")
        return None

    def set_cache(self, key: str, data: Any):
        """Store data in cache."""
        self._cache[key] = {
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _update_health(self, status: SourceStatus, error: str = None, latency_ms: float = None):
        """Update source health after an operation."""
        now = datetime.now(timezone.utc).isoformat()
        self._health.status = status
        self._health.latency_ms = latency_ms
        if status == SourceStatus.ACTIVE and not error:
            self._health.last_successful_fetch = now
            self._health.last_failure = None
            self._health.last_error = None
        else:
            self._health.last_failure = now
            self._health.last_error = error
