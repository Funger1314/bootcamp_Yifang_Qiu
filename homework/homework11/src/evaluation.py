import numpy as np

class SimpleLinReg:
    def fit(self, X, y, quadratic=False):
        x = np.asarray(X, dtype=float).ravel()
        y = np.asarray(y, dtype=float).ravel()
        if quadratic:
            X1 = np.c_[np.ones(len(x)), x, x**2]
        else:
            X1 = np.c_[np.ones(len(x)), x]
        beta = np.linalg.pinv(X1) @ y
        self.intercept_ = float(beta[0])
        self.coef_ = np.asarray(beta[1:], dtype=float)
        self.quadratic_ = bool(quadratic)
        return self

    def predict(self, X):
        x = np.asarray(X, dtype=float).ravel()
        if self.quadratic_:
            return self.intercept_ + self.coef_[0] * x + self.coef_[1] * x**2
        return self.intercept_ + self.coef_[0] * x

def mean_impute(a):
    a = np.asarray(a, dtype=float).copy()
    fill = float(np.nanmean(a))
    a[np.isnan(a)] = fill
    return a

def median_impute(a):
    a = np.asarray(a, dtype=float).copy()
    fill = float(np.nanmedian(a))
    a[np.isnan(a)] = fill
    return a

def mae(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return float(np.mean(np.abs(y_true - y_pred)))

def rmse(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return float(np.sqrt(np.mean((y_true - y_pred)**2)))

def bias(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return float(np.mean(y_true - y_pred))

def bootstrap_abs_error_ci(residuals, n_boot=2000, seed=111, alpha=0.05):
    residuals = np.asarray(residuals, dtype=float)
    rng = np.random.default_rng(seed)
    vals = np.empty(n_boot)
    idx = np.arange(len(residuals))
    for b in range(n_boot):
        sample = rng.choice(idx, size=len(idx), replace=True)
        vals[b] = np.mean(np.abs(residuals[sample]))
    lo, hi = np.percentile(vals, [100*alpha/2, 100*(1-alpha/2)])
    return {
        "estimate": float(np.mean(np.abs(residuals))),
        "bootstrap_mean": float(vals.mean()),
        "lo": float(lo),
        "hi": float(hi),
        "samples": vals,
    }

def gaussian_mean_prediction_ci(x, y, x_grid):
    x = np.asarray(x, dtype=float).ravel()
    y = np.asarray(y, dtype=float).ravel()
    x_grid = np.asarray(x_grid, dtype=float).ravel()

    model = SimpleLinReg().fit(x, y)
    pred = model.predict(x_grid)
    resid = y - model.predict(x)

    n = len(x)
    sigma_hat = np.sqrt(np.sum(resid**2) / (n - 2))
    xbar = x.mean()
    sxx = np.sum((x - xbar)**2)
    se = sigma_hat * np.sqrt(1/n + (x_grid - xbar)**2 / sxx)

    lo = pred - 1.96 * se
    hi = pred + 1.96 * se
    return pred, lo, hi

def bootstrap_prediction_band(x_raw, y, x_grid, n_boot=1500, seed=111):
    x_raw = np.asarray(x_raw, dtype=float).ravel()
    y = np.asarray(y, dtype=float).ravel()
    x_grid = np.asarray(x_grid, dtype=float).ravel()

    rng = np.random.default_rng(seed)
    idx = np.arange(len(y))
    P = np.empty((n_boot, len(x_grid)))

    for b in range(n_boot):
        sample = rng.choice(idx, size=len(idx), replace=True)
        xb_raw = x_raw[sample]
        yb = y[sample]
        xb = mean_impute(xb_raw)
        m = SimpleLinReg().fit(xb, yb)
        P[b] = m.predict(x_grid)

    return (
        P.mean(axis=0),
        np.percentile(P, 2.5, axis=0),
        np.percentile(P, 97.5, axis=0),
    )
