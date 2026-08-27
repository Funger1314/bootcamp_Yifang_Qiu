# Project Summary

## Problem

Portfolio managers and risk managers need to know when market risk is rising before it becomes a portfolio surprise. This project asks whether current market stress and interest-rate indicators can help predict future 5-trading-day realized S&P 500 volatility.

The project is deliberately framed as a risk-monitoring and decision-support workflow. It does not recommend trades, automate portfolio changes, or claim causal relationships. Its practical job is to provide a reproducible forecast, compare that forecast with a naive baseline, and highlight when the result deserves human review.

## What was built

The final project is an end-to-end Python pipeline under `project/`. It downloads public daily data for the S&P 500, VIX, 10-year Treasury yield, and 2-year Treasury yield. It stores the raw files, aligns market dates, forward-fills Treasury yield publication gaps after alignment, and creates a clean modeling table.

The modeling target is future 5-day realized S&P 500 volatility. Features include recent S&P 500 returns, rolling realized volatility, VIX level/change, Treasury yield levels, the 10Y-2Y spread, and an interaction between VIX and recent realized volatility. The feature design avoids time leakage: inputs use information available at or before the prediction date, while the target is computed from the following five trading days.

The project compares a naive last-5-day realized-volatility baseline with Linear Regression, Ridge, and Random Forest models using a chronological holdout split. Ridge is selected because it has the best holdout MAE while keeping the model interpretable and stable.

## What was found

On the chronological test period, Ridge achieves MAE of 0.002774 and RMSE of 0.004688. The naive persistence baseline has MAE of 0.003855 and RMSE of 0.006342. That means Ridge improves MAE by about 28.0% and RMSE by about 26.1%, exceeding the project success criteria stated in the README.

The model also performs better than the naive baseline in high-VIX and high-realized-volatility regimes. That matters because the stakeholder cares most about periods when market risk is elevated. A bootstrap confidence interval for selected-model MAE is [0.002426, 0.003127], using 1,000 resamples. This uncertainty estimate is useful but should be treated cautiously because row bootstrap methods do not fully preserve time-series dependence.

## How to use the result

A risk analyst should run the pipeline after market close and review `data/processed/volatility_forecasts.csv` and `reports/volatility_risk_report.md`. If predicted volatility is elevated relative to recent history, the analyst should escalate to the portfolio risk manager for review. The correct action is a human risk discussion, not an automatic trade.

The Flask API in `app.py` lets another program submit a validated feature vector and receive a JSON volatility prediction. This is enough for a prototype risk dashboard, scheduled job, or internal tool.

## What not to rely on

Do not treat the model as a causal explanation of volatility. Do not expect it to perform equally well across future regimes without monitoring. Do not delete stress-period observations simply because they look like outliers; those observations are central to the risk-management use case.

## Next steps

The next practical step would be a monitoring dashboard that tracks data freshness, rolling model error, API health, and elevated-risk alert frequency. A future version could add richer macro indicators, options-derived features, or a high-volatility classification layer, but the core regression forecast should remain the primary project target unless the stakeholder reframes the decision.
