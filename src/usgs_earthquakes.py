"""USGS earthquake data ingestion and cleaning.

This module downloads global earthquake records from the USGS
Earthquake Catalog, validates the data and exports reproducible
raw and processed datasets for the GeoRisk Finder project.

Responsibilities:
- Query the USGS Earthquake Catalog.
- Download earthquake data.
- Validate essential fields.
- Remove duplicate records.
- Standardize column names and data types.
- Export raw and cleaned datasets.

Out of scope:
- H3 geographical aggregation.
- Feature engineering for clustering.
- Scaling and PCA.
- Clustering models.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests


# ---------------------------------------------------------------------------
# USGS API configuration
# ---------------------------------------------------------------------------

USGS_API_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"

START_DATE = "1900-01-01"
END_DATE = datetime.now(timezone.utc).date().isoformat()

MIN_MAGNITUDE = 4.5
EVENT_TYPE = "earthquake"

MADRID_TIMEZONE = "Europe/Madrid"

REQUEST_TIMEOUT_SECONDS = 60
MAX_RESULTS_PER_REQUEST = 20_000


# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw" / "earthquakes"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

RAW_DATA_PATH = RAW_DATA_DIR / "usgs_earthquakes_raw.csv"
PROCESSED_DATA_PATH = (
    PROCESSED_DATA_DIR / "usgs_earthquakes_clean.csv"
)

# ---------------------------------------------------------------------------
# Dataset schema
# ---------------------------------------------------------------------------

USGS_COLUMN_RENAME_MAP = {
    "id": "event_id",
    "time": "timestamp_utc",
    "updated": "updated_at_utc",
    "latitude": "lat",
    "longitude": "lon",
    "depth": "depth_km",
    "mag": "magnitude",
    "magType": "magnitude_type",
    "place": "place",
    "type": "event_type",
    "net": "network",
    "nst": "station_count",
    "gap": "azimuthal_gap",
    "dmin": "nearest_station_distance",
    "rms": "rms_error",
    "horizontalError": "horizontal_error_km",
    "depthError": "depth_error_km",
    "magError": "magnitude_error",
    "magNst": "magnitude_station_count",
    "status": "review_status",
    "locationSource": "location_source",
    "magSource": "magnitude_source",
}

ESSENTIAL_COLUMNS = [
    "event_id",
    "timestamp_utc",
    "lat",
    "lon",
    "depth_km",
    "magnitude",
]

NUMERIC_COLUMNS = [
    "lat",
    "lon",
    "depth_km",
    "magnitude",
    "station_count",
    "azimuthal_gap",
    "nearest_station_distance",
    "rms_error",
    "horizontal_error_km",
    "depth_error_km",
    "magnitude_error",
    "magnitude_station_count",
]

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

LOGGER = logging.getLogger(__name__)