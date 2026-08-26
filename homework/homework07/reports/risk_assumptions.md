# Stage 07 Risk Assumptions

- The notebook uses the starter-generated 115-row dataset saved at `data/raw/outliers_homework.csv` with NumPy seed `17`.
- The primary rule is Tukey IQR with `k=1.5`; the secondary rule is absolute population Z-score above `3.0`.
- Winsorization at the 5th/95th percentiles is reported as a sensitivity treatment, not as a correction of known errors.
- IQR flags 9 observations and Z-score flags 5; all 5 Z-score flags are also IQR flags.
- IQR filtering reduces sample return standard deviation from approximately `0.0406` to `0.0094`, but regression R-squared also falls from `0.962` to `0.574` because the shared shocks carry correlation.
- Removing an extreme can remove a data error or erase a valid stress event. The original data and boolean flags are preserved, and no treatment is silently selected as “correct.”
- The regression is descriptive and in-sample. It is not a causal model, forecast, or trading rule.
- Real decisions require longer time coverage, source investigation, time-aware validation, and stakeholder approval of any exclusion rule.
