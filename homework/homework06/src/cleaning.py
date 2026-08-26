"""General-purpose, non-mutating data-cleaning functions for Stage 06.

Each public function returns a new ``pandas.DataFrame`` so callers can compare
intermediate results with the original data without accidental mutation.
"""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd


def _require_columns(dataframe: pd.DataFrame, columns: Sequence[str]) -> list[str]:
    """Validate a column selection and return it as a list."""

    selected = list(columns)
    missing = sorted(set(selected) - set(dataframe.columns))
    if missing:
        raise KeyError(f"Columns not found: {missing}")
    return selected


def fill_missing_median(
    dataframe: pd.DataFrame,
    columns: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Fill missing values in selected numeric columns with column medians.

    Parameters
    ----------
    dataframe:
        Input data. It is never modified in place.
    columns:
        Numeric columns to impute. When omitted, every numeric column is used.

    Returns
    -------
    pandas.DataFrame
        A copy containing the median-filled values.

    Raises
    ------
    KeyError
        If a requested column does not exist.
    TypeError
        If a requested column is not numeric.
    ValueError
        If a selected column has missing values but no finite median because
        the column contains only missing values.

    Notes
    -----
    Median imputation is deterministic and resistant to extreme values, but it
    reduces observed variability and does not model time-series continuity.
    """

    cleaned = dataframe.copy(deep=True)
    selected = (
        list(cleaned.select_dtypes(include="number").columns)
        if columns is None
        else _require_columns(cleaned, columns)
    )

    for column in selected:
        if not pd.api.types.is_numeric_dtype(cleaned[column]):
            raise TypeError(f"Median imputation requires a numeric column: {column}")
        median = cleaned[column].median(skipna=True)
        if cleaned[column].isna().any() and pd.isna(median):
            raise ValueError(f"Cannot compute a median for all-missing column: {column}")
        cleaned[column] = cleaned[column].fillna(median)

    return cleaned


def drop_missing(
    dataframe: pd.DataFrame,
    subset: Sequence[str] | None = None,
    *,
    how: str = "any",
    threshold: float | None = None,
) -> pd.DataFrame:
    """Drop rows with missing critical values or overly sparse columns.

    Parameters
    ----------
    dataframe:
        Input data. It is never modified in place.
    subset:
        Columns used for row deletion. With no ``subset`` and no ``threshold``,
        rows missing any value are removed.
    how:
        Row rule passed to ``DataFrame.dropna``: ``"any"`` or ``"all"``.
    threshold:
        Optional maximum allowed missing fraction for a column, between 0 and
        1. Columns with a strictly larger missing fraction are removed. When
        supplied without ``subset``, only column deletion is performed.

    Returns
    -------
    pandas.DataFrame
        A reset-index copy after the documented deletion rule.

    Raises
    ------
    KeyError
        If a requested subset column does not exist.
    ValueError
        If ``how`` or ``threshold`` is outside its accepted values.

    Notes
    -----
    Deletion can bias results when missingness is systematic. It should be
    limited to fields that are essential and cannot be reconstructed, such as
    an invalid date in a chronological dataset.
    """

    if how not in {"any", "all"}:
        raise ValueError("how must be either 'any' or 'all'")
    if threshold is not None and not 0 <= threshold <= 1:
        raise ValueError("threshold must be between 0 and 1")

    cleaned = dataframe.copy(deep=True)
    selected = None if subset is None else _require_columns(cleaned, subset)

    if threshold is not None:
        missing_rates = cleaned.isna().mean()
        cleaned = cleaned.loc[:, missing_rates <= threshold].copy()
        if selected is None:
            return cleaned.reset_index(drop=True)
        removed_subset = sorted(set(selected) - set(cleaned.columns))
        if removed_subset:
            raise ValueError(
                "threshold removed columns required by subset: "
                f"{removed_subset}"
            )

    return cleaned.dropna(subset=selected, how=how).reset_index(drop=True)


def normalize_data(
    dataframe: pd.DataFrame,
    columns: Sequence[str],
    *,
    method: str = "minmax",
    suffix: str = "_normalized",
) -> pd.DataFrame:
    """Add normalized versions of selected numeric columns.

    Parameters
    ----------
    dataframe:
        Input data. It is never modified in place.
    columns:
        Numeric columns to scale.
    method:
        ``"minmax"`` maps values to [0, 1]. ``"zscore"`` centers values at
        zero with population standard deviation one.
    suffix:
        Suffix appended to each source column for the derived feature.

    Returns
    -------
    pandas.DataFrame
        A copy with one derived normalized column per selected source column.

    Raises
    ------
    KeyError
        If a requested column does not exist.
    TypeError
        If a requested column is not numeric.
    ValueError
        If the method is unsupported or a selected column still has missing
        values. Constant columns are safely mapped to 0.0.

    Notes
    -----
    Scaling parameters are estimated from the supplied data. In a real model,
    call this function on training data only and reuse the fitted parameters on
    validation/test data to avoid leakage.
    """

    if method not in {"minmax", "zscore"}:
        raise ValueError("method must be either 'minmax' or 'zscore'")

    normalized = dataframe.copy(deep=True)
    selected = _require_columns(normalized, columns)

    for column in selected:
        series = normalized[column]
        if not pd.api.types.is_numeric_dtype(series):
            raise TypeError(f"Normalization requires a numeric column: {column}")
        if series.isna().any():
            raise ValueError(f"Fill or drop missing values before normalizing: {column}")

        if method == "minmax":
            minimum = series.min()
            spread = series.max() - minimum
            scaled = pd.Series(0.0, index=series.index) if spread == 0 else (series - minimum) / spread
        else:
            mean = series.mean()
            standard_deviation = series.std(ddof=0)
            scaled = (
                pd.Series(0.0, index=series.index)
                if standard_deviation == 0
                else (series - mean) / standard_deviation
            )

        normalized[f"{column}{suffix}"] = scaled.astype(float)

    return normalized
