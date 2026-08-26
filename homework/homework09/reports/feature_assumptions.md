# Stage 09 Feature Assumptions

- Predictors use information available at or before date `t`. All return rolling features are shifted before rolling so they do not use the current or future return.
- The forward five-day volatility column is a target, not a predictor. It uses only returns from `t+1` through `t+5`.
- Calendar indicators can capture recurring weekday effects, but the current short sample cannot establish that such an effect exists.
- Volume features may be associated with market activity but are not interpreted as causal.
- The current dataset provides only a small number of model-ready rows after lag and target requirements. A longer history is required before training or evaluating models.
- Feature-target correlations are used as assignment-required screening checks, not as final evidence of predictive power.
- Stage 10 modeling should use chronological train/test splitting and should not shuffle rows before the split.
