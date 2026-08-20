"""Reusable helpers for the Stage 03 homework."""

import pandas as pd


def get_summary_stats(df: pd.DataFrame, group_column: str) -> pd.DataFrame:
    """Return mean, median, minimum, and maximum numeric values by group.

    Parameters
    ----------
    df:
        Dataset containing a grouping column and numeric columns.
    group_column:
        Column used to split the data into groups.

    Returns
    -------
    pandas.DataFrame
        One row per group with flattened, descriptive column names.
    """
    if group_column not in df.columns:
        raise KeyError(f"'{group_column}' is not a column in the DataFrame.")

    numeric_columns = df.select_dtypes(include="number").columns.tolist()
    if not numeric_columns:
        raise ValueError("The DataFrame must contain at least one numeric column.")

    summary = df.groupby(group_column)[numeric_columns].agg(["mean", "median", "min", "max"])
    summary.columns = [f"{column}_{statistic}" for column, statistic in summary.columns]
    return summary.reset_index()
