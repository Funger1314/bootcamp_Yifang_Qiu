"""EDA helpers and project-specific charts."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.config import REPORTS_DIR


def eda_summary(dataframe: pd.DataFrame) -> dict:
    """Return structural, missingness, and numeric summary statistics."""

    numeric = dataframe.select_dtypes(include="number")
    return {
        "shape": dataframe.shape,
        "dtypes": {column: str(dtype) for column, dtype in dataframe.dtypes.items()},
        "missing": dataframe.isna().sum().astype(int).to_dict(),
        "numeric_summary": numeric.agg(["mean", "median", "std", "min", "max", "skew"]).T,
        "date_min": str(dataframe["date"].min().date()) if "date" in dataframe else None,
        "date_max": str(dataframe["date"].max().date()) if "date" in dataframe else None,
    }


def save_eda_tables(dataframe: pd.DataFrame, reports_dir: Path = REPORTS_DIR) -> dict[str, Path]:
    """Save EDA summary and correlation tables."""

    tables_dir = reports_dir / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)
    numeric = dataframe.select_dtypes(include="number")
    outputs = {
        "numeric_summary": tables_dir / "eda_numeric_summary.csv",
        "correlation_matrix": tables_dir / "eda_correlation_matrix.csv",
        "missingness": tables_dir / "eda_missingness.csv",
    }
    numeric.agg(["mean", "median", "std", "min", "max", "skew"]).T.to_csv(outputs["numeric_summary"])
    numeric.corr().to_csv(outputs["correlation_matrix"])
    dataframe.isna().sum().rename("missing_count").to_frame().to_csv(outputs["missingness"])
    return outputs


def save_eda_figures(dataframe: pd.DataFrame, reports_dir: Path = REPORTS_DIR) -> dict[str, Path]:
    """Create charts linking the data to the volatility prediction question."""

    figures_dir = reports_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")
    outputs: dict[str, Path] = {}

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(dataframe["date"], dataframe["realized_volatility_21d"], label="21d realized volatility")
    ax.plot(dataframe["date"], dataframe["vix_close"] / 100, label="VIX / 100", alpha=0.75)
    ax.set_title("S&P 500 realized volatility and VIX")
    ax.set_ylabel("Volatility / scaled index")
    ax.legend()
    outputs["volatility_time_series"] = figures_dir / "eda_volatility_time_series.png"
    fig.tight_layout()
    fig.savefig(outputs["volatility_time_series"], dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(dataframe["vix_close"], dataframe["future_5d_realized_volatility"], alpha=0.35, s=16)
    ax.set_title("VIX vs future 5-day realized volatility")
    ax.set_xlabel("VIX close")
    ax.set_ylabel("Future 5-day realized volatility")
    outputs["vix_vs_future_vol"] = figures_dir / "eda_vix_vs_future_vol.png"
    fig.tight_layout()
    fig.savefig(outputs["vix_vs_future_vol"], dpi=160)
    plt.close(fig)

    columns = [
        "future_5d_realized_volatility",
        "realized_volatility_5d",
        "vix_close",
        "treasury_10y",
        "treasury_2y",
        "yield_spread_10y_2y",
    ]
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(dataframe[columns].corr(), annot=True, cmap="vlag", center=0, fmt=".2f", ax=ax)
    ax.set_title("Correlation among volatility predictors")
    outputs["correlation_heatmap"] = figures_dir / "eda_correlation_heatmap.png"
    fig.tight_layout()
    fig.savefig(outputs["correlation_heatmap"], dpi=160)
    plt.close(fig)

    return outputs
