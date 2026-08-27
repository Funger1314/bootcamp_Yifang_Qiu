# Handoff Plan

- Deployment path: run `python src/run_step.py all` from `project/` to refresh data, rebuild features, retrain the selected model, evaluate, and regenerate stakeholder outputs.
- API launch: after the pipeline produces `model/model.pkl`, run `python app.py` from `project/`.
- Operator runbook links: `README.md` for setup/API commands, `docs/monitoring_plan.md` for thresholds, `docs/orchestration_plan.md` for task dependencies, and `reports/pipeline.log` for runtime diagnostics.
- On-call owner: risk analytics operator monitors data freshness, pipeline completion, and API health.
- Decision owner: portfolio risk manager approves model rollback, retraining outside cadence, and stakeholder escalation.
- Primary outputs to check after each run: `data/processed/volatility_forecasts.csv`, `reports/tables/model_metrics.csv`, and `reports/volatility_risk_report.md`.
- First response to failed ingestion: rerun `python src/run_step.py ingest`, check Yahoo/FRED availability, and do not publish stale forecasts until raw data are refreshed or the limitation is documented.
- First response to degraded model metrics: compare selected model with naive baseline, review high-VIX regime errors, and escalate if rolling MAE breaches the monitoring threshold.
- Rollback path: restore the last known-good `model/model.pkl` from version control or the latest approved release branch.
- Manual steps retained: final portfolio action remains human-reviewed because the model is a risk-monitoring signal, not an automated trading system.
