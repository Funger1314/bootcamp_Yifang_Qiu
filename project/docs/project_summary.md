# Project Summary

## 1. Problem and Decision Context

Portfolio managers and risk managers need a practical way to notice when market risk is rising before it becomes a surprise in a portfolio review. This project addresses that need by forecasting short-term S&P 500 realized volatility over the next five trading days. Five trading days is a useful horizon because it is short enough to support weekly risk meetings, margin and exposure reviews, and near-term scenario discussion, but long enough to smooth some of the noise in a single daily return. The primary stakeholder is a portfolio manager or risk manager, with a risk analyst operating the workflow after market close.

The project is deliberately framed as decision support, not automated trading. Its output is a forecast and a set of diagnostics that can help a human decide whether to review exposure, ask for additional scenario analysis, or monitor a position more closely. It does not recommend buying or selling securities, and it does not claim to identify causal drivers of volatility.

## 2. Data Used

The project uses public daily data for four market indicators: the S&P 500 index, VIX, the 10-year Treasury yield, and the 2-year Treasury yield. The S&P 500 provides the return series from which realized volatility and the future target are built. VIX adds an implied-volatility and market-stress signal. The two Treasury yields provide interest-rate and term-structure context, including the 10Y minus 2Y spread. The reproducible run covers observations from 2018-01-01 through 2026-08-26, with 2,148 model-ready rows after cleaning and feature construction.

Raw files are stored separately from processed artifacts. `data/raw/` preserves source-level downloads and `raw_data_manifest.json` records provenance. `data/processed/` contains cleaned, model-ready, feature-registry, and forecast CSVs. CSV is intentionally used because it is easy to inspect, diff, and reproduce in a course setting.

## 3. How the Pipeline Works

The pipeline begins by downloading the four public data sources. It then cleans and aligns them by date, sorts observations, removes duplicate dates, validates numeric fields, and forward-fills Treasury yields across market dates where publication gaps occur. This is reasonable for short holiday or reporting gaps, but the assumption is documented because stale macro data can create risk in production.

Feature engineering converts the aligned table into a model-ready dataset. The features include lagged S&P 500 returns, rolling realized volatility, VIX level and changes, Treasury levels, the yield spread, spread changes, and a VIX-by-realized-volatility interaction. The target, `future_5d_realized_volatility`, is computed from returns after the prediction date, while all input features use information observable at or before the prediction date. This leakage boundary is the most important design rule in the pipeline.

The command-line orchestration script `src/run_step.py` runs the workflow as `ingest -> clean -> features -> eda -> model -> evaluate/report`. A Flask API in `app.py` loads the saved model once at startup and exposes `/health`, `/features`, and `/predict`.

## 4. Modeling Approach

Because the target is continuous future volatility, the project uses regression. Candidate models are Linear Regression, Ridge, and Random Forest. A naive benchmark predicts that the most recent five-day realized volatility will persist into the next five days. That benchmark is important because volatility is persistent; a model that cannot beat it is not practically useful.

The corrected methodology separates model selection from final testing. The final 20% of observations, from 2024-11-29 through 2026-08-19, is held out as the final test period. Inside the earlier development period only, `TimeSeriesSplit` compares candidate models without shuffling. The model with the lowest average validation MAE is selected, refit on the full development period, and evaluated once on the untouched final test period.

## 5. Findings

The validation process selected `random_forest`. Its average development-validation MAE is 0.004317, with validation RMSE 0.006086. On the final test period, the selected model has MAE 0.003532 and RMSE 0.006555. The naive benchmark has MAE 0.003855 and RMSE 0.006342. This means the selected model improves MAE by 8.4%, but RMSE changes by -3.4%. In plain language, the model reduces average absolute error modestly, but it does not reduce large squared errors relative to the naive benchmark.

That mixed result is still useful because it is honest. The project does not hide the fact that the naive volatility-persistence rule remains difficult to beat. A risk manager should treat the forecast as one input in a monitoring process, especially when the model and naive benchmark disagree.

## 6. Uncertainty and Sensitivity

The bootstrap MAE estimate is 0.003532, with a 95% interval from 0.003020 to 0.004048. This communicates sampling uncertainty around test-period absolute error. The limitation is that a simple row bootstrap does not fully preserve time-series dependence, so it should be read as a course-scope approximation rather than a production-grade uncertainty model.

Assumption sensitivity compares three cases on the same final test dates: the baseline selected model with all features, a version without Treasury/yield information, and a version trained only on observations from 2020 onward. In the current run, removing Treasury features has MAE 0.003265; the shorter-history scenario has MAE 0.003413. These results suggest that the model is not highly dependent on Treasury inputs in this sample and that older pre-2020 data may not be essential for the latest test period. This should be monitored rather than over-interpreted.

Regime diagnostics show that errors are larger in the hardest subgroup, `High VIX regime`, where selected-model MAE is 0.008419. That is expected in stress periods, but it is exactly where a risk model must be scrutinized most carefully.

## 7. When the Model Is Useful

The model is useful when a risk team wants a repeatable daily signal, a benchmark comparison, and structured evidence for risk review. It is most appropriate as an early-warning input: if predicted volatility is elevated, the analyst can review exposure, compare the model with naive persistence, inspect VIX and realized-volatility context, and escalate to the portfolio risk manager.

## 8. When Not to Rely on It

Do not rely on the model when input data are stale, source downloads fail, market structure changes sharply, or the model has recently underperformed the naive benchmark. Do not treat coefficients or feature importance as causal explanations. Do not use the API output as an automated trading instruction. The model can support a discussion, but accountability stays with the human decision owner.

## 9. Monitoring and Next Steps

The next step is operational monitoring: data freshness, rolling MAE/RMSE, bias, high-VIX performance, API errors, and alert frequency. If rolling errors breach thresholds or if the selected model underperforms naive for several days, the team should review features, rerun evaluation, and consider retraining or rollback. A production extension could compute feature vectors automatically from fresh market data, display forecasts in a dashboard, and add richer macro or options-derived predictors.
