# Monitoring Plan

This model is monitored by a risk analyst; the portfolio risk manager owns escalation, rollback, and model-change approvals. Monitoring focuses on four layers: data, model, system, and business usefulness.

**Data.** Check S&P 500, VIX, 10Y yield, and 2Y yield freshness after each trading day. A batch is late if required market data are unavailable by 7:00 p.m. New York time. Validate expected raw schemas against `data/raw/raw_data_manifest.json`; missing close/yield columns are hard failures. More than 2% missing cleaned VIX or yield observations in the latest 60 trading days triggers review. First response: rerun `python src/run_step.py ingest`, inspect source availability, and log the issue in GitHub Issues or the team's operational tracker.

**Model.** Track 20-day rolling MAE, rolling RMSE, bias, and performance versus the naive last-5-day volatility baseline. Alert if rolling MAE exceeds backtest MAE by 25%, if RMSE deteriorates sharply, or if the selected model underperforms naive for 10 consecutive trading days. Track high-VIX rows separately because stress periods matter most. Retrain monthly, or sooner after two threshold breaches in one month.

**System.** Monitor pipeline success, `reports/pipeline.log`, API 400/500 rates, and p95 API latency. Alert on failed scheduled runs, p95 latency above two seconds, or 500 errors above 1%. First response: rerun the failed CLI step, check logs, and roll back to the prior `model/model.pkl` if service stability is affected.

**Business.** Track elevated-risk alert frequency, missed stress events, and false alarms. Alert if elevated-risk signals occur on more than 30% of trading days in a month, or if realized volatility exceeds the 80th percentile without prior warning three times in a quarter.
