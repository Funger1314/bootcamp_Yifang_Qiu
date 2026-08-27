"""Outlier and market-stress helpers for the volatility project."""

from __future__ import annotations

import pandas as pd


def iqr_bounds(series: pd.Series, k: float = 1.5) -> tuple[float, float]:
    """Return Tukey IQR lower and upper bounds for a numeric series."""

    if k <= 0:
        raise ValueError("k must be positive")
    observed = pd.to_numeric(series, errors="coerce").dropna()
    if observed.empty:
        raise ValueError("series must contain at least one observed numeric value")
    q1, q3 = observed.quantile([0.25, 0.75])
    iqr = q3 - q1
    return float(q1 - k * iqr), float(q3 + k * iqr)


def flag_iqr_outliers(dataframe: pd.DataFrame, column: str, k: float = 1.5, flag_name: str | None = None) -> pd.DataFrame:
    """Add a boolean IQR outlier flag without deleting risk-relevant rows."""

    flagged = dataframe.copy()
    lower, upper = iqr_bounds(flagged[column], k=k)
    name = flag_name or f"{column}_iqr_outlier"
    flagged[name] = ((flagged[column] < lower) | (flagged[column] > upper)).fillna(False)
    return flagged


def add_stress_flags(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Flag volatility/return stress observations used for subgroup diagnostics."""

    flagged = dataframe.copy()
    high_vix_cutoff = flagged["vix_close"].quantile(0.75)
    high_realized_vol_cutoff = flagged["realized_volatility_5d"].quantile(0.75)
    return_cutoff = flagged["sp500_return"].abs().quantile(0.95)
    flagged["high_vix_regime"] = flagged["vix_close"] >= high_vix_cutoff
    flagged["high_realized_vol_regime"] = flagged["realized_volatility_5d"] >= high_realized_vol_cutoff
    flagged["large_abs_return_flag"] = flagged["sp500_return"].abs() >= return_cutoff
    return flagged


def outlier_sensitivity_summary(dataframe: pd.DataFrame, target_column: str) -> pd.DataFrame:
    """Summarize retained-vs-excluded target behavior for flagged stress rows."""

    rows = []
    flag_columns = [c for c in dataframe.columns if c.endswith("_outlier") or c.endswith("_flag")]
    for flag in flag_columns:
        mask = dataframe[flag].astype(bool)
        rows.append(
            {
                "flag": flag,
                "flagged_rows": int(mask.sum()),
                "flagged_share": float(mask.mean()),
                "target_mean_all_rows": float(dataframe[target_column].mean()),
                "target_mean_flagged_rows": float(dataframe.loc[mask, target_column].mean()) if mask.any() else float("nan"),
                "target_mean_unflagged_rows": float(dataframe.loc[~mask, target_column].mean()) if (~mask).any() else float("nan"),
                "treatment_decision": "retain and flag for sensitivity/regime analysis",
            }
        )
    return pd.DataFrame(rows)
