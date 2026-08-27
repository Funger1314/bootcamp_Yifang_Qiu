"""Evaluation, uncertainty, and risk communication helpers."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.patches import Patch

from src.config import REPORTS_DIR


def bootstrap_mae_ci(
    residuals: pd.Series | np.ndarray,
    n_bootstrap: int = 1000,
    seed: int = 42,
    alpha: float = 0.05,
) -> dict[str, float]:
    """Estimate a bootstrap confidence interval for MAE."""

    errors = np.abs(np.asarray(residuals, dtype=float))
    rng = np.random.default_rng(seed)
    draws = np.empty(n_bootstrap)
    for idx in range(n_bootstrap):
        sample = rng.choice(errors, size=len(errors), replace=True)
        draws[idx] = sample.mean()
    lower, upper = np.quantile(draws, [alpha / 2, 1 - alpha / 2])
    return {
        "mae": float(errors.mean()),
        "bootstrap_mean": float(draws.mean()),
        "ci_lower": float(lower),
        "ci_upper": float(upper),
        "n_bootstrap": int(n_bootstrap),
    }


def scenario_metrics(predictions: pd.DataFrame, model_ready: pd.DataFrame) -> pd.DataFrame:
    """Compare performance under materially different market/regime scenarios."""

    pred = predictions.copy()
    pred["date"] = pd.to_datetime(pred["date"])
    context = model_ready[["date", "vix_close", "high_vix_regime", "high_realized_vol_regime"]].copy()
    context["date"] = pd.to_datetime(context["date"])
    pred = pred.merge(context, on="date", how="left")
    scenarios = {
        "All test observations": pd.Series(True, index=pred.index),
        "Low/normal VIX regime": ~pred["high_vix_regime"].fillna(False),
        "High VIX regime": pred["high_vix_regime"].fillna(False),
        "High realized-volatility regime": pred["high_realized_vol_regime"].fillna(False),
    }
    rows = []
    for name, mask in scenarios.items():
        subset = pred.loc[mask].copy()
        if subset.empty:
            continue
        selected_error = subset["actual"] - subset["selected_prediction"]
        naive_error = subset["actual"] - subset["naive_last_5d_realized_vol"]
        rows.append(
            {
                "scenario": name,
                "n": int(len(subset)),
                "selected_MAE": float(np.abs(selected_error).mean()),
                "naive_MAE": float(np.abs(naive_error).mean()),
                "MAE_improvement_vs_naive": float((np.abs(naive_error).mean() - np.abs(selected_error).mean()) / np.abs(naive_error).mean()),
                "selected_bias": float(selected_error.mean()),
            }
        )
    return pd.DataFrame(rows)


def feature_specification_sensitivity(results: dict, model_ready: pd.DataFrame) -> pd.DataFrame:
    """Summarize two assumption scenarios: selected model vs VIX-only and naive."""

    pred = results["predictions"]
    rows = []
    for column, label in [
        ("naive_last_5d_realized_vol", "Naive persistence baseline"),
        ("linear_regression", "Linear regression feature specification"),
        (results["best_model_name"], f"Selected model ({results['best_model_name']})"),
    ]:
        if column not in pred.columns:
            continue
        err = pred["actual"] - pred[column]
        rows.append(
            {
                "scenario": label,
                "MAE": float(np.abs(err).mean()),
                "RMSE": float(np.sqrt(np.mean(err**2))),
                "bias": float(err.mean()),
                "assumption": "Different model/feature specification on the same chronological test period.",
            }
        )
    return pd.DataFrame(rows)


def save_evaluation_outputs(
    results: dict,
    model_ready: pd.DataFrame,
    reports_dir: Path = REPORTS_DIR,
) -> dict[str, Path]:
    """Save evaluation tables and charts for risk communication."""

    tables_dir = reports_dir / "tables"
    figures_dir = reports_dir / "figures"
    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)
    pred = results["predictions"]
    ci = bootstrap_mae_ci(pred["selected_residual"], n_bootstrap=1000, seed=42)
    scenario = scenario_metrics(pred, model_ready)
    sensitivity = feature_specification_sensitivity(results, model_ready)
    outputs = {
        "bootstrap_ci": tables_dir / "bootstrap_mae_ci.csv",
        "scenario_metrics": tables_dir / "scenario_metrics.csv",
        "sensitivity": tables_dir / "sensitivity_analysis.csv",
    }
    pd.DataFrame([ci]).to_csv(outputs["bootstrap_ci"], index=False)
    scenario.to_csv(outputs["scenario_metrics"], index=False)
    sensitivity.to_csv(outputs["sensitivity"], index=False)

    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.barplot(data=scenario, x="scenario", y="selected_MAE", ax=ax, color="#4c78a8")
    ax.scatter(range(len(scenario)), scenario["naive_MAE"], color="#f58518", label="Naive MAE")
    ax.set_title("Selected model MAE by market regime")
    ax.set_ylabel("MAE")
    ax.tick_params(axis="x", rotation=25)
    ax.legend(handles=[Patch(color="#4c78a8", label="Selected model MAE"), *ax.get_legend_handles_labels()[0]])
    outputs["scenario_mae"] = figures_dir / "scenario_mae_by_regime.png"
    fig.tight_layout()
    fig.savefig(outputs["scenario_mae"], dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.errorbar(["Selected model"], [ci["mae"]], yerr=[[ci["mae"] - ci["ci_lower"]], [ci["ci_upper"] - ci["mae"]]], fmt="o", capsize=8)
    ax.set_title("Bootstrap uncertainty for selected-model MAE")
    ax.set_ylabel("MAE")
    outputs["bootstrap_mae_ci"] = figures_dir / "bootstrap_mae_ci.png"
    fig.tight_layout()
    fig.savefig(outputs["bootstrap_mae_ci"], dpi=160)
    plt.close(fig)

    return outputs
