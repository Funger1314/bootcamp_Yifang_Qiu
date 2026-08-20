# Stage 03: Python Fundamentals

This submission applies NumPy and pandas skills to a small, illustrative market-stress dataset that supports the broader S&P 500 volatility project.

## Contents

- `homework03_python-fundamentals_submission.ipynb`: completed homework notebook.
- `data/raw/starter_data.csv`: illustrative input data used for the assignment.
- `data/processed/summary.csv`: market-regime aggregation produced by the notebook.
- `data/processed/numeric_summary.csv`: descriptive statistics produced by the notebook.
- `data/processed/vix_by_date.png`: optional plot produced by the notebook.
- `src/utils.py`: reusable summary-statistics function.

## Run

From the repository root, install the project dependencies and open the notebook:

```bash
pip install -r project/requirements.txt
jupyter lab
```

Run all notebook cells. The output files in `data/processed/` will be recreated from `data/raw/starter_data.csv`.

The input data are deliberately small and illustrative. They are for practicing the Stage 03 workflow, not for market analysis or investment decisions.
