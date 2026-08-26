# Stage 08 EDA Insights

## Top 3 Insights
1. The index rose 2.93% over the observed month, but 19 prices are insufficient to establish a persistent trend or seasonality.
2. The largest daily move was -2.66% on 2025-01-10, and return skewness is -1.00; later diagnostics should retain visibility of downside tail behavior.
3. The strongest displayed correlation is `close` versus `daily_return` (0.28), which is too weak and sample-dependent to support a causal or predictive claim.

## Assumptions & Risks
- Stage 06 schema, cleaning, and trading-date coverage are assumed correct.
- The single-ticker, one-month sample excludes other assets and market regimes.
- Calendar gaps reflect non-trading days; they are not filled as if prices were observed.
- Correlation is descriptive and may be unstable in a larger or later sample.

## Implications for Next Step
- Stage 09: create lagged returns, rolling volatility, and volume-relative features using only past data.
- Stage 10b: preserve chronological order, compare against simple baselines, and evaluate performance on later unseen periods.
