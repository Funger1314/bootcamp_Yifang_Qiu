# Stakeholder Handoff Summary

## Project purpose

This project forecasts future 5-trading-day realized S&P 500 volatility using market stress and interest-rate indicators. It is a risk-monitoring and decision-support tool, not an automated trading system.

## Primary stakeholder

The primary stakeholder is a portfolio manager or risk manager. A risk analyst operates the pipeline, reviews the outputs, and escalates unusual forecasts or degraded model behavior.

## Key findings

The corrected time-aware validation workflow selects `random_forest` after applying `TimeSeriesSplit(gap=5)`. On the final untouched test period, the selected model has MAE 0.003566 and RMSE 0.006571. The naive benchmark has MAE 0.003855 and RMSE 0.006342. The selected model improves MAE by 7.5%, but it does not improve RMSE, so large-error risk remains important.

## Recommendation

Use the forecast as an early-warning input in daily or weekly risk review. Escalate when predicted volatility is elevated, when the model disagrees sharply with the naive benchmark, or when VIX/recent realized volatility point to stress.

## Important assumptions

Inputs are daily close-based market indicators available at prediction time. Treasury gaps are forward-filled after market-date alignment. The final test period is not used for model selection. A five-row purge gap prevents overlapping forward target windows from leaking validation/test-period returns into training labels.

## Limitations and risks

The model is predictive, not causal. Performance may degrade under regime change, source outages, stale inputs, or unusual stress events. The API currently expects a complete engineered feature vector.

## Operational instructions

Run `python src/run_step.py all --start-date 2018-01-01 --end-date 2026-08-26` from `project/` to rebuild the project. Review `reports/volatility_risk_report.md`, `reports/tables/model_test_metrics.csv`, and `data/processed/volatility_forecasts.csv`. Start the prototype API with `python app.py`.

## Monitoring and escalation

Monitor data freshness, rolling MAE/RMSE, bias, high-VIX errors, pipeline logs, API 500 rates, and alert frequency. Escalate if rolling MAE exceeds the backtest MAE by 25%, if the model underperforms naive for 10 consecutive trading days, or if source data are stale after 7:00 p.m. New York time.

## Next steps

Build a dashboard that computes features automatically from fresh market data, tracks monitoring thresholds, and records analyst review decisions.
