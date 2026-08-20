"""Reusable exploratory-data-analysis helpers for Stage 08."""

import numpy as np
import pandas as pd
from scipy.stats import kurtosis, skew
from typing import List, Optional


def eda_summary(dataframe: pd.DataFrame, numeric_columns: Optional[List[str]] = None) -> dict:
    """Return data shape, dtypes, missingness, and numeric profile statistics."""
    if numeric_columns is None:
        numeric_columns = dataframe.select_dtypes(include=np.number).columns.tolist()

    profile = dataframe[numeric_columns].describe().T
    profile["skew"] = [skew(dataframe[column].dropna()) for column in profile.index]
    profile["kurtosis"] = [kurtosis(dataframe[column].dropna()) for column in profile.index]
    return {
        "shape": dataframe.shape,
        "dtypes": {column: str(dtype) for column, dtype in dataframe.dtypes.items()},
        "missing": dataframe.isna().sum().to_dict(),
        "numeric_profile": profile,
    }


def correlation_matrix(dataframe: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """Return a Pearson correlation matrix for explicitly selected numeric columns."""
    return dataframe[columns].corr(numeric_only=True)


def strongest_pairwise_correlation(correlation: pd.DataFrame) -> tuple[str, str, float]:
    """Return the strongest non-diagonal absolute correlation from a square matrix."""
    matrix = correlation.copy()
    np.fill_diagonal(matrix.values, np.nan)
    row, column = matrix.abs().stack().idxmax()
    return row, column, float(correlation.loc[row, column])
