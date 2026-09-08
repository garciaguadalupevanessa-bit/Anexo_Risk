"""H3 Spatial Resolver — converts coordinates to H3 cells.

Uses H3 resolution 3 as the common spatial identifier between
Anexo_Risk and GeoRisk Finder.
"""
from __future__ import annotations

import logging

try:
    import h3
    H3_AVAILABLE = True
except ImportError:
    H3_AVAILABLE = False

logger = logging.getLogger(__name__)

H3_RESOLUTION = 3


def latlon_to_h3(lat: float, lon: float, resolution: int = H3_RESOLUTION) -> str | None:
    """Convert lat/lon to H3 cell index.

    Returns None if h3 is not installed or coordinates are invalid.
    """
    if not H3_AVAILABLE:
        logger.debug("h3 not installed — cannot resolve coordinates")
        return None
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        logger.warning("Invalid coordinates: lat=%s lon=%s", lat, lon)
        return None
    try:
        return h3.latlng_to_cell(lat, lon, resolution)
    except Exception as exc:
        logger.warning("H3 resolution failed: %s", exc)
        return None


def h3_to_center(h3_index: str) -> tuple[float, float] | None:
    """Convert H3 cell index to center lat/lon.

    Returns None if h3 is not installed or the index is invalid.
    """
    if not H3_AVAILABLE:
        return None
    try:
        lat, lon = h3.cell_to_latlng(h3_index)
        return (lat, lon)
    except Exception:
        return None


def get_h3_neighbors(h3_index: str, k: int = 1) -> list[str] | None:
    """Get H3 cell neighbors within k rings.

    Returns None if h3 is not installed.
    """
    if not H3_AVAILABLE:
        return None
    try:
        return list(h3.grid_disk(h3_index, k))
    except Exception:
        return None


def get_h3_resolution() -> int:
    """Return the configured H3 resolution."""
    return H3_RESOLUTION
