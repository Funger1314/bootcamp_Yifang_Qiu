# Homework 02: Tooling Setup

This submission demonstrates a reproducible local setup for the S&P 500 volatility project and connects the homework configuration exercise to the live `project/` scaffold.

## Submission Files

- `homework02_tooling-setup_submission.ipynb` - completed and executed environment, `.env`, path, and NumPy checks.
- `.env.example` - safe configuration template with no real secret.
- `.gitignore` - prevents the local `.env` file from being committed.

## Live Project Contribution

The corresponding project scaffold is in `../../project/` and includes:

- `data/raw/` and `data/processed/`
- `notebooks/`, `src/`, `docs/`, `reports/`, and `model/`
- `.gitignore`, `.env.example`, `README.md`, and `requirements.txt`
- `src/config.py`, the reusable configuration helper adapted from this homework

Empty project folders contain `.gitkeep` files so they remain visible on GitHub.

## Reproduce the Notebook

From this folder:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install numpy python-dotenv jupyter nbconvert
cp .env.example .env      # Windows PowerShell: Copy-Item .env.example .env
jupyter nbconvert --to notebook --execute --inplace homework02_tooling-setup_submission.ipynb
```

The committed notebook contains saved outputs from a successful top-to-bottom run. The local `.env` file is ignored and must never contain a secret that is committed to Git.
