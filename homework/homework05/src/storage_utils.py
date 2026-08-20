"""Format-aware DataFrame storage helpers for Stage 05."""

from pathlib import Path
from typing import Union

import pandas as pd


PathLike = Union[str, Path]


def ensure_parent_dir(path: PathLike) -> Path:
    """Create the parent directory for a file path and return the path."""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    return file_path


def detect_format(path: PathLike) -> str:
    """Return the supported storage format inferred from a file suffix."""
    suffix = Path(path).suffix.lower()
    if suffix == ".csv":
        return "csv"
    if suffix in {".parquet", ".pq", ".parq"}:
        return "parquet"
    raise ValueError(f"Unsupported format: {path}")


def write_dataframe(dataframe: pd.DataFrame, path: PathLike) -> Path:
    """Write a DataFrame as CSV or Parquet, selected from its suffix."""
    file_path = ensure_parent_dir(path)
    if detect_format(file_path) == "csv":
        dataframe.to_csv(file_path, index=False)
    else:
        dataframe.to_parquet(file_path, index=False)
    return file_path


def read_dataframe(path: PathLike) -> pd.DataFrame:
    """Read a CSV or Parquet DataFrame and parse a date column when present."""
    file_path = Path(path)
    if detect_format(file_path) == "csv":
        columns = pd.read_csv(file_path, nrows=0).columns
        return pd.read_csv(file_path, parse_dates=["date"] if "date" in columns else None)
    return pd.read_parquet(file_path)


def validate_round_trip(original: pd.DataFrame, reloaded: pd.DataFrame) -> dict:
    """Return checks for shape, column order, dates, and numeric price values."""
    checks = {
        "shape_equal": original.shape == reloaded.shape,
        "columns_equal": list(original.columns) == list(reloaded.columns),
        "date_is_datetime": "date" not in reloaded or pd.api.types.is_datetime64_any_dtype(reloaded["date"]),
        "close_is_numeric": "close" not in reloaded or pd.api.types.is_numeric_dtype(reloaded["close"]),
    }
    if not all(checks.values()):
        raise ValueError(f"Storage validation failed: {checks}")
    return checks
