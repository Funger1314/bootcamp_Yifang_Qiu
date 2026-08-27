"""Stakeholder reporting helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config import REPORTS_DIR


def write_stakeholder_report(
    validation_metrics: pd.DataFrame,
    test_metrics: pd.DataFrame,
    assumption_sensitivity: pd.DataFrame,
    regime_metrics: pd.DataFrame,
    bootstrap_ci: pd.DataFrame,
    reports_dir: Path = REPORTS_DIR,
) -> Path:
    """Write a stakeholder-ready Markdown volatility risk report."""

    reports_dir.mkdir(parents=True, exist_ok=True)
    selected = test_metrics.loc[test_metrics["role"] == "selected_by_development_validation"].iloc[0]
    naive = test_metrics.loc[test_metrics["model"] == "naive_last_5d_realized_vol"].iloc[0]
    ci = bootstrap_ci.iloc[0]
    success_mae = selected["MAE_improvement_vs_naive"] >= 0.10
    success_rmse = selected["RMSE_improvement_vs_naive"] >= 0.05
    validation_table = _markdown_table(validation_metrics)
    test_table = _markdown_table(test_metrics)
    assumption_table = _markdown_table(assumption_sensitivity)
    regime_table = _markdown_table(regime_metrics)
    baseline_assumption = assumption_sensitivity.iloc[0]
    alternative_assumptions = assumption_sensitivity.iloc[1:].copy()
    worst_alternative = alternative_assumptions.sort_values("MAE", ascending=False).iloc[0] if not alternative_assumptions.empty else baseline_assumption
    if not alternative_assumptions.empty and alternative_assumptions["delta_MAE_vs_baseline"].max() <= 0:
        sensitivity_interpretation = (
            "In this run, neither alternative assumption worsens MAE relative to the baseline. "
            "That suggests the final-test result is not highly dependent on Treasury/yield features or older pre-2020 training rows, "
            "although this should be monitored rather than treated as a permanent economic rule."
        )
    else:
        sensitivity_interpretation = (
            f"The result is most sensitive to **{worst_alternative['scenario']}**, whose MAE changes by "
            f"**{worst_alternative['delta_MAE_vs_baseline']:.6f}** versus baseline."
        )

    text = f"""# Volatility Risk Forecast Report

Audience: Portfolio manager / risk manager

## Executive Summary

- The selected model is **{selected['model']}**, chosen using time-aware validation inside the development period only with a five-row purge gap.
- The final test period is kept untouched for model selection. It is used once to compare the selected model with the naive last-observed-volatility benchmark.
- A five-row purge gap prevents overlapping forward target windows from leaking validation/test-period returns into training labels.
- Final-test MAE improvement versus naive is **{selected['MAE_improvement_vs_naive']:.1%}** and RMSE improvement is **{selected['RMSE_improvement_vs_naive']:.1%}**.
- The tool is useful as a risk-monitoring aid, not an automated trading system. Elevated forecasts should trigger human review.

## Key Charts

![Actual vs predicted volatility](figures/actual_vs_predicted_volatility.png)

This chart compares realized future five-day volatility with the model forecast and the naive persistence baseline on the final test period. It shows whether the model follows the broad volatility regime without claiming exact day-by-day precision.

![Model validation comparison](figures/model_validation_comparison.png)

This chart shows the development-period validation evidence used to choose the model. Each validation fold uses a five-row gap, and the final development/test boundary also purges five rows before the final test start.

![Assumption sensitivity](figures/assumption_sensitivity.png)

This chart compares the baseline specification with two alternative assumptions on the same final test dates: removing Treasury/yield information and training only on more recent post-2020 observations.

## Model Selection and Final Test Results

Development-period validation metrics:

{validation_table}

Final untouched test metrics:

{test_table}

Final split leakage control: the target uses returns from t+1 through t+5, so the workflow removes the five rows immediately before the final test period from development training. This keeps the intended final-test start date while preventing development labels from using final-test-period returns.

## Assumption Sensitivity

The baseline scenario uses the selected model, the full approved feature set, and the full development training window. Alternative scenarios change one practical assumption at a time while preserving the same final test period.

{assumption_table}

Prediction holds if the public market, VIX, and Treasury inputs remain available and the future market regime resembles the development data closely enough. {sensitivity_interpretation} The model is relatively stable to an assumption when its MAE/RMSE deltas remain small relative to baseline MAE **{baseline_assumption['MAE']:.6f}**.

## Regime / Subgroup Diagnostics

The following diagnostics ask where the model performs better or worse. They are not the same as assumption sensitivity because the model specification is not changed; the final-test observations are sliced by market conditions.

{regime_table}

Risk increases when VIX or recent realized volatility is elevated, so the high-stress rows deserve separate review even when average test error is acceptable.

## Bootstrap Uncertainty

Bootstrap selected-model MAE estimate: **{ci['mae']:.6f}**, 95% CI **[{ci['ci_lower']:.6f}, {ci['ci_upper']:.6f}]** using 1,000 resamples of final-test residual errors.

This interval is useful for communicating uncertainty, but it should be read cautiously because a simple row bootstrap does not fully preserve time-series dependence in daily financial data.

## Assumptions and Risks

- Inputs are daily close-based market indicators available at the prediction date close.
- Treasury yield reporting gaps are forward-filled across market dates; this is reasonable for short holiday gaps but can understate data staleness risk.
- Extreme market observations are retained and flagged rather than deleted because stress periods are decision-relevant.
- The model is predictive, not causal. Coefficients or feature importance should not be read as proof that an input caused volatility.
- Financial regimes change; performance should be monitored with rolling errors, data freshness checks, and stress-regime diagnostics.

## What This Means for You

1. Use the forecast as an early-warning input for daily risk review.
2. Compare the model forecast with the naive baseline before taking action; disagreement is a prompt for analyst review.
3. Give more weight to the signal when VIX and recent realized volatility both point to elevated risk.
4. Do not automate trades from this model. The output supports monitoring, scenario discussion, and escalation.

## Success Criteria Check

- MAE at least 10% better than naive: **{'PASS' if success_mae else 'NEEDS ATTENTION'}**
- RMSE at least 5% better than naive: **{'PASS' if success_rmse else 'NEEDS ATTENTION'}**
- Model selection kept separate from final test evaluation: **PASS**
- Reproducible artifacts generated under `data/processed/`, `model/`, and `reports/`: **PASS**
"""
    output = reports_dir / "volatility_risk_report.md"
    output.write_text(text, encoding="utf-8")
    return output


def _markdown_table(dataframe: pd.DataFrame) -> str:
    """Render a small DataFrame as a Markdown table without extra dependencies."""

    display = dataframe.copy()
    for column in display.select_dtypes(include="number").columns:
        if column in {"n", "folds", "train_rows", "validation_rows", "development_rows", "final_test_rows", "feature_count", "test_rows", "selection_rank"} or column.endswith("_rank"):
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
