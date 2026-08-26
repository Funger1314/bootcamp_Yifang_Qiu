# Stage 06: Data Preprocessing

This homework applies the three required reusable cleaning functions to a controlled S&P 500 price fixture derived from the Stage 05 raw snapshot. The original Stage 05 data remain unchanged.

## Required Deliverables

- `src/cleaning.py`: documented implementations of `fill_missing_median()`, `drop_missing()`, and `normalize_data()`.
- `homework06_data-preprocessing_submission.ipynb`: executed demonstration that imports and applies all three functions.
- `data/raw/sp500_prices_dirty_fixture_20260820-050305.csv`: provided raw teaching fixture.
- `data/processed/sp500_prices_cleaned.csv`: canonical cleaned dataset produced by the notebook.
- `data/processed/cleaning_comparison.csv`: original-versus-cleaned quality metrics.
- `data/processed/cleaning_metadata.json`: machine-readable assumptions, decisions, validation, and output paths.

## Cleaning Strategy

| Issue | Function or rule | Reason | Tradeoff |
|---|---|---|---|
| Invalid date | `drop_missing(..., subset=["date"])` after coercion | A row without a valid date cannot be placed in the chronological series | Row deletion can bias results if invalid dates are systematic |
| Missing close | `fill_missing_median(..., ["close"])` | Demonstrates the required robust, deterministic imputation | Median filling reduces variability and does not preserve local time-series movement |
| Missing volume | `fill_missing_median(..., ["volume"])` | Volume is skewed; the median is less sensitive to extremes than the mean | Imputation can understate unusual trading activity |
| Close scale | `normalize_data(..., method="minmax")` | Produces a bounded [0, 1] feature for comparison | New extremes can move the fitted range |
| Volume scale | `normalize_data(..., method="zscore")` | Expresses volume relative to this sample's mean and dispersion | Production models must fit scaling parameters on training data only |
| Formatted numerics and ticker text | Currency/comma removal plus trim/uppercase | Restores numeric types and a consistent identifier | Unexpected formats are converted to missing and must pass validation |

## Workflow

1. Load the committed dirty fixture from `data/raw/`.
2. Compare data types, missingness, row counts, and numeric summaries before cleaning.
3. Parse dates and formatted numerics, then explicitly demonstrate all three functions from `src/cleaning.py`.
4. Create `daily_return`, `close_minmax`, and `volume_zscore`; compare original and cleaned data.
5. Validate the final schema and values, then save stable CSV, Parquet, comparison, and metadata outputs.

## Assumptions

- The fixture's missing values and invalid date were deliberately introduced for learning; they do not establish an MCAR, MAR, or MNAR mechanism in real market data.
- Rows are ordered chronologically after date validation.
- Prices must be positive and volume must be nonnegative.
- Median imputation is used because the homework requires it, not because it is automatically optimal for every financial time series.
- Scaling in this homework is descriptive. A predictive pipeline must fit scaling parameters on training data only to prevent leakage.

## Storage

- `data/raw/`: source-faithful dirty teaching fixture and prior-run lineage metadata.
- `data/processed/`: canonical cleaned CSV/Parquet, comparison table, metadata, and missingness visualization. Timestamped files are retained as prior-run evidence for downstream stages.
- `.env`: local path configuration and ignored by Git. `.env.example` is the committed template.
- `src/cleaning.py`: the three required general cleaning functions.
- `src/preprocess_utils.py`: the market-specific composition and validation layer that imports the required functions.
- `tests/test_cleaning.py`: correctness and edge-case tests.

## Run

From the repository root, install dependencies and start Jupyter:

```bash
pip install -r project/requirements.txt
jupyter lab
```

Copy `.env.example` to `.env` if necessary, then run all notebook cells from the repository root. To run the function tests:

```bash
python -m unittest discover -s homework/homework06/tests -v
```

The notebook is committed with successful execution outputs and performs a reload check on the saved processed dataset.
