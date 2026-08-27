"""Cleaning and alignment helpers for project financial time series."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.config import PROCESSED_DATA_DIR, RAW_DATA_DIR
from src.utils import assert_columns, write_json


def _read_stooq_price(path: Path, prefix: str) -> pd.DataFrame:
    data = pd.read_csv(path)
    assert_columns(data, ["Date", "Open", "High", "Low", "Close"])
    data = data.rename(columns={c: c.lower() for c in data.columns})
    data["date"] = pd.to_datetime(data["date"], errors="coerce")
    keep = ["date", "open", "high", "low", "close"]
    if "volume" in data.columns:
        keep.append("volume")
    data = data[keep].rename(
        columns={col: f"{prefix}_{col}" for col in keep if col != "date"}
    )
    return data


def _read_fred_yield(path: Path, series_id: str, column: str) -> pd.DataFrame:
    data = pd.read_csv(path)
    assert_columns(data, ["observation_date", series_id])
    data = data.rename(columns={"observation_date": "date", series_id: column})
    data["date"] = pd.to_datetime(data["date"], errors="coerce")
    data[column] = pd.to_numeric(data[column].replace(".", np.nan), errors="coerce")
    return data[["date", column]]


def load_raw_sources(raw_dir: Path = RAW_DATA_DIR) -> dict[str, pd.DataFrame]:
    """Load saved raw source files from ``data/raw``."""

    return {
        "sp500": _read_stooq_price(raw_dir / "sp500_yahoo.csv", "sp500"),
        "vix": _read_stooq_price(raw_dir / "vix_yahoo.csv", "vix"),
        "treasury_10y": _read_fred_yield(raw_dir / "treasury_10y_fred.csv", "DGS10", "treasury_10y"),
        "treasury_2y": _read_fred_yield(raw_dir / "treasury_2y_fred.csv", "DGS2", "treasury_2y"),
    }


def clean_and_align_sources(raw_dir: Path = RAW_DATA_DIR) -> pd.DataFrame:
    """Clean, validate, and align raw S&P 500, VIX, and Treasury data.

    Treasury yields are forward-filled only across market dates after the left
    join to S&P 500 trading days. This treats holiday/reporting gaps as stale
    but still known information. Rows with missing market stress values are
    dropped because VIX and S&P prices are essential model inputs.
    """

    sources = load_raw_sources(raw_dir)
    sp500 = sources["sp500"].dropna(subset=["date", "sp500_close"]).copy()
    sp500 = sp500.sort_values("date").drop_duplicates("date").reset_index(drop=True)

    vix = sources["vix"].dropna(subset=["date", "vix_close"]).copy()
    vix = vix.sort_values("date").drop_duplicates("date").reset_index(drop=True)

    data = sp500.merge(vix[["date", "vix_close"]], on="date", how="left")
    data = data.merge(sources["treasury_10y"], on="date", how="left")
    data = data.merge(sources["treasury_2y"], on="date", how="left")
    data = data.sort_values("date").drop_duplicates("date").reset_index(drop=True)

    numeric_columns = [c for c in data.columns if c != "date"]
    for column in numeric_columns:
        data[column] = pd.to_numeric(data[column], errors="coerce")

    data[["treasury_10y", "treasury_2y"]] = data[["treasury_10y", "treasury_2y"]].ffill()
    data = data.dropna(subset=["sp500_close", "vix_close", "treasury_10y", "treasury_2y"]).reset_index(drop=True)
    data["sp500_return"] = data["sp500_close"].pct_change()
    data["vix_change"] = data["vix_close"].diff()
    data["vix_pct_change"] = data["vix_close"].pct_change()
    data["yield_spread_10y_2y"] = data["treasury_10y"] - data["treasury_2y"]
    data = data.dropna(subset=["sp500_return", "vix_change", "vix_pct_change"]).reset_index(drop=True)

    if not data["date"].is_monotonic_increasing:
        raise ValueError("Cleaned data must be sorted by date")
    if len(data) < 500:
        raise ValueError(f"Cleaned data is too small for project modeling: {len(data)} rows")

    return data


def save_cleaned_dataset(
    data: pd.DataFrame,
    processed_dir: Path = PROCESSED_DATA_DIR,
    filename: str = "market_data_cleaned.csv",
) -> Path:
    """Persist the cleaned market dataset and a small metadata file."""

    processed_dir.mkdir(parents=True, exist_ok=True)
    output_path = processed_dir / filename
    data.to_csv(output_path, index=False)
    metadata = {
        "file": str(output_path),
        "rows": int(len(data)),
        "columns": data.columns.tolist(),
        "min_date": str(data["date"].min().date()),
        "max_date": str(data["date"].max().date()),
        "missing_counts": data.isna().sum().astype(int).to_dict(),
        "cleaning_assumptions": [
            "S&P 500 trading dates define the analysis calendar.",
            "Treasury yields are forward-filled across market dates after publication gaps.",
            "Extreme returns and volatility spikes are retained because they are risk-relevant.",
        ],
    }
    write_json(metadata, processed_dir / "cleaning_metadata.json")
    return output_path
