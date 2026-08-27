# Monitoring Plan

This S&P 500 volatility model would be monitored by a risk analyst, with the portfolio risk manager owning final review and escalation decisions. The model is a decision-support tool, so the monitoring goal is to catch stale inputs, degraded forecasts, system failures, and misleading business signals before they affect risk meetings.

**Data layer.** Monitor data freshness for S&P 500, VIX, and Treasury yields. A batch is late if market data are not refreshed by 7:00 p.m. New York time on a trading day. Monitor schema using expected columns in `data/raw/raw_data_manifest.json`; any missing `Close`, VIX, or Treasury column is a hard failure. Monitor null rates after cleaning; more than 2% missing VIX or yield observations in the last 60 trading days triggers review. First response: rerun `python src/run_step.py ingest`, inspect source availability, and log the issue in the project tracker.

**Model layer.** Monitor 20-day rolling MAE, rolling RMSE, and error versus the naive last-5-day realized-volatility baseline. Alert if rolling MAE is more than 25% above the backtest MAE or if the model underperforms the naive baseline for 10 consecutive trading days. Monitor high-VIX regime performance separately because stressed periods matter most. Retrain monthly or whenever rolling MAE breaches threshold twice in a month.

**System layer.** Monitor pipeline success rate, `reports/pipeline.log`, API 400/500 rates, and p95 API latency. Alert if a scheduled run fails, if p95 latency exceeds 2 seconds, or if 500 errors exceed 1% of requests. First response: rerun the failed CLI step, check logs, and roll back to the prior `model/model.pkl` if needed.

**Business layer.** Monitor elevated-risk alert frequency, missed stress events, and false alarms. Alert if elevated-risk signals occur on more than 30% of days in a month or if realized volatility exceeds the 80th percentile without a prior elevated signal three times in a quarter. The risk analyst updates dashboards weekly; the portfolio risk manager approves rollbacks and model changes.
