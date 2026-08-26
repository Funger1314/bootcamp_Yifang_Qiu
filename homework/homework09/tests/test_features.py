from pathlib import Path
import sys

import pandas as pd


HOMEWORK_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOMEWORK_DIR / "src"))

from features import (  # noqa: E402
    TARGET_COLUMN,
    create_time_series_features,
    summarize_feature_target_relationships,
    validate_model_ready_data,
)


def _sample_prices() -> pd.DataFrame:
    dates = pd.bdate_range("2025-01-01", periods=14)
    close = [100, 101, 100, 102, 103, 101, 102, 104, 103, 105, 106, 104, 107, 108]
    volume = [
        1000,
        1100,
        1050,
        1250,
        1300,
        1500,
        1450,
        1600,
        1550,
        1700,
        1650,
        1800,
        1750,
        1900,
    ]
    frame = pd.DataFrame({"date": dates, "ticker": "^GSPC", "close": close, "volume": volume})
    frame["open"] = frame["close"]
    frame["high"] = frame["close"] + 1
    frame["low"] = frame["close"] - 1
    frame["daily_return"] = frame["close"].pct_change()
    return frame


def test_create_features_includes_categorical_encoding_and_target():
    engineered, feature_columns, registry = create_time_series_features(_sample_prices())

    assert TARGET_COLUMN in engineered.columns
    assert "return_rolling_volatility_5" in feature_columns
    assert "weekday_Wednesday" in feature_columns
    assert registry["weekday_Wednesday"]["eda_link"]
    assert registry["return_lag_1"]["rationale"]


def test_model_ready_validation_passes_after_expected_gaps_are_dropped():
    engineered, feature_columns, _ = create_time_series_features(_sample_prices())
    model_ready = engineered.dropna(subset=feature_columns + [TARGET_COLUMN]).copy()

    checks = validate_model_ready_data(model_ready, feature_columns)

    assert checks["features_present"]
    assert checks["no_missing_features_or_target"]
    assert checks["dates_sorted"]


def test_feature_target_relationship_summary_has_one_row_per_feature():
    engineered, feature_columns, _ = create_time_series_features(_sample_prices())
    model_ready = engineered.dropna(subset=feature_columns + [TARGET_COLUMN]).copy()

    summary = summarize_feature_target_relationships(model_ready, feature_columns)

    assert len(summary) == len(feature_columns)
    assert {"feature", "correlation_with_target", "interpretation"}.issubset(summary.columns)
