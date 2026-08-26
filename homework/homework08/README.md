# Stage 08: Exploratory Data Analysis

This homework explores the canonical cleaned S&P 500 dataset from Stage 06. It profiles 19 January 2025 price observations and 18 valid daily returns, visualizes distributions and relationships, inspects the short time series, calculates correlations, and documents modeling implications. Stage 07 uses a separate instructional dataset, so its results are not treated as directly comparable.

## Contents

- `homework08_exploratory-data-analysis_submission.ipynb`: executed EDA workflow.
- `data/processed/`: stable numeric profile, categorical profile, correlation matrix, and machine-readable EDA summary.
- `reports/`: distribution, relationship, time-series, correlation charts, and written insight record.
- `src/eda.py`: required reusable `eda_summary()` and correlation helpers.
- `src/eda_utils.py`: backward-compatible import wrapper.

## Interpretation Boundary

The data cover only 18 usable daily returns in January 2025. The index rose 2.93% from the first to the last observation, but this short window cannot establish seasonality or a persistent trend. These visuals validate the workflow and identify feature hypotheses; they do not establish causal relationships or a predictive trading strategy.

## Run

From the repository root:

```bash
pip install -r project/requirements.txt
jupyter lab
```

Copy `.env.example` to `.env` if needed, then run all cells. The notebook reads the canonical Stage 06 file at `homework/homework06/data/processed/sp500_prices_cleaned.parquet` and overwrites stable Stage 08 output filenames, so repeated runs are reproducible and do not create timestamped duplicates.
