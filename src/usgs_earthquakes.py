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
from io import StringIO
from pathlib import Path

import pandas as pd
import requests


# ---------------------------------------------------------------------------
# USGS API configuration
# ---------------------------------------------------------------------------

USGS_API_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
USGS_COUNT_URL = "https://earthquake.usgs.gov/fdsnws/event/1/count"

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
PROCESSED_DATA_PATH = PROCESSED_DATA_DIR / "usgs_earthquakes_clean.csv"

# ---------------------------------------------------------------------------
# Dataset schema
# ---------------------------------------------------------------------------

USGS_COLUMN_RENAME_MAP = {
    "id": "event_id",
    "time": "timestamp",
    "updated": "updated_at",
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
    "timestamp",
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

MAGNITUDE_SCALE_NAMES = {
    "ml": "Local magnitude (Richter)",
    "md": "Duration magnitude",
    "mb": "Body-wave magnitude",
    "ms": "Surface-wave magnitude",
    "mw": "Moment magnitude",
    "mwb": "Moment magnitude",
    "mwc": "Moment magnitude",
    "mwr": "Moment magnitude",
    "mww": "Moment magnitude",
}

MAGNITUDE_CATEGORY_BINS = [
    float("-inf"),
    4.0,
    5.0,
    6.0,
    7.0,
    8.0,
    float("inf"),
]

MAGNITUDE_CATEGORY_LABELS = [
    "minor",
    "light",
    "moderate",
    "strong",
    "major",
    "great",
]

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

LOGGER = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# USGS API helpers
# ---------------------------------------------------------------------------


def build_query_params(
    start_date: str,
    end_date: str,
    min_magnitude: float = MIN_MAGNITUDE,
) -> dict[str, str | float]:
    """Build the common parameters used in USGS API requests.

    Parameters
    ----------
    start_date:
        First date included in the query, using YYYY-MM-DD format.
    end_date:
        Last date included in the query, using YYYY-MM-DD format.
    min_magnitude:
        Minimum earthquake magnitude included in the query.

    Returns
    -------
    dict
        Parameters ready to be sent to the USGS API.
    """
    return {
        "starttime": start_date,
        "endtime": end_date,
        "minmagnitude": min_magnitude,
        "eventtype": EVENT_TYPE,
    }


def count_usgs_events(
    start_date: str,
    end_date: str,
    min_magnitude: float = MIN_MAGNITUDE,
) -> int:
    """Return the number of USGS earthquakes matching the filters.

    This check is performed before downloading a period so the script can
    detect queries that contain too many records for one API request.
    """
    params = build_query_params(
        start_date=start_date,
        end_date=end_date,
        min_magnitude=min_magnitude,
    )

    LOGGER.info(
        "Counting USGS events from %s to %s with magnitude >= %.1f",
        start_date,
        end_date,
        min_magnitude,
    )

    try:
        response = requests.get(
            USGS_COUNT_URL,
            params=params,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError("The USGS event count request failed.") from exc

    try:
        event_count = int(response.text.strip())
    except ValueError as exc:
        raise RuntimeError("The USGS count response was not a valid integer.") from exc

    LOGGER.info("USGS returned %s matching events", event_count)

    return event_count


def download_usgs_period(
    start_date: str,
    end_date: str,
    min_magnitude: float = MIN_MAGNITUDE,
) -> pd.DataFrame:
    """Download USGS earthquake records for one time period.

    The function checks the number of matching records before downloading
    them. If the period contains more events than the API request limit,
    the function recursively splits the period into smaller intervals.

    Parameters
    ----------
    start_date:
        First date included in the query, using YYYY-MM-DD format.
    end_date:
        Last date included in the query, using YYYY-MM-DD format.
    min_magnitude:
        Minimum earthquake magnitude included in the query.

    Returns
    -------
    pandas.DataFrame
        Raw earthquake records returned by the USGS API.

    Raises
    ------
    ValueError
        If the number of matching records exceeds the request limit.
    RuntimeError
        If the USGS request fails or returns invalid CSV data.
    """
    event_count = count_usgs_events(
        start_date=start_date,
        end_date=end_date,
        min_magnitude=min_magnitude,
    )

    if event_count == 0:
        LOGGER.warning(
            "No USGS events found from %s to %s",
            start_date,
            end_date,
        )
        return pd.DataFrame()

    if event_count > MAX_RESULTS_PER_REQUEST:
        interval_start = pd.Timestamp(start_date)
        interval_end = pd.Timestamp(end_date)
        interval_duration = interval_end - interval_start

        if interval_duration <= pd.Timedelta(seconds=1):
            raise RuntimeError(
                f"The interval {start_date} to {end_date} still contains "
                f"{event_count:,} events and cannot be divided safely."
            )

        midpoint = interval_start + interval_duration / 2
        midpoint_text = midpoint.isoformat()

        LOGGER.info(
            "Period exceeds the API limit. Splitting at %s",
            midpoint_text,
        )

        first_half = download_usgs_period(
            start_date=start_date,
            end_date=midpoint_text,
            min_magnitude=min_magnitude,
        )

        second_half = download_usgs_period(
            start_date=midpoint_text,
            end_date=end_date,
            min_magnitude=min_magnitude,
        )

        combined_halves = pd.concat(
            [first_half, second_half],
            ignore_index=True,
        )

        if "id" in combined_halves.columns:
            combined_halves = combined_halves.drop_duplicates(
                subset="id", keep="last"
            ).reset_index(drop=True)

        return combined_halves

    params = build_query_params(
        start_date=start_date,
        end_date=end_date,
        min_magnitude=min_magnitude,
    )
    params.update(
        {
            "format": "csv",
            "orderby": "time-asc",
            "limit": MAX_RESULTS_PER_REQUEST,
        }
    )

    LOGGER.info(
        "Downloading %s USGS events from %s to %s",
        event_count,
        start_date,
        end_date,
    )

    try:
        response = requests.get(
            USGS_API_URL,
            params=params,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(
            f"The USGS download request failed for {start_date} to {end_date}."
        ) from exc

    try:
        dataframe = pd.read_csv(StringIO(response.text))
    except (pd.errors.ParserError, UnicodeDecodeError) as exc:
        raise RuntimeError(
            "The USGS response could not be interpreted as CSV."
        ) from exc

    if len(dataframe) != event_count:
        LOGGER.warning(
            "Expected %s events but downloaded %s rows",
            event_count,
            len(dataframe),
        )

    LOGGER.info(
        "Downloaded %s rows and %s columns",
        len(dataframe),
        len(dataframe.columns),
    )

    return dataframe


def download_usgs_history(
    start_date: str = START_DATE,
    end_date: str = END_DATE,
    min_magnitude: float = MIN_MAGNITUDE,
) -> pd.DataFrame:
    """Download the USGS earthquake catalogue in yearly intervals.

    Splitting the historical range prevents individual requests from
    exceeding the USGS API result limit. Duplicate event identifiers are
    removed after concatenating all periods because events located exactly
    at interval boundaries may appear more than once.

    Parameters
    ----------
    start_date:
        First date included in the historical download.
    end_date:
        Final date included in the historical download.
    min_magnitude:
        Minimum earthquake magnitude included.

    Returns
    -------
    pandas.DataFrame
        Combined raw USGS earthquake catalogue.
    """
    start_timestamp = pd.Timestamp(start_date)
    end_timestamp = pd.Timestamp(end_date)

    if start_timestamp >= end_timestamp:
        raise ValueError("start_date must be earlier than end_date.")

    period_starts = pd.date_range(
        start=start_timestamp,
        end=end_timestamp,
        freq="YS",
    )

    if period_starts.empty or period_starts[0] != start_timestamp:
        period_starts = period_starts.insert(0, start_timestamp)

    if period_starts[-1] != end_timestamp:
        period_starts = period_starts.append(pd.DatetimeIndex([end_timestamp]))

    downloaded_periods: list[pd.DataFrame] = []

    for period_start, period_end in zip(
        period_starts[:-1],
        period_starts[1:],
    ):
        start_text = period_start.date().isoformat()
        end_text = period_end.date().isoformat()

        dataframe = download_usgs_period(
            start_date=start_text,
            end_date=end_text,
            min_magnitude=min_magnitude,
        )

        if not dataframe.empty:
            downloaded_periods.append(dataframe)

    if not downloaded_periods:
        LOGGER.warning("No earthquake records were downloaded.")
        return pd.DataFrame()

    combined_dataframe = pd.concat(
        downloaded_periods,
        ignore_index=True,
    )

    rows_before_deduplication = len(combined_dataframe)

    if "id" in combined_dataframe.columns:
        combined_dataframe = (
            combined_dataframe.sort_values("updated")
            .drop_duplicates(subset="id", keep="last")
            .reset_index(drop=True)
        )

    removed_duplicates = rows_before_deduplication - len(combined_dataframe)

    LOGGER.info(
        "Combined historical catalogue: %s rows",
        len(combined_dataframe),
    )
    LOGGER.info(
        "Duplicate event identifiers removed: %s",
        removed_duplicates,
    )

    return combined_dataframe


# ---------------------------------------------------------------------------
# Data cleaning
# ---------------------------------------------------------------------------


def clean_usgs_data(
    dataframe: pd.DataFrame,
    min_magnitude: float = MIN_MAGNITUDE,
) -> pd.DataFrame:
    """Clean and standardize raw USGS earthquake records.

    The function renames columns, converts data types, validates essential
    fields, removes duplicates and creates descriptive helper columns.

    Negative depths are preserved because some USGS events may be located
    above the reference sea level.
    """
    if dataframe.empty:
        raise ValueError("The raw USGS dataframe is empty and cannot be cleaned.")

    cleaned_dataframe = dataframe.copy()

    cleaned_dataframe = cleaned_dataframe.rename(
        columns=USGS_COLUMN_RENAME_MAP,
    )

    missing_columns = [
        column
        for column in ESSENTIAL_COLUMNS
        if column not in cleaned_dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            "The USGS dataframe is missing essential columns: "
            + ", ".join(missing_columns)
        )

    string_columns = [
        "event_id",
        "place",
        "event_type",
        "network",
        "magnitude_type",
        "review_status",
        "location_source",
        "magnitude_source",
    ]

    for column in string_columns:
        if column in cleaned_dataframe.columns:
            cleaned_dataframe[column] = (
                cleaned_dataframe[column]
                .astype("string")
                .str.strip()
                .replace("", pd.NA)
            )

    if "magnitude_type" in cleaned_dataframe.columns:
        cleaned_dataframe["magnitude_type"] = cleaned_dataframe[
            "magnitude_type"
        ].str.lower()

    if "event_type" in cleaned_dataframe.columns:
        cleaned_dataframe["event_type"] = cleaned_dataframe["event_type"].str.lower()

    cleaned_dataframe["timestamp"] = pd.to_datetime(
        cleaned_dataframe["timestamp"],
        errors="coerce",
        utc=True,
    )

    if "updated_at" in cleaned_dataframe.columns:
        cleaned_dataframe["updated_at"] = pd.to_datetime(
            cleaned_dataframe["updated_at"],
            errors="coerce",
            utc=True,
        )

    for column in NUMERIC_COLUMNS:
        if column in cleaned_dataframe.columns:
            cleaned_dataframe[column] = pd.to_numeric(
                cleaned_dataframe[column],
                errors="coerce",
            )

    rows_before_cleaning = len(cleaned_dataframe)

    cleaned_dataframe = cleaned_dataframe.dropna(
        subset=ESSENTIAL_COLUMNS,
    )

    cleaned_dataframe = cleaned_dataframe[
        cleaned_dataframe["lat"].between(-90, 90)
        & cleaned_dataframe["lon"].between(-180, 180)
        & (cleaned_dataframe["magnitude"] >= min_magnitude)
    ]

    if "event_type" in cleaned_dataframe.columns:
        cleaned_dataframe = cleaned_dataframe[
            cleaned_dataframe["event_type"] == EVENT_TYPE
        ]

    cleaned_dataframe = (
        cleaned_dataframe.sort_values(
            ["event_id", "updated_at"],
            na_position="first",
        )
        .drop_duplicates(
            subset="event_id",
            keep="last",
        )
        .reset_index(drop=True)
    )

    cleaned_dataframe["timestamp_madrid"] = cleaned_dataframe[
        "timestamp"
    ].dt.tz_convert(MADRID_TIMEZONE)

    cleaned_dataframe["magnitude_scale_name"] = (
        cleaned_dataframe["magnitude_type"]
        .map(MAGNITUDE_SCALE_NAMES)
        .fillna("Other or unspecified magnitude scale")
    )

    cleaned_dataframe["magnitude_category"] = pd.cut(
        cleaned_dataframe["magnitude"],
        bins=MAGNITUDE_CATEGORY_BINS,
        labels=MAGNITUDE_CATEGORY_LABELS,
        right=False,
        include_lowest=True,
    ).astype("string")

    cleaned_dataframe["source"] = "USGS"

    cleaned_dataframe = cleaned_dataframe.sort_values("timestamp").reset_index(
        drop=True
    )

    removed_rows = rows_before_cleaning - len(cleaned_dataframe)

    LOGGER.info(
        "Cleaned USGS dataset: %s rows retained and %s rows removed",
        len(cleaned_dataframe),
        removed_rows,
    )

    return cleaned_dataframe


# ---------------------------------------------------------------------------
# Data export helpers
# ---------------------------------------------------------------------------


def ensure_data_directories() -> None:
    """Create the raw and processed data directories when necessary."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)


def save_raw_data(
    dataframe: pd.DataFrame,
    output_path: Path = RAW_DATA_PATH,
) -> Path:
    """Save the raw USGS catalogue as a CSV file.

    Parameters
    ----------
    dataframe:
        Raw earthquake records downloaded from the USGS API.
    output_path:
        Destination CSV path.

    Returns
    -------
    pathlib.Path
        Path where the dataset was saved.
    """
    if dataframe.empty:
        raise ValueError("The raw USGS dataframe is empty and cannot be exported.")

    ensure_data_directories()

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataframe.to_csv(
        output_path,
        index=False,
    )

    LOGGER.info(
        "Raw USGS dataset saved to %s with %s rows",
        output_path,
        len(dataframe),
    )

    return output_path


def save_processed_data(
    dataframe: pd.DataFrame,
    output_path: Path = PROCESSED_DATA_PATH,
) -> Path:
    """Save the cleaned USGS earthquake catalogue as a CSV file.

    Parameters
    ----------
    dataframe:
        Cleaned and standardized earthquake records.
    output_path:
        Destination CSV path.

    Returns
    -------
    pathlib.Path
        Path where the cleaned dataset was saved.
    """
    if dataframe.empty:
        raise ValueError("The cleaned USGS dataframe is empty and cannot be exported.")

    ensure_data_directories()

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataframe.to_csv(
        output_path,
        index=False,
    )

    LOGGER.info(
        "Processed USGS dataset saved to %s with %s rows",
        output_path,
        len(dataframe),
    )

    return output_path


def run_ingestion(
    start_date: str = START_DATE,
    end_date: str = END_DATE,
    min_magnitude: float = MIN_MAGNITUDE,
    output_path: Path = RAW_DATA_PATH,
) -> Path:
    """Download and save the raw historical USGS earthquake catalogue."""
    LOGGER.info(
        "Starting USGS ingestion from %s to %s with magnitude >= %.1f",
        start_date,
        end_date,
        min_magnitude,
    )

    raw_dataframe = download_usgs_history(
        start_date=start_date,
        end_date=end_date,
        min_magnitude=min_magnitude,
    )

    saved_path = save_raw_data(
        raw_dataframe,
        output_path=output_path,
    )

    LOGGER.info("USGS ingestion completed successfully")

    return saved_path


def run_pipeline(
    start_date: str = START_DATE,
    end_date: str = END_DATE,
    min_magnitude: float = MIN_MAGNITUDE,
    raw_output_path: Path = RAW_DATA_PATH,
    processed_output_path: Path = PROCESSED_DATA_PATH,
) -> tuple[Path, Path]:
    """Run the complete USGS ingestion and cleaning pipeline.

    The pipeline downloads the historical catalogue, exports the raw data,
    cleans and standardizes the records, and exports the processed dataset.

    Returns
    -------
    tuple[pathlib.Path, pathlib.Path]
        Paths of the raw and processed CSV files.
    """
    LOGGER.info(
        "Starting complete USGS pipeline from %s to %s",
        start_date,
        end_date,
    )

    raw_dataframe = download_usgs_history(
        start_date=start_date,
        end_date=end_date,
        min_magnitude=min_magnitude,
    )

    raw_path = save_raw_data(
        raw_dataframe,
        output_path=raw_output_path,
    )

    cleaned_dataframe = clean_usgs_data(
        raw_dataframe,
        min_magnitude=min_magnitude,
    )

    processed_path = save_processed_data(
        cleaned_dataframe,
        output_path=processed_output_path,
    )

    LOGGER.info("Complete USGS pipeline finished successfully")

    return raw_path, processed_path


if __name__ == "__main__":
    run_pipeline()
