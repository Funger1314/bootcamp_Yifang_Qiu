# Stage 07: Outliers and Risk Assumptions

This homework applies IQR, Z-score, and residual-based outlier checks to the Stage 06 S&P 500 daily-return data. It compares all observations, IQR-filtered observations, and 5%/95% winsorized returns in a simple sensitivity analysis.

## Key Result

With the selected thresholds, this short 18-observation return sample has no IQR or Z-score outliers. That does **not** establish that market tail risk is absent: thresholds, sample size, and time period materially affect the result. The notebook preserves all observations and documents the comparison.

## Contents

- `homework07_outliers-risk-assumptions_submission.ipynb`: executed detection, treatment comparison, and documentation.
- `data/processed/`: outlier flags and sensitivity metrics CSVs.
- `reports/`: return-distribution and sensitivity plots plus a Markdown risk-assumptions record.
- `src/outlier_utils.py`: reusable outlier and sensitivity helpers.

## Run

From the repository root:

```bash
pip install -r project/requirements.txt
jupyter lab
```

Copy `.env.example` to `.env` if it is missing, then run all cells. The notebook expects the Stage 06 cleaned Parquet dataset to be present in the repository.
