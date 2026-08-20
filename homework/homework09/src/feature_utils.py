"""Leakage-aware feature-engineering helpers for Stage 09."""

from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


def add_future_volatility_target(dataframe: pd.DataFrame, horizon: int = 5) -> pd.DataFrame:
    """Add forward realized volatility using returns strictly after each row's date."""
    engineered = dataframe.copy()
    returns = engineered["daily_return"]
    target_values = []
    for index in range(len(engineered)):
        future_window = returns.iloc[index + 1:index + 1 + horizon]
        if len(future_window) == horizon and future_window.notna().all():
            target_values.append(float(future_window.std(ddof=0)))
        else:
            target_values.append(np.nan)
    engineered["future_5d_realized_volatility"] = target_values
    return engineered


def create_time_series_features(dataframe: pd.DataFrame) -> Tuple[pd.DataFrame, List[str], Dict[str, Dict[str, str]]]:
    """Create price, return, volume, calendar, and interaction features without look-ahead."""
    engineered = dataframe.sort_values("date").copy().reset_index(drop=True)
    engineered.loc[engineered.index[0], "daily_return"] = np.nan

    prior_returns = engineered["daily_return"].shift(1)
    prior_volume = engineered["volume"].shift(1)
    prior_close = engineered["close"].shift(1)
    engineered["return_lag_1"] = prior_returns
    engineered["return_lag_3"] = engineered["daily_return"].shift(3)
    engineered["return_rolling_mean_3"] = prior_returns.rolling(window=3, min_periods=3).mean()
    engineered["return_rolling_volatility_5"] = prior_returns.rolling(window=5, min_periods=5).std(ddof=0)
    engineered["volume_pct_change_1"] = engineered["volume"].pct_change(fill_method=None)
    engineered["volume_relative_to_5d"] = engineered["volume"] / prior_volume.rolling(window=5, min_periods=5).mean()
    engineered["log_volume"] = np.log(engineered["volume"])
    engineered["close_relative_to_3d"] = engineered["close"] / prior_close.rolling(window=3, min_periods=3).mean() - 1
    engineered["day_of_week"] = engineered["date"].dt.day_name()

    weekday_features = pd.get_dummies(engineered["day_of_week"], prefix="weekday", dtype=int)
    engineered = pd.concat([engineered, weekday_features], axis=1)
    engineered["return_lag_1_x_volume_change_1"] = engineered["return_lag_1"] * engineered["volume_pct_change_1"]
    engineered = add_future_volatility_target(engineered, horizon=5)

    feature_columns = [
        "return_lag_1", "return_lag_3", "return_rolling_mean_3",
        "return_rolling_volatility_5", "volume_pct_change_1", "volume_relative_to_5d",
        "log_volume", "close_relative_to_3d", "return_lag_1_x_volume_change_1",
    ] + weekday_features.columns.tolist()

    registry = {
        "return_lag_1": {"definition": "Daily return at t-1", "lookback": "1 trading day"},
        "return_lag_3": {"definition": "Daily return at t-3", "lookback": "3 trading days"},
        "return_rolling_mean_3": {"definition": "Mean return from t-3 through t-1", "lookback": "3 trading days"},
        "return_rolling_volatility_5": {"definition": "Population standard deviation of returns from t-5 through t-1", "lookback": "5 trading days"},
        "volume_pct_change_1": {"definition": "Current volume change from t-1", "lookback": "1 trading day"},
        "volume_relative_to_5d": {"definition": "Current volume divided by mean volume from t-5 through t-1", "lookback": "5 trading days"},
        "log_volume": {"definition": "Natural logarithm of current volume", "lookback": "current observation"},
        "close_relative_to_3d": {"definition": "Current close relative to mean close from t-3 through t-1", "lookback": "3 trading days"},
        "return_lag_1_x_volume_change_1": {"definition": "Lagged return times current volume change", "lookback": "1 trading day"},
        "future_5d_realized_volatility": {"definition": "Population standard deviation of returns from t+1 through t+5", "lookback": "future target only"},
    }
    for column in weekday_features.columns:
        registry[column] = {"definition": "One-hot day-of-week calendar indicator", "lookback": "calendar at current observation"}
    return engineered, feature_columns, registry


def validate_model_ready_data(dataframe: pd.DataFrame, feature_columns: List[str]) -> Dict[str, bool]:
    """Validate feature completeness, finite numerics, chronology, and target constraints."""
    required = feature_columns + ["future_5d_realized_volatility"]
    checks = {
        "features_present": set(required).issubset(dataframe.columns),
        "no_missing_features_or_target": not dataframe[required].isna().any().any(),
        "finite_numeric_features": bool(np.isfinite(dataframe[required].select_dtypes(include=np.number)).all().all()),
        "dates_sorted": dataframe["date"].is_monotonic_increasing,
        "nonnegative_target": bool((dataframe["future_5d_realized_volatility"] >= 0).all()),
    }
    if not all(checks.values()):
        raise ValueError("Model-ready feature validation failed: {}".format(checks))
    return checks
