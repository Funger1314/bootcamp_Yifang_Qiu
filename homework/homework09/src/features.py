"""Feature engineering helpers for Stage 09.

The functions in this module create model-ready predictors from the cleaned
S&P 500 price series while keeping future information out of the feature set.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


TARGET_COLUMN = "future_5d_realized_volatility"


def add_future_volatility_target(dataframe: pd.DataFrame, horizon: int = 5) -> pd.DataFrame:
    """Add forward realized volatility from returns strictly after each row."""
    engineered = dataframe.copy()
    returns = engineered["daily_return"]
    target_values = []

    for index in range(len(engineered)):
        future_window = returns.iloc[index + 1 : index + 1 + horizon]
        if len(future_window) == horizon and future_window.notna().all():
            target_values.append(float(future_window.std(ddof=0)))
        else:
            target_values.append(np.nan)

    engineered[TARGET_COLUMN] = target_values
    return engineered


def create_time_series_features(
    dataframe: pd.DataFrame,
) -> Tuple[pd.DataFrame, List[str], Dict[str, Dict[str, str]]]:
    """Create return, volume, price, calendar, and interaction features."""
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
        "return_lag_1",
        "return_lag_3",
        "return_rolling_mean_3",
        "return_rolling_volatility_5",
        "volume_pct_change_1",
        "volume_relative_to_5d",
        "log_volume",
        "close_relative_to_3d",
        "return_lag_1_x_volume_change_1",
    ] + weekday_features.columns.tolist()

    registry = build_feature_registry(weekday_features.columns.tolist())
    return engineered, feature_columns, registry


def build_feature_registry(weekday_columns: List[str]) -> Dict[str, Dict[str, str]]:
    """Describe each engineered feature, its EDA link, and leakage boundary."""
    registry = {
        "return_lag_1": {
            "definition": "Daily return at t-1.",
            "rationale": "Stage 08 showed daily returns move around a near-zero center, so yesterday's return may summarize recent momentum or reversal pressure.",
            "eda_link": "Stage 08 return distribution and time-series plot.",
            "leakage_note": "Uses only the previous trading day's return.",
        },
        "return_lag_3": {
            "definition": "Daily return at t-3.",
            "rationale": "Adds short-memory return behavior without duplicating the one-day lag.",
            "eda_link": "Stage 08 time-series movement in daily returns.",
            "leakage_note": "Uses only the return three trading days before date t.",
        },
        "return_rolling_mean_3": {
            "definition": "Mean return from t-3 through t-1.",
            "rationale": "Smooths noisy daily returns into a recent directional signal.",
            "eda_link": "Stage 08 found return volatility and short sample swings, making a smoothed signal more stable than a single return.",
            "leakage_note": "Returns are shifted before rolling, so the current and future returns are excluded.",
        },
        "return_rolling_volatility_5": {
            "definition": "Population standard deviation of returns from t-5 through t-1.",
            "rationale": "Recent realized volatility is a natural predictor for near-future volatility clustering.",
            "eda_link": "Stage 08 distribution and boxplot highlighted variation in daily returns.",
            "leakage_note": "Uses only prior returns.",
        },
        "volume_pct_change_1": {
            "definition": "Current volume percent change from t-1.",
            "rationale": "Sudden activity changes can coincide with market stress or information arrival.",
            "eda_link": "Stage 08 volume distribution showed variation across trading days.",
            "leakage_note": "Uses current volume and the previous day's volume, both available at date t close.",
        },
        "volume_relative_to_5d": {
            "definition": "Current volume divided by mean volume from t-5 through t-1.",
            "rationale": "Compares today's trading activity with recent baseline activity.",
            "eda_link": "Stage 08 volume analysis suggested scale differences that are easier to interpret as a relative measure.",
            "leakage_note": "The comparison baseline uses only prior volume.",
        },
        "log_volume": {
            "definition": "Natural logarithm of current volume.",
            "rationale": "Reduces the scale of large volume counts while preserving order.",
            "eda_link": "Stage 08 descriptive statistics showed volume is much larger in scale than return features.",
            "leakage_note": "Uses only current-date volume.",
        },
        "close_relative_to_3d": {
            "definition": "Current close relative to the mean close from t-3 through t-1.",
            "rationale": "Measures whether price is extended relative to a short prior baseline.",
            "eda_link": "Stage 08 price trend plot showed short-run level changes.",
            "leakage_note": "The denominator uses only prior closes.",
        },
        "return_lag_1_x_volume_change_1": {
            "definition": "Lagged return multiplied by current one-day volume change.",
            "rationale": "Combines direction and activity, allowing high-volume moves to carry different information than quiet moves.",
            "eda_link": "Stage 08 bivariate checks considered return, volume, and price relationships.",
            "leakage_note": "Uses lagged return and current volume change only.",
        },
        TARGET_COLUMN: {
            "definition": "Population standard deviation of returns from t+1 through t+5.",
            "rationale": "Target for later supervised modeling, not an input feature.",
            "eda_link": "Stage 08 framed future volatility as the likely modeling target.",
            "leakage_note": "Future-only calculation is excluded from predictors.",
        },
    }

    for column in weekday_columns:
        weekday = column.replace("weekday_", "")
        registry[column] = {
            "definition": f"One-hot indicator for {weekday}.",
            "rationale": "Encodes the categorical day-of-week field required by the assignment and tests whether weekday patterns carry signal.",
            "eda_link": "Stage 08 noted the sample is chronological and short, so calendar effects must be treated as tentative.",
            "leakage_note": "Calendar information is known at date t.",
        }

    return registry


def summarize_feature_target_relationships(
    dataframe: pd.DataFrame,
    feature_columns: List[str],
    target_column: str = TARGET_COLUMN,
) -> pd.DataFrame:
    """Return per-feature correlation checks against the target."""
    rows = []
    for feature in feature_columns:
        pair = dataframe[[feature, target_column]].dropna()
        correlation = pair[feature].corr(pair[target_column]) if pair[feature].nunique() > 1 else np.nan
        rows.append(
            {
                "feature": feature,
                "correlation_with_target": correlation,
                "absolute_correlation": abs(correlation) if pd.notna(correlation) else np.nan,
                "n_observations": int(len(pair)),
                "interpretation": _interpret_correlation(feature, correlation, len(pair)),
            }
        )

    return pd.DataFrame(rows).sort_values("absolute_correlation", ascending=False, na_position="last")


def _interpret_correlation(feature: str, correlation: float, n_observations: int) -> str:
    """Convert a small-sample correlation into a cautious sentence."""
    if pd.isna(correlation):
        return f"{feature} has no usable variation in the model-ready sample."

    direction = "positive" if correlation > 0 else "negative"
    strength = "strong" if abs(correlation) >= 0.7 else "moderate" if abs(correlation) >= 0.4 else "weak"
    return (
        f"{feature} has a {strength} {direction} sample correlation with the target "
        f"(n={n_observations}); treat this as screening evidence, not proof."
    )


def validate_model_ready_data(dataframe: pd.DataFrame, feature_columns: List[str]) -> Dict[str, bool]:
    """Validate feature completeness, finite numerics, chronology, and target values."""
    required = feature_columns + [TARGET_COLUMN]
    numeric_required = dataframe[required].select_dtypes(include=np.number)
    checks = {
        "features_present": set(required).issubset(dataframe.columns),
        "no_missing_features_or_target": not dataframe[required].isna().any().any(),
        "finite_numeric_features": bool(np.isfinite(numeric_required).all().all()),
        "dates_sorted": bool(dataframe["date"].is_monotonic_increasing),
        "nonnegative_target": bool((dataframe[TARGET_COLUMN] >= 0).all()),
    }
    if not all(checks.values()):
        raise ValueError(f"Model-ready feature validation failed: {checks}")
    return checks
