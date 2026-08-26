"""Validated, non-mutating outlier functions for Stage 07.

The public function signatures match the homework starter notebook. Missing
values are never classified as outliers, and every function preserves the
input index so masks can be assigned safely back to the source DataFrame.
"""

from __future__ import annotations

import math

import pandas as pd


def _validate_series(series: pd.Series) -> pd.Series:
    """Return a numeric Series after validating its type and usable values."""

    if not isinstance(series, pd.Series):
        raise TypeError("series must be a pandas Series")
    if not pd.api.types.is_numeric_dtype(series):
        raise TypeError("series must contain numeric values")
    if series.dropna().empty:
        raise ValueError("series must contain at least one non-missing value")
    return series


def _validate_positive(value: float, name: str) -> float:
    """Validate a finite, strictly positive numeric parameter."""

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be numeric")
    if not math.isfinite(float(value)) or value <= 0:
        raise ValueError(f"{name} must be finite and greater than zero")
    return float(value)


def iqr_bounds(series: pd.Series, k: float = 1.5) -> tuple[float, float]:
    """Calculate Tukey lower and upper fences for a numeric Series.

    Parameters
    ----------
    series:
        Numeric observations. Missing values are ignored when estimating the
        quartiles.
    k:
        Positive multiplier applied to the interquartile range. The conventional
        exploratory default is 1.5.

    Returns
    -------
    tuple[float, float]
        Lower and upper Tukey fences.

    Raises
    ------
    TypeError
        If the input is not a numeric pandas Series or ``k`` is not numeric.
    ValueError
        If the Series has no observed values or ``k`` is not positive and finite.
    """

    validated = _validate_series(series)
    multiplier = _validate_positive(k, "k")
    q1, q3 = validated.quantile([0.25, 0.75])
    iqr = q3 - q1
    return float(q1 - multiplier * iqr), float(q3 + multiplier * iqr)


def detect_outliers_iqr(series: pd.Series, k: float = 1.5) -> pd.Series:
    """Return a boolean mask for observations outside Tukey IQR fences.

    Parameters
    ----------
    series:
        Numeric observations. Missing values are returned as ``False`` because
        missingness is a separate data-quality condition, not an outlier.
    k:
        Positive IQR multiplier controlling strictness; larger values flag fewer
        observations.

    Returns
    -------
    pandas.Series
        Boolean mask with the same index as ``series``.

    Notes
    -----
    IQR detection is robust to extreme observations but is sample- and
    threshold-dependent. A flagged value can be a valid stress event rather
    than a data error.
    """

    lower, upper = iqr_bounds(series, k=k)
    return ((series < lower) | (series > upper)).fillna(False).astype(bool)


def detect_outliers_zscore(
    series: pd.Series,
    threshold: float = 3.0,
) -> pd.Series:
    """Return a boolean mask where absolute population Z-score exceeds a threshold.

    Parameters
    ----------
    series:
        Numeric observations. Missing values are returned as ``False``.
    threshold:
        Positive absolute Z-score cutoff. A conventional exploratory value is 3.

    Returns
    -------
    pandas.Series
        Boolean mask with the same index as ``series``.

    Notes
    -----
    Population standard deviation (``ddof=0``) is used because this synthetic
    assignment dataset is treated as the complete analysis sample. Z-scores are
    sensitive to heavy tails because extreme values affect both mean and scale.
    A constant Series returns an all-False mask.
    """

    validated = _validate_series(series)
    cutoff = _validate_positive(threshold, "threshold")
    standard_deviation = validated.std(ddof=0, skipna=True)
    if standard_deviation == 0:
        return pd.Series(False, index=validated.index, dtype=bool)
    z_scores = (validated - validated.mean(skipna=True)) / standard_deviation
    return (z_scores.abs() > cutoff).fillna(False).astype(bool)


def winsorize_series(
    series: pd.Series,
    lower: float = 0.05,
    upper: float = 0.95,
) -> pd.Series:
    """Clip observations to selected lower and upper sample quantiles.

    Parameters
    ----------
    series:
        Numeric observations. Missing values remain missing.
    lower:
        Lower quantile in the closed interval [0, 1).
    upper:
        Upper quantile in the interval (0, 1], strictly above ``lower``.

    Returns
    -------
    pandas.Series
        A clipped copy with the same name and index as ``series``.

    Raises
    ------
    ValueError
        If the quantiles are outside [0, 1] or are not strictly ordered.

    Notes
    -----
    Winsorization retains every row but changes tail values. It should be
    presented as a sensitivity treatment, not as proof that extremes are errors.
    """

    validated = _validate_series(series)
    for value, name in ((lower, "lower"), (upper, "upper")):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"{name} must be numeric")
        if not math.isfinite(float(value)) or not 0 <= value <= 1:
            raise ValueError(f"{name} must be finite and between zero and one")
    if lower >= upper:
        raise ValueError("lower must be strictly less than upper")

    lower_value, upper_value = validated.quantile([lower, upper])
    return validated.clip(lower=lower_value, upper=upper_value)
