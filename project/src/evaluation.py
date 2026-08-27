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
from src.features import BASE_FEATURES, TARGET_COLUMN
from src.modeling import build_model_by_name


TREASURY_FEATURES = [
    "treasury_10y",
    "treasury_2y",
    "yield_spread_10y_2y",
    "yield_spread_change_5d",
]


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


def _mae_rmse_bias(y_true: pd.Series | np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    """Return the sensitivity metrics required by the project rubric."""

    error = np.asarray(y_true, dtype=float) - np.asarray(y_pred, dtype=float)
    return {
        "MAE": float(np.abs(error).mean()),
        "RMSE": float(np.sqrt(np.mean(error**2))),
        "bias": float(error.mean()),
    }


def regime_subgroup_metrics(predictions: pd.DataFrame, model_ready: pd.DataFrame) -> pd.DataFrame:
    """Compare final-test performance across risk-relevant market subgroups."""

    pred = predictions.copy()
    pred["date"] = pd.to_datetime(pred["date"])
    context = model_ready[["date", "vix_close", "high_vix_regime", "high_realized_vol_regime"]].copy()
    context["date"] = pd.to_datetime(context["date"])
    pred = pred.merge(context, on="date", how="left")
    subgroups = {
        "All final-test observations": pd.Series(True, index=pred.index),
        "Low/normal VIX regime": ~pred["high_vix_regime"].fillna(False),
        "High VIX regime": pred["high_vix_regime"].fillna(False),
        "High realized-volatility regime": pred["high_realized_vol_regime"].fillna(False),
    }
    rows = []
    for name, mask in subgroups.items():
        subset = pred.loc[mask].copy()
        if subset.empty:
            continue
        selected_error = subset["actual"] - subset["selected_prediction"]
        naive_error = subset["actual"] - subset["naive_last_5d_realized_vol"]
        selected_mae = float(np.abs(selected_error).mean())
        naive_mae = float(np.abs(naive_error).mean())
        rows.append(
            {
                "subgroup": name,
                "n": int(len(subset)),
                "selected_MAE": selected_mae,
                "selected_RMSE": float(np.sqrt(np.mean(selected_error**2))),
                "selected_bias": float(selected_error.mean()),
                "naive_MAE": naive_mae,
                "MAE_improvement_vs_naive": float((naive_mae - selected_mae) / naive_mae),
            }
        )
    return pd.DataFrame(rows)


def assumption_sensitivity(results: dict, model_ready: pd.DataFrame) -> pd.DataFrame:
    """Evaluate materially different assumptions on the same final test period.

    The final test dates are held constant for every scenario. Each alternative
    scenario refits the already selected model class using only development data.
    This tests robustness without letting the final test period influence model
    selection.
    """

    selected_model_name = results["best_model_name"]
    development = results["development"].copy()
    final_test = results["test"].copy()
    y_test = final_test[TARGET_COLUMN]
    baseline_pred = results["predictions"]["selected_prediction"].to_numpy()

    scenario_specs = [
        {
            "scenario": "Baseline: selected model, full feature set, full development history",
            "feature_columns": results["feature_columns"],
            "training_data": development,
            "prediction": baseline_pred,
            "interpretation": "Prediction holds if all approved market, volatility, VIX, and Treasury inputs remain available.",
        },
        {
            "scenario": "No Treasury/yield information",
            "feature_columns": [column for column in results["feature_columns"] if column not in TREASURY_FEATURES],
            "training_data": development,
            "prediction": None,
            "interpretation": "Tests sensitivity to losing interest-rate levels and yield-spread information.",
        },
        {
            "scenario": "Shorter training history: 2020 onward",
            "feature_columns": results["feature_columns"],
            "training_data": development.loc[pd.to_datetime(development["date"]) >= pd.Timestamp("2020-01-01")].copy(),
            "prediction": None,
            "interpretation": "Tests whether older market regimes are helping or hurting final-test performance.",
        },
    ]

    rows: list[dict] = []
    baseline_mae: float | None = None
    baseline_rmse: float | None = None
    for spec in scenario_specs:
        train_data = spec["training_data"]
        features = spec["feature_columns"]
        if train_data.empty:
            continue
        if spec["prediction"] is None:
            model = build_model_by_name(selected_model_name)
            model.fit(train_data[features], train_data[TARGET_COLUMN])
            prediction = model.predict(final_test[features])
        else:
            prediction = spec["prediction"]
        metrics = _mae_rmse_bias(y_test, prediction)
        if baseline_mae is None:
            baseline_mae = metrics["MAE"]
            baseline_rmse = metrics["RMSE"]
        rows.append(
            {
                "scenario": spec["scenario"],
                "model": selected_model_name,
                "feature_count": int(len(features)),
                "train_rows": int(len(train_data)),
                "test_rows": int(len(final_test)),
                "test_start": str(final_test["date"].min().date()),
                "test_end": str(final_test["date"].max().date()),
                **metrics,
                "delta_MAE_vs_baseline": float(metrics["MAE"] - baseline_mae),
                "delta_RMSE_vs_baseline": float(metrics["RMSE"] - baseline_rmse),
                "interpretation": spec["interpretation"],
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
    regime = regime_subgroup_metrics(pred, model_ready)
    sensitivity = assumption_sensitivity(results, model_ready)
    outputs = {
        "bootstrap_ci": tables_dir / "bootstrap_mae_ci.csv",
        "scenario_metrics": tables_dir / "scenario_metrics.csv",
        "regime_subgroup_metrics": tables_dir / "regime_subgroup_metrics.csv",
        "assumption_sensitivity": tables_dir / "assumption_sensitivity.csv",
    }
    pd.DataFrame([ci]).to_csv(outputs["bootstrap_ci"], index=False)
    regime.to_csv(outputs["scenario_metrics"], index=False)
    regime.to_csv(outputs["regime_subgroup_metrics"], index=False)
    sensitivity.to_csv(outputs["assumption_sensitivity"], index=False)

    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.barplot(data=regime, x="subgroup", y="selected_MAE", ax=ax, color="#4c78a8")
    ax.scatter(range(len(regime)), regime["naive_MAE"], color="#f58518", label="Naive MAE")
    ax.set_title("Final-test MAE by risk regime / subgroup")
    ax.set_ylabel("MAE")
    ax.set_xlabel("")
    ax.tick_params(axis="x", rotation=25)
    ax.legend(handles=[Patch(color="#4c78a8", label="Selected model MAE"), *ax.get_legend_handles_labels()[0]])
    outputs["scenario_mae"] = figures_dir / "scenario_mae_by_regime.png"
    fig.tight_layout()
    fig.savefig(outputs["scenario_mae"], dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4))
    plot_sensitivity = sensitivity.melt(
        id_vars=["scenario"],
        value_vars=["MAE", "RMSE"],
        var_name="metric",
        value_name="value",
    )
    sns.barplot(data=plot_sensitivity, x="scenario", y="value", hue="metric", ax=ax)
    ax.set_title("Assumption sensitivity on the same final test period")
    ax.set_ylabel("Error")
    ax.set_xlabel("")
    ax.tick_params(axis="x", rotation=25)
    outputs["assumption_sensitivity"] = figures_dir / "assumption_sensitivity.png"
    fig.tight_layout()
    fig.savefig(outputs["assumption_sensitivity"], dpi=160)
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
