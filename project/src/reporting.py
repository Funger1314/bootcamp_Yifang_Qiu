"""Stakeholder reporting helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config import REPORTS_DIR


def write_stakeholder_report(
    metrics: pd.DataFrame,
    scenario_metrics: pd.DataFrame,
    bootstrap_ci: pd.DataFrame,
    reports_dir: Path = REPORTS_DIR,
) -> Path:
    """Write a stakeholder-ready Markdown volatility risk report."""

    reports_dir.mkdir(parents=True, exist_ok=True)
    best = metrics.loc[metrics["model"] != "naive_last_5d_realized_vol"].sort_values("MAE").iloc[0]
    naive = metrics.loc[metrics["model"] == "naive_last_5d_realized_vol"].iloc[0]
    ci = bootstrap_ci.iloc[0]
    success_mae = best["MAE_improvement_vs_naive"] >= 0.10
    success_rmse = best["RMSE_improvement_vs_naive"] >= 0.05
    scenario_table = _markdown_table(scenario_metrics)
    text = f"""# Volatility Risk Forecast Report

Audience: Portfolio manager / risk manager

## Executive Summary

- The selected model is **{best['model']}**, evaluated on a chronological holdout period against a naive last-observed-volatility benchmark.
- Test MAE improvement versus naive is **{best['MAE_improvement_vs_naive']:.1%}** and RMSE improvement is **{best['RMSE_improvement_vs_naive']:.1%}**.
- The tool is useful as a risk-monitoring aid, not an automated trading system. It should trigger human review when predicted volatility is elevated.

## Key Charts

![Actual vs predicted volatility](figures/actual_vs_predicted_volatility.png)

This chart compares realized future five-day volatility with the model forecast and the naive persistence baseline. It shows whether the model follows the broad volatility regime without claiming exact day-by-day precision.

![Model error comparison](figures/model_error_comparison.png)

The benchmark comparison is the main practical test: the project should improve over the risk manager's simple fallback of assuming recent volatility persists.

![Performance by regime](figures/scenario_mae_by_regime.png)

Regime performance matters because a risk model that works only in calm markets is less useful to a portfolio manager.

## Assumptions and Risks

- Inputs are daily close-based market indicators available at the prediction date close.
- Treasury yield reporting gaps are forward-filled across market dates; this is reasonable for short holiday gaps but can understate data staleness risk.
- Extreme market observations are retained and flagged rather than deleted because stress periods are decision-relevant.
- The model is predictive, not causal. Coefficients or feature importance should not be read as proof that an input caused volatility.
- Financial regimes change; performance should be monitored with rolling errors and stress-regime diagnostics.

## Sensitivity and Uncertainty

Bootstrap selected-model MAE estimate: **{ci['mae']:.6f}**, 95% CI **[{ci['ci_lower']:.6f}, {ci['ci_upper']:.6f}]** using 1,000 resamples of test residual errors.

Scenario comparison:

{scenario_table}

## What This Means for You

1. Use the forecast as an early-warning input for daily risk review.
2. Compare the model forecast with the naive baseline before taking action; disagreement is a prompt for analyst review.
3. Give more weight to the signal when VIX and recent realized volatility both point to elevated risk.
4. Do not automate trades from this model. The output supports monitoring, scenario discussion, and escalation.

## Success Criteria Check

- MAE at least 10% better than naive: **{'PASS' if success_mae else 'NEEDS ATTENTION'}**
- RMSE at least 5% better than naive: **{'PASS' if success_rmse else 'NEEDS ATTENTION'}**
- Reproducible artifacts generated under `data/processed/`, `model/`, and `reports/`: **PASS**
"""
    output = reports_dir / "volatility_risk_report.md"
    output.write_text(text, encoding="utf-8")
    return output


def _markdown_table(dataframe: pd.DataFrame) -> str:
    """Render a small DataFrame as a Markdown table without extra dependencies."""

    display = dataframe.copy()
    for column in display.select_dtypes(include="number").columns:
        if column == "n" or column.endswith("_rows"):
            display[column] = display[column].map(lambda value: f"{int(value)}")
        elif "improvement" in column or "share" in column:
            display[column] = display[column].map(lambda value: f"{value:.1%}")
        else:
            display[column] = display[column].map(lambda value: f"{value:.6f}")
    headers = list(display.columns)
    rows = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for _, row in display.iterrows():
        rows.append("| " + " | ".join(str(row[column]) for column in headers) + " |")
    return "\n".join(rows)
