# Predicting Short-Term S&P 500 Volatility Using Market Stress and Interest Rate Indicators

Author: Yifang Qiu

## Project summary

This project predicts future 5-trading-day realized S&P 500 volatility using market stress and interest-rate indicators. The primary stakeholder is a portfolio manager or risk manager who needs an interpretable daily risk-monitoring signal, not an automated trading rule.

The final pipeline downloads public market data, stores raw and processed artifacts, cleans and aligns the series, flags risk-relevant outliers, builds leakage-safe features, trains regression models with a chronological split, evaluates model risk, and packages the result as a stakeholder report and Flask prediction API.

## Stakeholder and decision

The decision owner is a portfolio risk manager. A risk analyst can run the pipeline after the market close, review the next-five-day volatility forecast, and escalate when predicted volatility is materially elevated. The output supports monitoring and exposure review; it does not execute trades.

## Data sources

- S&P 500 index daily OHLCV from Yahoo Finance chart data (`^GSPC`)
- VIX daily OHLCV from Yahoo Finance chart data (`^VIX`)
- 10-year Treasury yield from FRED (`DGS10`)
- 2-year Treasury yield from FRED (`DGS2`)

The committed raw-data manifest is `data/raw/raw_data_manifest.json`. The default reproducible sample starts on `2018-01-01` and currently contains 2,148 model-ready rows after alignment and leakage-safe feature construction.

## Target and features

Target: `future_5d_realized_volatility`, the population standard deviation of S&P 500 daily returns from t+1 through t+5.

Key feature groups:

- recent S&P 500 returns and rolling realized volatility
- VIX level, change, and percentage change
- 10-year and 2-year Treasury yield levels
- 10Y minus 2Y yield spread and recent spread change
- interaction between VIX and recent realized volatility

Feature definitions and rationales are saved in `data/processed/feature_registry.csv`.

## Modeling results

The project uses regression because the target is continuous future volatility. The split is chronological, not random.

| Model | MAE | RMSE | R2 | MAE improvement vs naive | RMSE improvement vs naive |
| --- | ---: | ---: | ---: | ---: | ---: |
| Naive last 5d realized vol | 0.003855 | 0.006342 | -0.176 | 0.0% | 0.0% |
| Linear Regression | 0.002775 | 0.004688 | 0.358 | 28.0% | 26.1% |
| Ridge | 0.002774 | 0.004688 | 0.358 | 28.0% | 26.1% |
| Random Forest | 0.003532 | 0.006555 | -0.256 | 8.4% | -3.4% |

The selected model is Ridge. It meets the project success criteria of at least 10% MAE improvement and 5% RMSE improvement versus the naive persistence baseline.

Bootstrap selected-model MAE: 0.002774, 95% CI [0.002426, 0.003127] using 1,000 bootstrap resamples of test residual errors. A row bootstrap is used for course-scope simplicity; the limitation is that daily financial residuals can be serially dependent.

## Important limitations

- The model is predictive, not causal.
- Volatility regimes can shift; performance should be monitored over rolling windows.
- Yahoo/FRED availability can affect reproducibility during live data refreshes.
- Treasury yield values are forward-filled across market dates after publication gaps.
- Extreme returns are retained because they are the observations a risk manager cares about most.

## Project structure

```text
project/
├── app.py
├── requirements.txt
├── README.md
├── .env.example
├── data/
│   ├── raw/
│   └── processed/
├── docs/
├── model/
├── notebooks/
├── reports/
│   ├── figures/
│   └── tables/
└── src/
```

## Setup

From a fresh clone:

```bash
cd project
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

On macOS/Linux, activate with:

```bash
source .venv/bin/activate
```

## Reproduce the project

Run the full end-to-end pipeline:

```bash
python src/run_step.py all --start-date 2018-01-01
```

Run individual orchestration steps:

```bash
python src/run_step.py ingest
python src/run_step.py clean
python src/run_step.py features
python src/run_step.py eda
python src/run_step.py model
python src/run_step.py evaluate
```

Run the cumulative notebook:

```bash
jupyter execute notebooks/project_pipeline.ipynb --inplace
```

## Run the API

After `python src/run_step.py all` has produced `model/model.pkl`:

```bash
python app.py
```

Health check:

```bash
curl http://127.0.0.1:5000/health
```

Feature list:

```bash
curl http://127.0.0.1:5000/features
```

Prediction with a feature object:

```bash
curl -X POST http://127.0.0.1:5000/predict ^
  -H "Content-Type: application/json" ^
  -d "{\"features\":{\"sp500_return_lag_1\":0.001,\"sp500_return_lag_3\":-0.002,\"sp500_return_rolling_mean_5\":0.0005,\"realized_volatility_5d\":0.008,\"realized_volatility_10d\":0.009,\"realized_volatility_21d\":0.010,\"vix_close\":18.0,\"vix_change\":0.4,\"vix_pct_change\":0.02,\"treasury_10y\":4.1,\"treasury_2y\":3.9,\"yield_spread_10y_2y\":0.2,\"yield_spread_change_5d\":0.03,\"vix_x_realized_vol_5d\":0.144}}"
```

Bad input returns JSON with HTTP 400 instead of a traceback.

## Lifecycle map

| Stage | Implementation | Main artifact |
| --- | --- | --- |
| 01 Problem framing | Stakeholder-centered volatility risk question | `README.md`, `docs/stakeholder_memo.md` |
| 02 Tooling setup | Reproducible folder structure, env template, requirements | `.env.example`, `.gitignore`, `requirements.txt`, `src/config.py` |
| 03 Python fundamentals | Reusable utilities and fundamentals notebook | `src/utils.py`, `notebooks/python_fundamentals_summary.ipynb` |
| 04 Acquisition | Public Yahoo/FRED download functions | `src/acquisition.py`, `data/raw/` |
| 05 Storage | Raw/processed separation and manifest | `data/raw/raw_data_manifest.json`, `data/processed/` |
| 06 Preprocessing | Cleaning, alignment, missingness handling | `src/cleaning.py`, `data/processed/market_data_cleaned.csv` |
| 07 Outliers | Flag stress/outlier rows rather than deleting them | `src/outliers.py`, `data/processed/outlier_sensitivity_summary.csv` |
| 08 EDA | Summary tables and project-specific charts | `src/eda.py`, `reports/figures/eda_*.png` |
| 09 Features | Leakage-safe volatility features and target | `src/features.py`, `data/processed/model_ready_volatility.csv` |
| 10 Modeling | Naive, linear, Ridge, and Random Forest regressors | `src/modeling.py`, `model/model.pkl` |
| 11 Evaluation | Bootstrap CI, scenarios, regime diagnostics | `src/evaluation.py`, `reports/tables/` |
| 12 Reporting | Stakeholder-ready written report and charts | `reports/volatility_risk_report.md` |
| 13 Productization | Flask API loading saved model once | `app.py`, `model/model.pkl` |
| 14 Monitoring | Four-layer monitoring and handoff plans | `docs/monitoring_plan.md`, `docs/handoff_plan.md` |
| 15 Orchestration | CLI task runner and logging | `src/run_step.py`, `reports/pipeline.log` |
| 16 Lifecycle review | Final summary and framework guide | `docs/lifecycle_framework_guide.md`, `docs/project_summary.md` |

## Generated artifacts

- `data/raw/*.csv`
- `data/raw/raw_data_manifest.json`
- `data/processed/market_data_cleaned.csv`
- `data/processed/model_ready_volatility.csv`
- `data/processed/feature_registry.csv`
- `data/processed/volatility_forecasts.csv`
- `model/model.pkl`
- `model/model_metadata.json`
- `reports/tables/*.csv`
- `reports/figures/*.png`
- `reports/volatility_risk_report.md`
- `reports/pipeline.log`

## Documentation

- `docs/stakeholder_memo.md`
- `docs/monitoring_plan.md`
- `docs/handoff_plan.md`
- `docs/orchestration_plan.md`
- `docs/lifecycle_framework_guide.md`
- `docs/project_summary.md`
- `docs/grading_checklist.md`
