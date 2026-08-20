# Predicting Short-Term S&P 500 Volatility Using Market Stress and Interest Rate Indicators

**Current progress:** Stages 01-06 complete - problem framing, tooling setup, Python fundamentals, data acquisition, storage, and preprocessing.

## Problem Statement

Financial markets can experience sudden changes in volatility, creating challenges for portfolio managers and risk managers who need to monitor and control short-term market risk. While indicators such as the VIX, Treasury yields, and recent market volatility contain information about current market conditions, it is not always clear how useful they are for anticipating volatility over the next several trading days.

This project aims to examine whether market stress and interest-rate indicators can help predict short-term S&P 500 volatility. The initial analysis will focus on variables such as the S&P 500, VIX, 10-year Treasury yield, 2-year Treasury yield, recent returns, and rolling volatility. The primary prediction target will be realized S&P 500 volatility over the next five trading days. The goal is not to create a direct trading signal, but to develop a risk-monitoring framework that helps users identify periods when market volatility may increase.

## Stakeholder & User

The primary stakeholder is a **portfolio manager or risk manager** responsible for monitoring short-term market risk and portfolio exposure.

The stakeholder would use the project output to better understand whether current financial-market conditions indicate an elevated probability of higher volatility in the near future.

Key stakeholder concerns include:

* Whether market volatility is likely to increase over the next five trading days.
* Which indicators are most informative for short-term volatility.
* How reliable the model is during both normal and stressed market conditions.
* Whether the results are sufficiently interpretable to support risk-management decisions.

The analysis could be reviewed as part of a regular portfolio risk-monitoring process.

## Useful Answer & Decision

The primary task is **predictive**.

The main output will be an estimate of **future 5-day realized S&P 500 volatility** based on information available at the current time.

Possible model inputs include:

* VIX level and recent changes in VIX
* Recent S&P 500 returns
* Recent realized volatility
* 10-year Treasury yield
* 2-year Treasury yield
* 10-year minus 2-year Treasury yield spread

The project may also convert future volatility into a classification problem by defining a **high-volatility regime** and estimating the probability that the market will enter that regime during the next five trading days.

Model performance may be evaluated using metrics such as:

* MAE
* RMSE
* R² for regression
* Precision
* Recall
* F1 score
* ROC-AUC for classification

The final deliverable should help the stakeholder decide whether current conditions justify increased risk monitoring or changes in portfolio risk exposure.

## Assumptions & Constraints

* Historical market data are assumed to contain useful information about future short-term volatility.
* Market indicators must be available before the prediction period to avoid look-ahead bias.
* Different financial series may have missing observations because of weekends, holidays, or different reporting schedules.
* Daily observations from different datasets will need to be aligned by date.
* The project will initially use a limited number of interpretable financial indicators rather than a very large feature set.
* Extreme market events will not automatically be removed because they may contain important information for risk management.
* Historical relationships may change over time because financial markets operate under different economic and policy regimes.
* The project is designed as an analytical and risk-monitoring tool rather than a production trading system.

## Known Unknowns / Risks

* The relationship between VIX, interest rates, and future realized volatility may not remain stable across different market periods.
* VIX may explain a large portion of volatility by itself, making additional variables less useful.
* Extreme periods such as market crashes may have a large influence on model estimates.
* The definition of a "high-volatility" regime may affect classification results.
* Model performance may vary substantially between normal market periods and crisis periods.
* Strong in-sample performance may not translate into good out-of-sample performance.
* Additional preprocessing may be required if financial datasets contain missing values or inconsistent trading dates.

These risks will be examined through model evaluation, sensitivity analysis, and comparison of performance across different time periods.

## Lifecycle Mapping

Goal → Stage → Deliverable

* Define the financial risk problem and identify the stakeholder → **Problem Framing & Scoping (Stage 01)** → Problem statement and stakeholder memo
* Establish a reproducible project structure → **Tooling Setup (Stage 02)** → Organized GitHub repository and development environment
* Build reusable Python functions → **Python Fundamentals (Stage 03)** → Utility functions and Python notebook
* Collect financial market indicators → **Data Acquisition / Ingestion (Stage 04)** → Reproducible API and web-scraping ingestion workflow
* Organize and preserve collected data → **Data Storage (Stage 05)** → Versioned raw CSVs, processed Parquet data, and JSON lineage manifests
* Clean and align financial time series → **Data Preprocessing (Stage 06)** → Validated, type-corrected and scaled analysis-ready dataset
* Investigate extreme market observations → **Outlier Analysis** → Outlier and sensitivity analysis
* Understand relationships among variables → **Exploratory Data Analysis** → Summary statistics and visualizations
* Construct predictive variables → **Feature Engineering** → Model-ready feature set
* Predict future 5-day volatility → **Modeling** → Regression and/or time-series model
* Identify future high-volatility regimes → **Modeling** → Classification model
* Evaluate model reliability and sensitivity → **Evaluation & Risk Communication** → Performance metrics and risk assessment
* Communicate findings to stakeholders → **Results Reporting & Stakeholder Communication** → Final notebook, charts, and presentation

## Repo Plan

The project uses the following repository structure:

```text
project/
├── data/
│   ├── raw/
│   └── processed/
├── notebooks/
├── src/
├── docs/
├── reports/
├── model/
├── requirements.txt
└── README.md
```

## Folder Purpose
data/raw/ — original datasets collected from external sources.
data/processed/ — cleaned and transformed datasets ready for analysis.
notebooks/ — Jupyter notebooks for exploration, preprocessing, modeling, and evaluation.
src/ — reusable Python functions and project utilities.
docs/ — stakeholder-facing documentation.
reports/ — generated reports, figures, and analytical outputs.
model/ — saved model files and model-related artifacts.
requirements.txt — Python dependencies required to reproduce the project environment.

## Setup

Create and activate a virtual environment, then install the project dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The Stage 03 homework is available in `../homework/homework03/`. It demonstrates the foundational NumPy and pandas workflow used by the Stage 04 ingestion notebook in `../homework/homework04/`, the Stage 05 storage workflow in `../homework/homework05/`, and the Stage 06 preprocessing workflow in `../homework/homework06/`.
