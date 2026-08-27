# Orchestration and System Design Plan

## Task decomposition

| Task | Purpose | Inputs | Outputs | Dependencies | Idempotent |
| --- | --- | --- | --- | --- | --- |
| ingest | Download raw public market data | Yahoo/FRED endpoints, dates | `data/raw/*.csv`, `raw_data_manifest.json` | none | Yes; overwrites same raw filenames for the configured date range |
| clean | Align S&P 500, VIX, and Treasury series | `data/raw/*.csv` | `data/processed/market_data_cleaned.csv` | ingest | Yes; deterministic transforms |
| features | Build leakage-safe predictors and target | cleaned CSV | `model_ready_volatility.csv`, `feature_registry.csv` | clean | Yes; deterministic rolling/lag logic |
| eda | Create project EDA tables and charts | model-ready CSV | `reports/tables/eda_*.csv`, `reports/figures/eda_*.png` | features | Yes; overwrites generated outputs |
| model | Train benchmark and candidate regressors | model-ready CSV | `model/model.pkl`, `model_metadata.json`, forecasts, metrics | features | Yes; fixed random seed for Random Forest |
| evaluate | Run uncertainty, scenario, and sensitivity analysis | model-ready CSV, model outputs | evaluation tables, charts, report | model | Yes; bootstrap seed fixed |
| report/API | Package stakeholder and product outputs | model/evaluation artifacts | `volatility_risk_report.md`, `app.py` responses | evaluate | Yes for report; API is read-only at request time |

## Dependencies

```text
ingest -> clean -> features -> eda
                         \-> model -> evaluate -> report/API
```

EDA can run after features and does not block model training conceptually, but in this small course project both are run sequentially for simpler logging and reproducibility.

## Logging and checkpoints

The CLI writes to `reports/pipeline.log`. Each task logs start, completion, selected model, and row counts where relevant. Checkpoints are the saved files in `data/raw/`, `data/processed/`, `model/`, `reports/tables/`, and `reports/figures/`. A failed task should be rerun from its nearest upstream checkpoint. For example, if evaluation fails, rerun `python src/run_step.py evaluate` after verifying `data/processed/model_ready_volatility.csv` exists.

## Failure points and retry policy

- Network/data-source failure: retry `ingest` once after checking connectivity; if still failing, do not publish new forecasts.
- Schema change: stop the pipeline and update `src/acquisition.py` or `src/cleaning.py`; this is not safe to auto-retry.
- Modeling failure: inspect feature completeness and missingness; rerun `features`, then `model`.
- Reporting failure: rerun `evaluate`; charts and tables are generated deterministically.
- API failure: confirm `model/model.pkl` exists and restart `python app.py`.

## Automation decisions

Automate ingestion through evaluation because these are deterministic, reproducible tasks. Keep portfolio action, retraining approval after unusual stress events, and model rollback decisions manual because they require risk judgment and accountability.

## CLI wrapper

The runnable orchestration proof is `src/run_step.py`.

```bash
python src/run_step.py all
python src/run_step.py ingest
python src/run_step.py clean
python src/run_step.py features
python src/run_step.py model
python src/run_step.py evaluate
```
