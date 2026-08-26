"""Reusable market-data preprocessing helpers for Stage 06."""

import pandas as pd

from .cleaning import drop_missing, fill_missing_median, normalize_data


PRICE_COLUMNS = ["open", "high", "low", "close", "volume"]


def missingness_summary(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Return missing counts and rates, sorted from most to least missing."""
    summary = pd.DataFrame({
        "missing_count": dataframe.isna().sum(),
        "missing_rate": dataframe.isna().mean(),
    })
    return summary.sort_values("missing_count", ascending=False)


def clean_market_prices(dataframe: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Apply the Stage 06 functions to market data and record decisions."""
    cleaned = dataframe.copy()
    decisions = {}

    cleaned["date"] = pd.to_datetime(cleaned["date"], errors="coerce")
    invalid_date_count = int(cleaned["date"].isna().sum())
    cleaned = drop_missing(cleaned, subset=["date"])
    cleaned = cleaned.sort_values("date").reset_index(drop=True)
    decisions["invalid_dates_dropped"] = invalid_date_count

    cleaned["ticker"] = cleaned["ticker"].astype("string").str.strip().str.upper().astype("category")
    for column in PRICE_COLUMNS:
        values = cleaned[column].astype("string").str.replace("$", "", regex=False).str.replace(",", "", regex=False)
        cleaned[column] = pd.to_numeric(values, errors="coerce")

    missing_before = {
        column: int(cleaned[column].isna().sum())
        for column in ["close", "volume"]
    }
    cleaned = fill_missing_median(cleaned, ["close", "volume"])
    decisions["median_values_filled"] = missing_before

    cleaned["daily_return"] = cleaned["close"].pct_change(fill_method=None).fillna(0.0)
    cleaned = normalize_data(cleaned, ["close"], method="minmax", suffix="_minmax")
    cleaned = normalize_data(cleaned, ["volume"], method="zscore", suffix="_zscore")
    decisions["normalization"] = {
        "close": "minmax",
        "volume": "zscore",
    }
    return cleaned, decisions


def validate_cleaned_prices(dataframe: pd.DataFrame) -> dict:
    """Validate the required schema and basic market-price quality rules."""
    required_columns = [
        "date", "ticker", "open", "high", "low", "close", "volume",
        "daily_return", "close_minmax", "volume_zscore",
    ]
    missing_columns = sorted(set(required_columns) - set(dataframe.columns))
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    checks = {
        "no_missing_values": not dataframe[required_columns].isna().any().any(),
        "date_is_datetime": pd.api.types.is_datetime64_any_dtype(dataframe["date"]),
        "close_is_numeric": pd.api.types.is_numeric_dtype(dataframe["close"]),
        "positive_prices": bool((dataframe[["open", "high", "low", "close"]] > 0).all().all()),
        "nonnegative_volume": bool((dataframe["volume"] >= 0).all()),
        "dates_sorted": dataframe["date"].is_monotonic_increasing,
    }
    if not all(checks.values()):
        raise ValueError(f"Cleaned-data validation failed: {checks}")
    return checks
