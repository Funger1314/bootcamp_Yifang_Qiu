"""Outlier detection and treatment-comparison helpers for Stage 07."""

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score


def iqr_bounds(series: pd.Series, multiplier: float = 1.5) -> tuple[float, float]:
    """Return lower and upper Tukey-IQR fences for a numeric Series."""
    q1, q3 = series.quantile([0.25, 0.75])
    iqr = q3 - q1
    return float(q1 - multiplier * iqr), float(q3 + multiplier * iqr)


def detect_outliers_iqr(series: pd.Series, multiplier: float = 1.5) -> pd.Series:
    """Return a boolean mask for values outside Tukey-IQR fences."""
    lower, upper = iqr_bounds(series, multiplier)
    return (series < lower) | (series > upper)


def detect_outliers_zscore(series: pd.Series, threshold: float = 3.0) -> pd.Series:
    """Return a boolean mask where the absolute population Z-score exceeds a threshold."""
    standard_deviation = series.std(ddof=0)
    if standard_deviation == 0 or pd.isna(standard_deviation):
        return pd.Series(False, index=series.index)
    z_scores = (series - series.mean()) / standard_deviation
    return z_scores.abs() > threshold


def winsorize_series(series: pd.Series, lower_quantile: float = 0.05, upper_quantile: float = 0.95) -> pd.Series:
    """Clip a Series to lower and upper quantiles without removing rows."""
    lower, upper = series.quantile([lower_quantile, upper_quantile])
    return series.clip(lower=lower, upper=upper)


def fit_return_sensitivity(dataframe: pd.DataFrame, target_column: str = "daily_return") -> dict:
    """Fit a simple volume-to-return regression and return in-sample diagnostics."""
    if len(dataframe) < 2:
        raise ValueError("At least two observations are required for sensitivity analysis.")

    features = dataframe[["volume_zscore"]].to_numpy()
    target = dataframe[target_column].to_numpy()
    model = LinearRegression().fit(features, target)
    predicted = model.predict(features)
    return {
        "observations": int(len(dataframe)),
        "slope": float(model.coef_[0]),
        "intercept": float(model.intercept_),
        "r2": float(r2_score(target, predicted)),
        "mae": float(mean_absolute_error(target, predicted)),
        "return_mean": float(np.mean(target)),
        "return_std": float(np.std(target, ddof=0)),
    }
