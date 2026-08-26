"""Reusable Stage 07 outlier-analysis package."""

from .outliers import (
    detect_outliers_iqr,
    detect_outliers_zscore,
    iqr_bounds,
    winsorize_series,
)

__all__ = [
    "detect_outliers_iqr",
    "detect_outliers_zscore",
    "iqr_bounds",
    "winsorize_series",
]
