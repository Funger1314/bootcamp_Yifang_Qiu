"""Reusable exploratory-data-analysis helpers for Stage 08."""

from typing import Iterable, Optional

import numpy as np
import pandas as pd


def eda_summary(
    dataframe: pd.DataFrame,
    numeric_columns: Optional[Iterable[str]] = None,
    categorical_columns: Optional[Iterable[str]] = None,
) -> dict:
    """Return numeric, categorical, missingness, and attention summaries.

    Parameters
    ----------
    dataframe:
        Data to profile. The function does not mutate the input.
    numeric_columns:
        Numeric columns to include. By default all numeric columns are used.
    categorical_columns:
        Categorical columns to include. By default object, string, category,
        and boolean columns are used; datetime columns remain temporal fields.

    Returns
    -------
    dict
        Shape, dtypes, missing counts, numeric statistics, categorical value
        counts and proportions, and simple flags for missingness, skewness,
        and potential IQR outliers.
    """
    if numeric_columns is None:
        numeric_columns = dataframe.select_dtypes(include=np.number).columns
    if categorical_columns is None:
        categorical_columns = dataframe.select_dtypes(
            include=["object", "string", "category", "bool"]
        ).columns

    numeric_columns = list(numeric_columns)
    categorical_columns = list(categorical_columns)
    numeric_profile = dataframe[numeric_columns].describe().T
    numeric_profile["skew"] = dataframe[numeric_columns].skew()
    numeric_profile["kurtosis"] = dataframe[numeric_columns].kurtosis()

    categorical_profile = {}
    for column in categorical_columns:
        counts = dataframe[column].value_counts(dropna=False)
        categorical_profile[column] = pd.DataFrame(
            {
                "count": counts,
                "proportion": dataframe[column].value_counts(
                    dropna=False, normalize=True
                ),
            }
        )

    attention_flags = {}
    for column in numeric_columns:
        series = dataframe[column].dropna()
        q1, q3 = series.quantile([0.25, 0.75])
        iqr = q3 - q1
        outlier_count = int(
            ((series < q1 - 1.5 * iqr) | (series > q3 + 1.5 * iqr)).sum()
        )
        attention_flags[column] = {
            "missing_count": int(dataframe[column].isna().sum()),
            "absolute_skew_over_1": bool(abs(series.skew()) > 1),
            "iqr_outlier_count": outlier_count,
        }

    return {
        "shape": dataframe.shape,
        "dtypes": {column: str(dtype) for column, dtype in dataframe.dtypes.items()},
        "missing": dataframe.isna().sum().to_dict(),
        "numeric_profile": numeric_profile,
        "categorical_profile": categorical_profile,
        "attention_flags": attention_flags,
    }


def correlation_matrix(dataframe: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    """Return a Pearson correlation matrix for selected numeric columns."""
    return dataframe[list(columns)].corr(numeric_only=True)


def strongest_pairwise_correlation(
    correlation: pd.DataFrame,
) -> tuple[str, str, float]:
    """Return the strongest non-diagonal absolute correlation."""
    values = correlation.to_numpy(dtype=float, copy=True)
    np.fill_diagonal(values, np.nan)
    matrix = pd.DataFrame(values, index=correlation.index, columns=correlation.columns)
    row, column = matrix.abs().stack().idxmax()
    return row, column, float(correlation.loc[row, column])
