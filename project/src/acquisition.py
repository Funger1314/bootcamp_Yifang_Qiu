"""Data acquisition for the S&P 500 short-term volatility project.

The project uses public, keyless sources so a reviewer can reproduce the raw
data without secrets:

* Yahoo Finance chart downloads for S&P 500 index prices and VIX.
* FRED CSV downloads for 10-year and 2-year Treasury yields.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

from src.config import RAW_DATA_DIR
from src.utils import write_json


YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"


@dataclass(frozen=True)
class SourceSpec:
    """Metadata needed to download and normalize one raw source."""

    name: str
    source: str
    symbol: str
    filename: str


SOURCES = [
    SourceSpec("sp500", "yahoo", "^GSPC", "sp500_yahoo.csv"),
    SourceSpec("vix", "yahoo", "^VIX", "vix_yahoo.csv"),
    SourceSpec("treasury_10y", "fred", "DGS10", "treasury_10y_fred.csv"),
    SourceSpec("treasury_2y", "fred", "DGS2", "treasury_2y_fred.csv"),
]


def _yyyymmdd(value: str | date) -> str:
    return pd.Timestamp(value).strftime("%Y%m%d")


def download_yahoo_chart(symbol: str, start_date: str, end_date: str, timeout: int = 30) -> pd.DataFrame:
    """Download daily OHLCV data from Yahoo Finance's chart endpoint."""

    period1 = int(pd.Timestamp(start_date, tz="UTC").timestamp())
    period2 = int((pd.Timestamp(end_date, tz="UTC") + pd.Timedelta(days=1)).timestamp())
    response = requests.get(
        YAHOO_CHART_URL.format(symbol=symbol),
        params={"period1": period1, "period2": period2, "interval": "1d", "events": "history"},
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    result = payload.get("chart", {}).get("result")
    if not result:
        raise ValueError(f"Yahoo Finance returned no chart data for {symbol}: {payload}")
    chart = result[0]
    timestamps = chart.get("timestamp", [])
    quote = chart.get("indicators", {}).get("quote", [{}])[0]
    if not timestamps or not quote:
        raise ValueError(f"Yahoo Finance returned incomplete chart data for {symbol}")
    data = pd.DataFrame(
        {
            "Date": pd.to_datetime(timestamps, unit="s", utc=True).tz_convert(None).date,
            "Open": quote.get("open"),
            "High": quote.get("high"),
            "Low": quote.get("low"),
            "Close": quote.get("close"),
            "Volume": quote.get("volume"),
        }
    )
    data = data.dropna(subset=["Close"]).reset_index(drop=True)
    if data.empty:
        raise ValueError(f"Yahoo Finance returned an empty table for {symbol}")
    return data


def download_fred(series_id: str, start_date: str, end_date: str, timeout: int = 30) -> pd.DataFrame:
    """Download a FRED series and filter to the requested date range."""

    response = requests.get(FRED_URL, params={"id": series_id}, timeout=timeout)
    response.raise_for_status()
    data = pd.read_csv(StringIO(response.text))
    if "observation_date" not in data.columns or series_id not in data.columns:
        raise ValueError(f"Unexpected FRED schema for {series_id}: {data.columns.tolist()}")
    data["observation_date"] = pd.to_datetime(data["observation_date"])
    mask = (data["observation_date"] >= pd.Timestamp(start_date)) & (
        data["observation_date"] <= pd.Timestamp(end_date)
    )
    data = data.loc[mask].reset_index(drop=True)
    if data.empty:
        raise ValueError(f"FRED returned no rows for {series_id} in requested range")
    return data


def acquire_raw_data(
    start_date: str = "2018-01-01",
    end_date: str | None = None,
    raw_dir: Path = RAW_DATA_DIR,
) -> dict[str, Path]:
    """Download all raw project datasets and save them in ``data/raw``."""

    end_date = end_date or pd.Timestamp.today().strftime("%Y-%m-%d")
    raw_dir.mkdir(parents=True, exist_ok=True)
    saved: dict[str, Path] = {}
    manifest = {
        "project": "Predicting Short-Term S&P 500 Volatility",
        "start_date": start_date,
        "end_date": end_date,
        "sources": {},
    }

    for spec in SOURCES:
        if spec.source == "yahoo":
            data = download_yahoo_chart(spec.symbol, start_date, end_date)
        elif spec.source == "fred":
            data = download_fred(spec.symbol, start_date, end_date)
        else:
            raise ValueError(f"Unsupported source type: {spec.source}")

        output_path = raw_dir / spec.filename
        data.to_csv(output_path, index=False)
        saved[spec.name] = output_path
        manifest["sources"][spec.name] = {
            "source": spec.source,
            "symbol": spec.symbol,
            "file": str(output_path.relative_to(raw_dir.parents[1])),
            "rows": int(len(data)),
            "columns": data.columns.tolist(),
            "min_date": str(pd.to_datetime(data.iloc[:, 0]).min().date()),
            "max_date": str(pd.to_datetime(data.iloc[:, 0]).max().date()),
        }

    manifest_path = raw_dir / "raw_data_manifest.json"
    write_json(manifest, manifest_path)
    saved["manifest"] = manifest_path
    return saved
