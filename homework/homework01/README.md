# Homework 01: Problem Framing and Scoping

## Specific, Actionable Problem

Portfolio and risk managers need advance notice when short-term market volatility is likely to rise, but the separate signals available from recent S&P 500 returns, VIX, realized volatility, and Treasury yields are difficult to combine consistently. This project will build and evaluate a reproducible **predictive** workflow that estimates S&P 500 realized volatility over the next five trading days using only information available at the forecast date.

The analysis will not produce an automatic trading signal or make a causal claim. It will support a human risk-review decision: whether current conditions justify enhanced monitoring and consideration of a temporary reduction in portfolio risk exposure.

## Decision, Owner, Operator, and Consumers

- **Decision owner:** the portfolio risk manager, who decides whether to escalate monitoring or recommend an exposure adjustment.
- **Operator:** a risk analyst, who refreshes the data and forecast after each trading day closes.
- **Consumers:** the portfolio risk manager and portfolio-management team.
- **Timing and workflow:** results are reviewed before the following market open and cover the next five trading days.
- **Decision trigger:** predicted five-day realized volatility above its rolling historical 80th percentile, or an optional high-volatility probability of at least 60%, triggers enhanced human review. It does not automatically execute a trade.

## Analytical Answer

The primary answer is **predictive**: an estimate of future five-day realized S&P 500 volatility. A secondary classification extension may estimate whether the next five-day period will be a high-volatility regime. Descriptive summaries will support validation and interpretation, but the project will not claim that the predictors cause future volatility.

## Measurable Success Criteria

The required regression workflow succeeds when all of the following hold on a chronological held-out test period:

1. MAE is at least 10% lower than a naive baseline that uses the most recent available five-day realized volatility.
2. RMSE is at least 5% lower than the same baseline.
3. Forecast coverage is at least 95% of eligible trading days after source alignment.
4. The final report shows the forecast, baseline comparison, error or uncertainty information, and interpretable model drivers.
5. A clean environment reproduces the processed data and evaluation outputs from documented commands without manual code edits.

If the optional classifier is delivered, it additionally targets ROC-AUC of at least 0.70 and recall of at least 0.70 for the high-volatility class. Results that miss a threshold will be reported as such rather than retroactively redefining success.

## Concrete Deliverables

- A reproducible modeling notebook containing chronological validation and baseline comparison.
- `project/data/processed/volatility_forecasts.csv`, containing dates, actuals, predictions, and evaluation-split labels.
- `project/reports/volatility_risk_report.html`, providing the current risk signal, performance summary, model drivers, assumptions, and limitations.
- `homework/homework01/stakeholder_memo.md`, summarizing the scope for a non-technical decision owner.

## Assumptions

- Historical market indicators contain some information about future short-term volatility.
- Every predictor is observable before the forecast window begins.
- Adjusted S&P 500 prices and published market indicators are sufficiently accurate for this educational analysis.
- A five-trading-day forecast horizon is relevant to the stakeholder's monitoring process.
- Historical evaluation is informative, while not guaranteeing future performance.

## Practical Constraints

- Public sources may have missing dates, revisions, rate limits, or different market calendars.
- The course timeline and computing resources favor interpretable models over a production trading platform.
- Extreme events are rare and must not be removed automatically because they are important to risk management.
- The deliverable is decision support, not investment advice or autonomous execution.
- Data alignment and feature creation must avoid look-ahead leakage.

## Known Unknowns and Risks

- Relationships among VIX, yields, recent returns, and future volatility may change across market regimes.
- VIX alone may account for most of the useful signal.
- Crisis observations may strongly influence fitted models and reported metrics.
- The high-volatility threshold may materially affect classification results.
- Strong in-sample results may not generalize to the chronological test period or future markets.
- Missing observations and inconsistent calendars may reduce usable coverage.

## Goals to Lifecycle to Deliverables Mapping

| Goal | Lifecycle stage | Deliverable |
|---|---|---|
| Define the risk decision and stakeholders | Stage 01 - Problem Framing and Scoping | This README and stakeholder memo |
| Establish a reproducible workspace | Stage 02 - Tooling Setup | Project folders, configuration helper, `.gitignore`, and requirements |
| Acquire market and macroeconomic indicators | Stage 04 - Data Acquisition | Versioned raw source snapshots and ingestion notebook |
| Preserve lineage and analysis-ready data | Stages 05-06 - Storage and Preprocessing | Raw/processed datasets, manifests, and validation checks |
| Understand data quality and relationships | Stages 07-08 - Outliers and EDA | Risk assumptions, diagnostics, and EDA report |
| Create leakage-aware predictors | Stage 09 - Feature Engineering | Feature registry and model-ready dataset |
| Predict and evaluate future volatility | Modeling and Evaluation | Model notebook, forecasts CSV, baseline comparison, and metrics |
| Communicate a decision-useful result | Reporting and Communication | Stakeholder-facing volatility risk report |

## Scope Boundary

This homework defines what will be built and how success will be assessed. It does not assert that the eventual model will meet the thresholds, and it does not authorize automated portfolio changes.
