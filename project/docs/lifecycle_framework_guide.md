# Lifecycle Framework Guide

| Stage | Lifecycle focus | Project implementation | Artifact | Key decision or lesson |
| --- | --- | --- | --- | --- |
| 01 | Problem framing and scoping | Framed a stakeholder-centered volatility risk question | `README.md`, `docs/stakeholder_memo.md` | The output informs human risk review, not automated trading |
| 02 | Tooling setup | Built reproducible folders, requirements, env template, and config paths | `.env.example`, `.gitignore`, `requirements.txt`, `src/config.py` | Keep secrets local and expose relative diagnostics |
| 03 | Python fundamentals | Added reusable utilities and executed fundamentals notebook | `src/utils.py`, `notebooks/python_fundamentals_summary.ipynb` | Small helper functions reduce repeated notebook code |
| 04 | Data acquisition | Downloaded public S&P 500, VIX, and Treasury data | `src/acquisition.py`, `data/raw/*.csv` | Keyless public sources make the project reproducible |
| 05 | Data storage | Preserved raw vs processed artifacts and provenance | `data/raw/raw_data_manifest.json`, `data/processed/` | Raw data should be auditable before cleaning |
| 06 | Preprocessing | Parsed dates, sorted, aligned market dates, handled missing yields | `src/cleaning.py`, `market_data_cleaned.csv` | Forward-fill yield gaps only after aligning to market dates |
| 07 | Outlier analysis | Flagged stress observations and summarized sensitivity | `src/outliers.py`, `outlier_sensitivity_summary.csv` | Do not delete volatility spikes blindly |
| 08 | EDA | Created a dedicated executed EDA notebook plus statistics and charts | `notebooks/eda_summary.ipynb`, `src/eda.py`, `reports/figures/eda_*.png` | VIX and realized volatility are central risk-state variables |
| 09 | Feature engineering | Created leakage-safe lag, rolling, VIX, yield, and interaction features | `src/features.py`, `model_ready_volatility.csv` | Predictors use only information available at date t |
| 10 | Modeling | Used TimeSeriesSplit in development data, then one final test evaluation | `src/modeling.py`, `model/model.pkl` | `random_forest` was selected by validation, not by final test |
| 11 | Evaluation and risk communication | Added bootstrap uncertainty, assumption sensitivity, and subgroup diagnostics | `src/evaluation.py`, `reports/tables/*.csv` | Assumption scenarios are separate from market-regime slices |
| 12 | Results reporting | Wrote stakeholder-ready risk report with charts and implications | `reports/volatility_risk_report.md` | Communicate both usefulness and benchmark limitations |
| 13 | Productization | Packaged the saved model behind a Flask API | `app.py`, `model/model.pkl` | Load the model once at startup and validate inputs |
| 14 | Deployment and monitoring | Defined four-layer monitoring with thresholds and owners | `docs/monitoring_plan.md`, `docs/handoff_plan.md`, `docs/stakeholder_handoff_summary.md` | Production value depends on knowing when the model is stale or wrong |
| 15 | Orchestration and system design | Refactored the pipeline into CLI-callable steps with logging | `src/run_step.py`, `docs/orchestration_plan.md` | A notebook becomes maintainable when steps have clear I/O |
| 16 | Lifecycle review | Finalized project README, summary, guide, handoff, and checklist | `docs/project_summary.md`, `docs/grading_checklist.md` | The final repo should be legible to stakeholders and engineers |

## Handoff links

- Final stakeholder handoff: `docs/stakeholder_handoff_summary.md`
- Monitoring plan: `docs/monitoring_plan.md`
- Orchestration plan: `docs/orchestration_plan.md`
- Grading evidence checklist: `docs/grading_checklist.md`
