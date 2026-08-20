# Stage 07 Risk Assumptions

- The analysis uses Stage 06 daily returns after excluding the first row, whose zero return was inserted only because no prior close was available.
- IQR outliers use Tukey fences with multiplier `1.5`; Z-score outliers use absolute Z-score greater than `3.0`; winsorization clips returns at the 5th and 95th percentiles.
- The data contain 18 daily-return observations from January 2025. This is too small and narrow a window to characterize market tail risk.
- Removing a flagged return can remove a data error, but it can also remove a meaningful market-stress event. The original return series is therefore preserved and all three treatment results are reported.
- The volume-to-return regression is a sensitivity device, not a trading model or causal claim. Any future model must split data in time and fit preprocessing decisions on training data only.
