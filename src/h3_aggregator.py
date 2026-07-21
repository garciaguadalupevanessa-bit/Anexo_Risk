"""
H3 hexagonal spatial aggregation for geological risk data.

Provides functions to assign H3 cell IDs to lat/lon points and
aggregate point data (cyclones, volcanoes, seismic events) per cell.
Joel (Persona 3) can extend or replace this module with the final
grid implementation while keeping the same interface.
"""

import h3
import numpy as np
import pandas as pd


def lat_lon_to_h3(lat: float, lon: float, res: int) -> str | None:
    try:
        return h3.latlng_to_cell(lat, lon, res)
    except Exception:
        return None


def aggregate_by_h3(
    df: pd.DataFrame, res: int, agg: dict | None = None
) -> pd.DataFrame:
    df = df.copy()
    df["h3_index"] = df.apply(
        lambda r: lat_lon_to_h3(r["lat"], r["lon"], res), axis=1
    )
    df = df.dropna(subset=["h3_index"])

    numeric_cols = [
        c for c in df.select_dtypes(include=[np.number]).columns if c != "h3_index"
    ]
    cat_cols = [c for c in df.columns if c not in numeric_cols and c != "h3_index"]

    agg_dict = {c: (agg.get(c, "mean") if agg else "mean") for c in numeric_cols}
    for c in cat_cols:
        agg_dict[c] = "first"

    grouped = df.groupby("h3_index").agg(agg_dict).reset_index()
    grouped["lat"] = grouped["h3_index"].apply(lambda h: h3.cell_to_latlng(h)[0])
    grouped["lon"] = grouped["h3_index"].apply(lambda h: h3.cell_to_latlng(h)[1])

    return grouped


def merge_h3_datasets(
    datasets: list[tuple[str, pd.DataFrame, dict]],
    res: int,
) -> pd.DataFrame:
    merged = None
    for prefix, df, agg_dict in datasets:
        if df.empty:
            continue
        part = aggregate_by_h3(df, res, agg_dict)
        part = part.add_prefix(prefix)
        part = part.rename(columns={f"{prefix}h3_index": "_h3_key"})
        if merged is None:
            merged = part
        else:
            merged = merged.merge(part, on="_h3_key", how="outer")
    return merged
