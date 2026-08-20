"""Reusable market-data preprocessing helpers for Stage 06."""

import pandas as pd
from sklearn.preprocessing import MinMaxScaler, StandardScaler


PRICE_COLUMNS = ["open", "high", "low", "close", "volume"]


def missingness_summary(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Return missing counts and rates, sorted from most to least missing."""
    summary = pd.DataFrame({
        "missing_count": dataframe.isna().sum(),
        "missing_rate": dataframe.isna().mean(),
    })
    return summary.sort_values("missing_count", ascending=False)


def clean_market_prices(dataframe: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Correct common market-data types and apply documented missing-data rules."""
    cleaned = dataframe.copy()
    decisions = {}

    cleaned["date"] = pd.to_datetime(cleaned["date"], errors="coerce")
    invalid_date_count = int(cleaned["date"].isna().sum())
    cleaned = cleaned.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    decisions["invalid_dates_dropped"] = invalid_date_count

    cleaned["ticker"] = cleaned["ticker"].astype("string").str.strip().str.upper().astype("category")
    for column in PRICE_COLUMNS:
        values = cleaned[column].astype("string").str.replace("$", "", regex=False).str.replace(",", "", regex=False)
        cleaned[column] = pd.to_numeric(values, errors="coerce")

    close_missing = int(cleaned["close"].isna().sum())
    cleaned = cleaned.set_index("date")
    cleaned["close"] = cleaned["close"].interpolate(method="time")
    cleaned = cleaned.reset_index()
    decisions["close_missing_interpolated"] = close_missing

    volume_missing = int(cleaned["volume"].isna().sum())
    cleaned["volume"] = cleaned["volume"].fillna(cleaned["volume"].median())
    decisions["volume_missing_median_filled"] = volume_missing

    cleaned["daily_return"] = cleaned["close"].pct_change(fill_method=None).fillna(0.0)
    cleaned["close_minmax"] = MinMaxScaler().fit_transform(cleaned[["close"]])
    cleaned["volume_zscore"] = StandardScaler().fit_transform(cleaned[["volume"]])
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
