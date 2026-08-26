# Stage 09: Feature Engineering

This homework creates model-ready features for the S&P 500 volatility project from the Stage 06 cleaned time series. The design keeps predictors available at time `t` and creates the future five-trading-day realized-volatility target separately.

The submission now directly addresses the Stage 09 grading rubric: at least three engineered features, a categorical encoding, clear feature rationales tied to Stage 08 EDA, reproducible helper code in `src/features.py`, and a correlation check for every engineered feature.

## Features

- Return lags: 1-day and 3-day lagged daily returns.
- Rolling features: 3-day prior return mean and 5-day prior return volatility.
- Volume features: 1-day percent change, relative volume versus prior 5-day average, and log volume.
- Price feature: close relative to its prior 3-day average.
- Calendar encoding: one-hot encoded day-of-week indicators.
- Interaction: lagged return multiplied by 1-day volume change.
- Target: forward 5-day realized volatility, computed only from returns after time `t`.

## Stage 08 EDA Connection

- Stage 08 found a short chronological January 2025 sample with no missing values after cleaning, so the Stage 09 notebook uses time-aware lag and rolling features instead of random-row transformations.
- Daily returns showed meaningful short-run variation, motivating `return_lag_1`, `return_lag_3`, `return_rolling_mean_3`, and `return_rolling_volatility_5`.
- Volume had a much larger scale than returns, motivating `log_volume`, `volume_pct_change_1`, and `volume_relative_to_5d`.
- Calendar information is available before modeling, so weekday one-hot features provide the required categorical encoding while avoiding look-ahead leakage.

## Correlation Check

The notebook writes `data/processed/feature_target_checks.csv` and `reports/feature_target_correlations.png`. In the current small sample, the strongest screening relationships with future 5-day realized volatility are `close_relative_to_3d`, `return_lag_1`, `weekday_Monday`, `volume_pct_change_1`, and `return_lag_1_x_volume_change_1`. These are treated as feature-screening evidence only because the model-ready sample has 8 rows.

## Provided Materials Assessment

- `stage09_feature-engineering_lecture-notebook.ipynb` informed the rolling, encoding, interaction, and temporal-feature design.
- `env.example` is useful as a configuration-template example, but its dummy API key and generic path are not used. This submission provides a project-specific `.env.example` instead.
- `starter_data.csv` is a generic category/value/date practice table. It is not merged into this finance project because it has no market or volatility fields.

## Contents

- `homework09_feature-engineering_submission.ipynb`: executed feature-engineering workflow.
- `data/processed/`: full engineered data, model-ready data, feature registry, feature rationale, target checks, and provenance metadata.
- `reports/`: feature overview chart, feature-target correlation chart, and assumption record.
- `src/features.py`: reusable leakage-aware feature and validation functions required by the assignment.
- `src/feature_utils.py`: compatibility wrapper for older imports.
- `tests/test_features.py`: lightweight regression tests for feature generation and validation.

## Run

From the repository root:

```bash
pip install -r project/requirements.txt
jupyter lab
```

Copy `.env.example` to `.env` if needed, then run all cells. The notebook expects the Stage 06 cleaned Parquet dataset already versioned in this repository.
