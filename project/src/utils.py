
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def clean_column_names(df):
    """
    Clean DataFrame column names.

    Converts column names to lowercase, removes leading/trailing
    whitespace, and replaces spaces with underscores.

    Parameters
    ----------
    df : pandas.DataFrame
        Input DataFrame.

    Returns
    -------
    pandas.DataFrame
        DataFrame with cleaned column names.
    """

    df = df.copy()

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    return df
def parse_date_column(df, column="date"):
    """
    Convert a DataFrame column to pandas datetime format.

    Parameters
    ----------
    df : pandas.DataFrame
        Input DataFrame.

    column : str
        Name of the date column.

    Returns
    -------
    pandas.DataFrame
        DataFrame with parsed datetime column.
    """

    df = df.copy()

    df[column] = pd.to_datetime(df[column])

    return df


def ensure_directory(path: str | Path) -> Path:
    """Create a directory if needed and return it as a ``Path``."""

    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def write_json(data: dict, path: str | Path) -> Path:
    """Write a JSON file with stable formatting."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    return output_path


def read_json(path: str | Path) -> dict:
    """Read a UTF-8 JSON file."""

    return json.loads(Path(path).read_text(encoding="utf-8"))


def assert_columns(dataframe: pd.DataFrame, columns: list[str]) -> None:
    """Raise a helpful error when required columns are missing."""

    missing = sorted(set(columns) - set(dataframe.columns))
    if missing:
        raise KeyError(f"Missing required columns: {missing}")
