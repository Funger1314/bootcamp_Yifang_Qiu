"""Backward-compatible Stage 07 helpers.

New work should import the required functions from :mod:`src.outliers`. This
module remains so previously executed downstream notebooks do not break.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score

try:
    from .outliers import (
        detect_outliers_iqr,
        detect_outliers_zscore,
        iqr_bounds,
        winsorize_series,
    )
except ImportError:  # Supports legacy ``sys.path`` imports from this folder.
    from outliers import (  # type: ignore[no-redef]
        detect_outliers_iqr,
        detect_outliers_zscore,
        iqr_bounds,
        winsorize_series,
    )


def fit_return_sensitivity(
    dataframe: pd.DataFrame,
    target_column: str = "daily_return",
) -> dict[str, float | int]:
    """Fit a descriptive volume-to-return regression and return diagnostics."""

    required = {"volume_zscore", target_column}
    missing = sorted(required - set(dataframe.columns))
    if missing:
        raise KeyError(f"Missing required columns: {missing}")
    if len(dataframe) < 2:
        raise ValueError("At least two observations are required")
    if dataframe[list(required)].isna().any().any():
        raise ValueError("Regression columns must not contain missing values")

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
