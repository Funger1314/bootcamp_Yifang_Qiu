# Stage 06: Data Preprocessing

This homework applies a reproducible preprocessing workflow to the S&P 500 price snapshot created in Stage 05.

## Workflow

1. Create a deterministic **teaching fixture** from the Stage 05 raw snapshot. The fixture introduces currency formatting, inconsistent ticker text, two missing numeric values, and one invalid date. Stage 05 source data remain unchanged.
2. Visualize and summarize missingness before cleaning.
3. Parse dates, standardize the ticker, convert formatted numeric fields, drop the invalid date, interpolate the missing closing price, and fill missing volume with the median.
4. Create `daily_return`, `close_minmax`, and `volume_zscore`; validate the model-ready table and save it as CSV and Parquet.

## Storage

- `data/raw/`: timestamped dirty teaching fixture and cleaning decisions JSON.
- `data/processed/`: validated cleaned data, in CSV and Parquet, plus a missingness heatmap.
- `.env`: local path configuration and ignored by Git. `.env.example` is the committed template.
- `src/preprocess_utils.py`: reusable functions for missingness, type correction, scaling, and validation.

## Run

From the repository root, install dependencies and start Jupyter:

```bash
pip install -r project/requirements.txt
jupyter lab
```

Copy `.env.example` to `.env` if necessary, then run all cells. The notebook expects the Stage 05 raw price CSV, which is versioned in this repository.
