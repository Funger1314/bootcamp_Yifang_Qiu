"""Leakage-safe feature engineering for future S&P 500 volatility."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.config import PROCESSED_DATA_DIR
from src.outliers import add_stress_flags, flag_iqr_outliers


TARGET_COLUMN = "future_5d_realized_volatility"


BASE_FEATURES = [
    "sp500_return_lag_1",
    "sp500_return_lag_3",
    "sp500_return_rolling_mean_5",
    "realized_volatility_5d",
    "realized_volatility_10d",
    "realized_volatility_21d",
    "vix_close",
    "vix_change",
    "vix_pct_change",
    "treasury_10y",
    "treasury_2y",
    "yield_spread_10y_2y",
    "yield_spread_change_5d",
    "vix_x_realized_vol_5d",
]


FEATURE_RATIONALE = {
    "sp500_return_lag_1": "Captures very recent market direction known at date t.",
    "sp500_return_lag_3": "Adds short-memory return behavior without using future returns.",
    "sp500_return_rolling_mean_5": "Smooths noisy recent returns into a five-day directional signal.",
    "realized_volatility_5d": "Naive volatility persistence benchmark and core risk state variable.",
    "realized_volatility_10d": "Captures slightly slower volatility clustering.",
    "realized_volatility_21d": "Approximates one trading month of recent volatility.",
    "vix_close": "Market-implied stress indicator observable at date t.",
    "vix_change": "Recent change in market-implied stress.",
    "vix_pct_change": "Scale-adjusted change in market-implied stress.",
    "treasury_10y": "Long-rate level as macro/discount-rate context.",
    "treasury_2y": "Short-rate/policy-sensitive yield context.",
    "yield_spread_10y_2y": "Term-structure slope, a macro stress and cycle proxy.",
    "yield_spread_change_5d": "Recent movement in the term-structure slope.",
    "vix_x_realized_vol_5d": "Interaction between implied and realized volatility regimes.",
}


def add_realized_volatility(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Add realized volatility features using only information through date t."""

    data = dataframe.sort_values("date").copy().reset_index(drop=True)
    for window in [5, 10, 21]:
        data[f"realized_volatility_{window}d"] = data["sp500_return"].rolling(window=window, min_periods=window).std(ddof=0)
    return data


def add_future_target(dataframe: pd.DataFrame, horizon: int = 5) -> pd.DataFrame:
    """Add future realized volatility from returns t+1 through t+horizon."""

    data = dataframe.copy()
    future_values: list[float] = []
    returns = data["sp500_return"]
    for idx in range(len(data)):
        future_window = returns.iloc[idx + 1 : idx + 1 + horizon]
        if len(future_window) == horizon and future_window.notna().all():
            future_values.append(float(future_window.std(ddof=0)))
        else:
            future_values.append(np.nan)
    data[TARGET_COLUMN] = future_values
    return data


def build_features(cleaned: pd.DataFrame) -> tuple[pd.DataFrame, list[str], pd.DataFrame]:
    """Create model-ready features, target, stress flags, and feature registry."""

    data = add_realized_volatility(cleaned)
    data["sp500_return_lag_1"] = data["sp500_return"].shift(1)
    data["sp500_return_lag_3"] = data["sp500_return"].shift(3)
    data["sp500_return_rolling_mean_5"] = data["sp500_return"].shift(1).rolling(5, min_periods=5).mean()
    data["yield_spread_change_5d"] = data["yield_spread_10y_2y"].diff(5)
    data["vix_x_realized_vol_5d"] = data["vix_close"] * data["realized_volatility_5d"]
    data = add_future_target(data, horizon=5)
    data = flag_iqr_outliers(data, "sp500_return", k=3.0, flag_name="sp500_return_iqr_outlier")
    data = flag_iqr_outliers(data, "realized_volatility_5d", k=3.0, flag_name="realized_volatility_iqr_outlier")
    data = add_stress_flags(data)

    model_ready = data.dropna(subset=BASE_FEATURES + [TARGET_COLUMN]).reset_index(drop=True)
    if len(model_ready) < 500:
        raise ValueError(f"Model-ready dataset too small: {len(model_ready)} rows")

    registry = pd.DataFrame(
        [
            {
                "feature": feature,
                "rationale": FEATURE_RATIONALE[feature],
                "leakage_boundary": "Uses only information observable at or before prediction date t.",
            }
            for feature in BASE_FEATURES
        ]
    )
    registry.loc[len(registry)] = {
        "feature": TARGET_COLUMN,
        "rationale": "Continuous target: realized S&P 500 volatility over the next five trading days.",
        "leakage_boundary": "Computed from t+1 through t+5 and never used as an input feature.",
    }
    return model_ready, BASE_FEATURES.copy(), registry


def save_feature_outputs(
    model_ready: pd.DataFrame,
    feature_registry: pd.DataFrame,
    processed_dir: Path = PROCESSED_DATA_DIR,
) -> dict[str, Path]:
    """Save model-ready data and feature documentation."""

    processed_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "model_ready_csv": processed_dir / "model_ready_volatility.csv",
        "feature_registry": processed_dir / "feature_registry.csv",
    }
    model_ready.to_csv(outputs["model_ready_csv"], index=False)
    feature_registry.to_csv(outputs["feature_registry"], index=False)
    return outputs
