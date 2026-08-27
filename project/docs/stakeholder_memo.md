# Stakeholder Memo

## Stakeholder

The primary stakeholder is a portfolio manager or risk manager responsible for monitoring short-term market risk and portfolio exposure.

## Problem

Financial market volatility can change quickly. The stakeholder needs a simple and interpretable way to assess whether current market stress and interest-rate conditions suggest higher S&P 500 volatility over the next several trading days.

## Decision

The analysis will help the stakeholder determine whether current market conditions justify increased risk monitoring or adjustments to portfolio risk exposure.

## Desired Output

The project will estimate future 5-day realized S&P 500 volatility using indicators such as VIX, recent S&P 500 returns, Treasury yields, and recent realized volatility.

## Success Criteria

The required regression model will be considered useful when, on a chronological held-out test period, it improves MAE by at least 10% and RMSE by at least 5% versus a last-observation volatility baseline, produces forecasts for at least 95% of eligible trading days, and can be reproduced in a clean environment. If the optional high-volatility classifier is delivered, it should achieve at least 0.70 ROC-AUC and 0.70 recall for high-volatility periods.

## Operating Context

A risk analyst will refresh the workflow after each trading day closes. The portfolio risk manager owns the decision and reviews the forecast before the next market open. A forecast above the rolling historical 80th percentile, or a high-volatility probability of at least 60%, triggers enhanced human review rather than an automatic trade.

## Deliverable

The stakeholder will receive a reproducible modeling notebook, a machine-readable forecast file at `data/processed/volatility_forecasts.csv`, and a concise risk report at `reports/volatility_risk_report.md`.

## Final Result

The completed final project uses a time-aware modeling workflow: Linear Regression, Ridge, and Random Forest are compared only inside the development period with `TimeSeriesSplit`, and the final chronological test period is reserved for one held-out evaluation of the selected model. In the current run, Random Forest is selected by validation. On the final test period it improves MAE by about 8.4% versus the naive last-observed-volatility baseline, but it does not improve RMSE. This mixed result is documented transparently: the model can support risk monitoring, but the stakeholder should continue comparing it with the naive benchmark and should not treat it as an automated trading or causal decision system.
