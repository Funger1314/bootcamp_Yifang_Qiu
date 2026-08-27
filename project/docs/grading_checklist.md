# Stage 01-16 Project Grading Checklist

| Stage | Official requirement | Actual project artifact | Evidence | Status |
| --- | --- | --- | --- | --- |
| 01 | Stakeholder-centered problem, decision owner, user, goals, lifecycle mapping | `README.md`, `docs/stakeholder_memo.md` | Portfolio/risk manager stakeholder, decision context, target, success criteria, lifecycle map | PASS |
| 02 | Project structure, `.gitignore`, `.env.example`, requirements, config | `.gitignore`, `.env.example`, `requirements.txt`, `src/config.py` | Reproducible folders, ignored secrets, env placeholders, project-relative diagnostics | PASS |
| 03 | Python/NumPy/pandas evidence and reusable utility | `notebooks/python_fundamentals_summary.ipynb`, `src/utils.py` | Executed fundamentals notebook plus reusable JSON/table helpers | PASS |
| 04 | Reproducible data acquisition and raw persistence | `src/acquisition.py`, `data/raw/*.csv` | Yahoo/FRED acquisition functions, raw CSVs, source manifest | PASS |
| 05 | Raw/processed storage and documentation | `data/raw/`, `data/processed/`, `README.md` | README Data Storage section explains raw immutability, processed artifacts, CSV use, and manifest provenance | PASS |
| 06 | Reusable preprocessing functions and cleaned dataset | `src/cleaning.py`, `data/processed/market_data_cleaned.csv` | Date parsing, sorting, deduping, numeric validation, aligned market dates, documented yield fill | PASS |
| 07 | Reusable outlier logic and assumption documentation | `src/outliers.py`, `data/processed/outlier_sensitivity_summary.csv` | Stress/outlier flags are retained for risk review rather than deleted | PASS |
| 08 | Dedicated EDA evidence with statistics and visuals | `notebooks/eda_summary.ipynb`, `src/eda.py`, `reports/tables/eda_*.csv`, `reports/figures/eda_*.png` | Executed EDA notebook shows structure, date range, missingness, summary statistics, VIX/future-vol chart, correlations, and stress observations | PASS |
| 09 | Engineered features, rationale, pipeline import | `src/features.py`, `data/processed/feature_registry.csv`, `data/processed/model_ready_volatility.csv` | Lag, rolling, VIX, yield, spread, and interaction features have rationales and leakage boundaries | PASS |
| 10a | Regression modeling, diagnostics, assumptions, metrics | `src/modeling.py`, `reports/tables/model_validation_metrics.csv`, `reports/tables/model_test_metrics.csv`, `reports/figures/residual_diagnostics.png` | TimeSeriesSplit model selection occurs only in development data; final untouched test evaluates selected `random_forest` once against naive | PASS |
| 10a | Coefficient interpretation for linear regression track | `reports/tables/linear_coefficients.csv`, `reports/figures/linear_coefficients.png`, `notebooks/modeling_evaluation_summary.ipynb` | Standardized Linear/Ridge coefficients are ranked and interpreted as predictive associations, not causal effects | PASS |
| 10b | Appropriate modeling track or time-series/classification alternative | `src/modeling.py`, `src/features.py` | Regression is appropriate for continuous volatility target; time ordering is respected with lag/rolling features and chronological splits | PASS |
| 11 | Metrics, uncertainty, two assumption scenarios, risks | `src/evaluation.py`, `reports/tables/bootstrap_mae_ci.csv`, `reports/tables/assumption_sensitivity.csv`, `reports/tables/regime_subgroup_metrics.csv` | Bootstrap CI, no-Treasury scenario, shorter-history scenario, and separate high-VIX/high-volatility subgroup diagnostics | PASS |
| 12 | Stakeholder-ready deliverable with charts and implications | `reports/volatility_risk_report.md`, `reports/figures/actual_vs_predicted_volatility.png`, `reports/figures/model_validation_comparison.png`, `reports/figures/assumption_sensitivity.png` | Executive summary, charts, assumptions, risks, bootstrap uncertainty, sensitivity, subgroup diagnostics, and “What This Means for You” | PASS |
| 13 | Productized saved model with API/dashboard and testing evidence | `app.py`, `model/model.pkl`, `notebooks/project_pipeline.ipynb` | Flask API loads model once and notebook demonstrates `/health`, `/features`, valid `/predict` 200, invalid `/predict` 400 JSON | PASS |
| 14 | Monitoring and handoff plans | `docs/monitoring_plan.md`, `docs/handoff_plan.md`, `docs/stakeholder_handoff_summary.md` | Four-layer monitoring plan with thresholds, owner, first response, rollback/retraining logic, and one-page handoff | PASS |
| 15 | Orchestration plan and runnable CLI | `docs/orchestration_plan.md`, `src/run_step.py`, `reports/pipeline.log` | 7-step DAG, idempotency, failure policy, logging, and runnable `ingest/clean/features/eda/model/evaluate/all` commands | PASS |
| 16 | Lifecycle guide, final summary, clean README/repo | `docs/lifecycle_framework_guide.md`, `docs/project_summary.md`, `README.md`, `docs/grading_checklist.md` | Lifecycle map, 2-3 page non-technical summary, setup/run/API instructions, and final audit checklist | PASS |

## Honest model-performance note

The project requirements are directly evidenced, but the corrected methodology changes the performance story. `random_forest` is selected by development-period validation, and final-test MAE improves by 8.4%. Final-test RMSE does **not** improve versus naive (-3.4%). This is documented in `README.md`, `reports/volatility_risk_report.md`, and `docs/project_summary.md` instead of being hidden.

## Latest QA evidence to refresh before submission

- `python src/run_step.py all --start-date 2018-01-01 --end-date 2026-08-26`
- `python src/run_step.py evaluate`
- Execute all notebooks:
  - `notebooks/python_fundamentals_summary.ipynb`
  - `notebooks/eda_summary.ipynb`
  - `notebooks/modeling_evaluation_summary.ipynb`
  - `notebooks/project_pipeline.ipynb`
- API checks:
  - GET `/health` -> 200
  - GET `/features` -> 200
  - POST `/predict` valid -> 200 JSON
  - POST `/predict` invalid -> 400 JSON
- `git diff --check`
- Secret scan and local absolute path scan

## Known limitations

- The API expects a complete engineered feature vector; a production dashboard would normally compute features from latest raw market data automatically.
- Bootstrap uncertainty uses row resampling for course-scope simplicity and does not fully preserve time-series dependence.
- Live data refresh depends on public Yahoo/FRED endpoint availability.
- The selected model does not beat the naive benchmark on final-test RMSE, so monitoring and benchmark comparison are essential.
