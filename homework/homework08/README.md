# Stage 08: Exploratory Data Analysis

This homework explores the cleaned S&P 500 data from Stage 06 and uses the same 18 valid daily returns analyzed in Stage 07. It profiles distributions, visualizes relationships, inspects the short time series, calculates correlations, and documents modeling implications.

## Contents

- `homework08_exploratory-data-analysis_submission.ipynb`: executed EDA workflow.
- `data/processed/`: numeric profile, correlation matrix, and machine-readable EDA summary.
- `reports/`: distribution, relationship, time-series, correlation charts, and written insight record.
- `src/eda_utils.py`: reusable profiling and correlation helpers.

## Interpretation Boundary

The data cover only 18 usable daily returns in January 2025. These visuals are useful for validating the workflow and identifying feature hypotheses, but they are not sufficient to establish stable market relationships or a predictive trading strategy.

## Run

From the repository root:

```bash
pip install -r project/requirements.txt
jupyter lab
```

Copy `.env.example` to `.env` if needed, then run all cells. The notebook expects the Stage 06 cleaned Parquet dataset already versioned in the repository.
