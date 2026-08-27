# Stage 01-16 Project Grading Checklist

| Stage | Official requirement | Corresponding project file | Evidence | Status |
| --- | --- | --- | --- | --- |
| 01 | Stakeholder-centered problem, user, goals, lifecycle mapping | `README.md`, `docs/stakeholder_memo.md` | Problem, stakeholder, decision context, success criteria, lifecycle map | PASS |
| 02 | Project structure, `.gitignore`, `.env.example`, requirements, config | `.gitignore`, `.env.example`, `requirements.txt`, `src/config.py` | Reproducible folders, ignored secrets, env placeholders, path helpers | PASS |
| 03 | Python/NumPy/pandas evidence and reusable utility | `notebooks/python_fundamentals_summary.ipynb`, `src/utils.py` | Existing fundamentals notebook plus reusable utility helpers | PASS |
| 04 | Reproducible data acquisition and raw persistence | `src/acquisition.py`, `data/raw/*.csv` | Yahoo/FRED downloads, source manifest, raw CSVs | PASS |
| 05 | Raw/processed storage and documentation | `data/raw/`, `data/processed/`, `README.md` | Raw manifest, cleaned/model-ready/forecast processed files | PASS |
| 06 | Reusable preprocessing functions and cleaned dataset | `src/cleaning.py`, `data/processed/market_data_cleaned.csv` | Date parsing, sorting, deduping, numeric validation, alignment, documented yield fill | PASS |
| 07 | Reusable outlier logic and assumption documentation | `src/outliers.py`, `data/processed/outlier_sensitivity_summary.csv` | Stress/outlier flags retained for sensitivity instead of deleted | PASS |
| 08 | EDA notebook/evidence, statistics, visuals, `src/eda.py` | `src/eda.py`, `reports/tables/eda_*.csv`, `reports/figures/eda_*.png` | Missingness, summary stats, correlations, VIX/future vol charts | PASS |
| 09 | Engineered features, rationale, pipeline import | `src/features.py`, `feature_registry.csv`, `model_ready_volatility.csv` | Lag, rolling, VIX, yield, spread, interaction features with leakage notes | PASS |
| 10a | Regression modeling, diagnostics, assumptions, metrics | `src/modeling.py`, `reports/tables/model_metrics.csv`, `residual_diagnostics.png` | Chronological split; naive, Linear, Ridge, Random Forest; residual plots | PASS |
| 10b | Appropriate modeling track or time-series/classification alternative | `src/modeling.py`, `src/features.py` | Regression is the selected track for continuous volatility target; lag/rolling features and sklearn pipelines included | PASS |
| 11 | Metrics, uncertainty, two scenarios, risks | `src/evaluation.py`, `reports/tables/bootstrap_mae_ci.csv`, `scenario_metrics.csv` | 1,000 bootstrap CI, high-VIX/high-vol scenarios, sensitivity table | PASS |
| 12 | Stakeholder-ready deliverable in reports with charts and implications | `reports/volatility_risk_report.md`, `reports/figures/*.png` | Executive summary, charts, assumptions, risks, sensitivity, "what this means for you" | PASS |
| 13 | Productized saved model with API/dashboard and testing evidence | `app.py`, `model/model.pkl`, `notebooks/project_pipeline.ipynb` | Flask API loads model once, validates input, returns JSON predictions/errors | PASS |
| 14 | Monitoring and handoff plans | `docs/monitoring_plan.md`, `docs/handoff_plan.md` | Data/model/system/business monitoring with thresholds, owners, runbook actions | PASS |
| 15 | Orchestration plan and CLI step | `docs/orchestration_plan.md`, `src/run_step.py` | 7-step DAG, idempotency, retries, logging, runnable CLI | PASS |
| 16 | Lifecycle guide, final summary, clean README/repo | `docs/lifecycle_framework_guide.md`, `docs/project_summary.md`, `README.md` | Every stage mapped to real files; final setup/run instructions | PASS |

## Known limitations

- The API expects a complete model feature vector; a production dashboard would normally compute features from latest raw market data automatically.
- Bootstrap uncertainty uses row resampling for course-scope simplicity and documents the time-dependence limitation.
- Live data refresh depends on public Yahoo/FRED endpoint availability.
