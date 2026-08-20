# Stage 09: Feature Engineering

This homework creates model-ready features for the S&P 500 volatility project from the Stage 06 cleaned time series. The design keeps predictors available at time `t` and creates the future five-trading-day realized-volatility target separately.

## Features

- Return lags: 1-day and 3-day lagged daily returns.
- Rolling features: 3-day prior return mean and 5-day prior return volatility.
- Volume features: 1-day percent change, relative volume versus prior 5-day average, and log volume.
- Price feature: close relative to its prior 3-day average.
- Calendar encoding: one-hot encoded day-of-week indicators.
- Interaction: lagged return multiplied by 1-day volume change.
- Target: forward 5-day realized volatility, computed only from returns after time `t`.

## Provided Materials Assessment

- `stage09_feature-engineering_lecture-notebook.ipynb` informed the rolling, encoding, interaction, and temporal-feature design.
- `env.example` is useful as a configuration-template example, but its dummy API key and generic path are not used. This submission provides a project-specific `.env.example` instead.
- `starter_data.csv` is a generic category/value/date practice table. It is not merged into this finance project because it has no market or volatility fields.

## Contents

- `homework09_feature-engineering_submission.ipynb`: executed feature-engineering workflow.
- `data/processed/`: full engineered data, model-ready data, feature registry, and provenance metadata.
- `reports/`: feature overview chart and assumption record.
- `src/feature_utils.py`: reusable leakage-aware feature and validation functions.

## Run

From the repository root:

```bash
pip install -r project/requirements.txt
jupyter lab
```

Copy `.env.example` to `.env` if needed, then run all cells. The notebook expects the Stage 06 cleaned Parquet dataset already versioned in this repository.
