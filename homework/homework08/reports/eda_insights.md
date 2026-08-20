# Stage 08 EDA Insights

- The analysis contains 18 usable daily returns and no missing values after Stage 06 preprocessing.
- The largest absolute return was 1.83% on 2025-01-15. This observation remains below the Stage 07 IQR and Z-score thresholds, but it should remain visible in later model diagnostics.
- The strongest non-duplicate correlation is between `close` and `daily_return` (0.19). Correlation in this short sample is descriptive, not causal.
- Next feature hypotheses: lagged returns, rolling volatility, and volume-relative features. Each must be calculated without using future observations.
- Limitation: January 2025 alone cannot represent calm, stressed, or changing market regimes. A longer data history is required before model evaluation.
