"""Model training and diagnostics for future volatility prediction.

The modeling workflow deliberately separates model selection from final
evaluation. Candidate models are compared only inside the development period
using time-aware cross-validation with a five-row gap. The final chronological
test period remains untouched until the selected model is refit on all
development data. A five-row purge gap prevents overlapping forward target
windows from leaking validation/test-period returns into training labels.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.config import MODEL_DIR, REPORTS_DIR
from src.features import BASE_FEATURES, TARGET_COLUMN
from src.utils import write_json


NAIVE_MODEL_NAME = "naive_last_5d_realized_vol"
TARGET_HORIZON_ROWS = 5
PURGE_GAP_ROWS = 5


def chronological_train_test_split(
    dataframe: pd.DataFrame,
    test_size: float = 0.2,
    purge_gap_rows: int = PURGE_GAP_ROWS,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split time-series rows chronologically with a purge gap before test.

    The target uses returns from t+1 through t+5. Purging the five rows
    immediately before the final test start prevents development labels from
    using any return belonging to the final-test period.
    """

    if not 0 < test_size < 1:
        raise ValueError("test_size must be between zero and one")
    if purge_gap_rows < 0:
        raise ValueError("purge_gap_rows must be non-negative")
    data = dataframe.sort_values("date").reset_index(drop=True)
    split_index = int(len(data) * (1 - test_size))
    if split_index <= 0 or split_index >= len(data):
        raise ValueError("Invalid split produced an empty development or test set")
    development_end_index = split_index - purge_gap_rows
    if development_end_index <= 0:
        raise ValueError("Purge gap produced an empty development set")
    development = data.iloc[:development_end_index].copy()
    purged = data.iloc[development_end_index:split_index].copy()
    test = data.iloc[split_index:].copy()
    return development, test, purged


def regression_pipeline(model) -> Pipeline:
    """Build a sklearn pipeline with imputation, scaling, and a regressor."""

    return Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("model", model),
        ]
    )


def candidate_model_factories() -> dict[str, Callable[[], Pipeline]]:
    """Return fresh model pipelines for each candidate used in validation."""

    return {
        "linear_regression": lambda: regression_pipeline(LinearRegression()),
        "ridge": lambda: regression_pipeline(Ridge(alpha=1.0)),
        "random_forest": lambda: Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                (
                    "model",
                    RandomForestRegressor(
                        n_estimators=250,
                        max_depth=6,
                        min_samples_leaf=8,
                        random_state=42,
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
    }


def build_model_by_name(model_name: str) -> Pipeline:
    """Create a fresh candidate model pipeline by name."""

    factories = candidate_model_factories()
    if model_name not in factories:
        raise ValueError(f"Unknown model name: {model_name}")
    return factories[model_name]()


def _metrics(y_true: pd.Series | np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    """Return standard regression metrics."""

    rmse = mean_squared_error(y_true, y_pred) ** 0.5
    return {
        "MAE": float(mean_absolute_error(y_true, y_pred)),
        "RMSE": float(rmse),
        "R2": float(r2_score(y_true, y_pred)),
    }


def time_series_validation_metrics(
    development: pd.DataFrame,
    feature_columns: list[str],
    n_splits: int = 5,
    gap_rows: int = PURGE_GAP_ROWS,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compare candidate models inside development with a time-series gap."""

    if len(development) < n_splits + gap_rows + 2:
        raise ValueError("Development set is too small for time-series validation")

    splitter = TimeSeriesSplit(n_splits=n_splits, gap=gap_rows)
    fold_rows: list[dict] = []
    X_dev = development[feature_columns]
    y_dev = development[TARGET_COLUMN]

    for fold, (train_index, validation_index) in enumerate(splitter.split(X_dev), start=1):
        fold_train = development.iloc[train_index]
        fold_validation = development.iloc[validation_index]
        X_train = fold_train[feature_columns]
        y_train = fold_train[TARGET_COLUMN]
        X_validation = fold_validation[feature_columns]
        y_validation = fold_validation[TARGET_COLUMN]

        for model_name, factory in candidate_model_factories().items():
            model = factory()
            model.fit(X_train, y_train)
            validation_pred = model.predict(X_validation)
            row = {
                "model": model_name,
                "fold": fold,
                "train_start": str(fold_train["date"].min().date()),
                "train_end": str(fold_train["date"].max().date()),
                "validation_start": str(fold_validation["date"].min().date()),
                "validation_end": str(fold_validation["date"].max().date()),
                "train_rows": int(len(fold_train)),
                "gap_rows": int(gap_rows),
                "validation_rows": int(len(fold_validation)),
                **_metrics(y_validation, validation_pred),
            }
            fold_rows.append(row)

    fold_metrics = pd.DataFrame(fold_rows)
    summary = (
        fold_metrics.groupby("model", as_index=False)
        .agg(
            validation_MAE=("MAE", "mean"),
            validation_RMSE=("RMSE", "mean"),
            validation_R2=("R2", "mean"),
            validation_MAE_std=("MAE", "std"),
            validation_RMSE_std=("RMSE", "std"),
            folds=("fold", "nunique"),
        )
        .sort_values(["validation_MAE", "validation_RMSE"])
        .reset_index(drop=True)
    )
    summary["selection_rank"] = np.arange(1, len(summary) + 1)
    return summary, fold_metrics


def _linear_coefficient_table(fitted_models: dict[str, Pipeline], feature_columns: list[str]) -> pd.DataFrame:
    """Extract standardized coefficients from fitted linear pipelines."""

    rows: list[dict] = []
    for model_name in ["linear_regression", "ridge"]:
        pipeline = fitted_models.get(model_name)
        if pipeline is None or "model" not in pipeline.named_steps:
            continue
        model = pipeline.named_steps["model"]
        if not hasattr(model, "coef_"):
            continue
        coefs = np.ravel(model.coef_)
        temp = pd.DataFrame(
            {
                "model": model_name,
                "feature": feature_columns,
                "coefficient": coefs,
                "abs_coefficient": np.abs(coefs),
                "sign": np.where(coefs >= 0, "positive", "negative"),
            }
        )
        temp["rank_abs_magnitude"] = temp["abs_coefficient"].rank(method="first", ascending=False).astype(int)
        rows.extend(temp.to_dict(orient="records"))
    return pd.DataFrame(rows).sort_values(["model", "rank_abs_magnitude"]).reset_index(drop=True)


def train_and_evaluate_models(
    model_ready: pd.DataFrame,
    feature_columns: list[str] | None = None,
    model_dir: Path = MODEL_DIR,
) -> dict:
    """Select a model by time-aware validation, then evaluate final test once."""

    feature_columns = feature_columns or BASE_FEATURES.copy()
    development, test, purged_gap = chronological_train_test_split(model_ready)
    validation_metrics, validation_fold_metrics = time_series_validation_metrics(development, feature_columns)
    best_name = str(validation_metrics.iloc[0]["model"])

    X_development = development[feature_columns]
    y_development = development[TARGET_COLUMN]
    X_test = test[feature_columns]
    y_test = test[TARGET_COLUMN]

    selected_model = build_model_by_name(best_name)
    selected_model.fit(X_development, y_development)
    selected_pred = selected_model.predict(X_test)
    naive_pred = test["realized_volatility_5d"].to_numpy()

    naive_metrics = {"model": NAIVE_MODEL_NAME, "role": "external_benchmark", **_metrics(y_test, naive_pred)}
    selected_metrics = {"model": best_name, "role": "selected_by_development_validation", **_metrics(y_test, selected_pred)}
    test_metrics = pd.DataFrame([naive_metrics, selected_metrics])
    naive_mae = float(test_metrics.loc[test_metrics["model"] == NAIVE_MODEL_NAME, "MAE"].iloc[0])
    naive_rmse = float(test_metrics.loc[test_metrics["model"] == NAIVE_MODEL_NAME, "RMSE"].iloc[0])
    test_metrics["MAE_improvement_vs_naive"] = (naive_mae - test_metrics["MAE"]) / naive_mae
    test_metrics["RMSE_improvement_vs_naive"] = (naive_rmse - test_metrics["RMSE"]) / naive_rmse
    test_metrics.loc[test_metrics["model"] == NAIVE_MODEL_NAME, ["MAE_improvement_vs_naive", "RMSE_improvement_vs_naive"]] = 0.0

    all_development_fitted = {}
    for model_name, factory in candidate_model_factories().items():
        model = factory()
        model.fit(X_development, y_development)
        all_development_fitted[model_name] = model

    coefficient_table = _linear_coefficient_table(all_development_fitted, feature_columns)
    prediction_frame = pd.DataFrame(
        {
            "date": test["date"].to_numpy(),
            "actual": y_test.to_numpy(),
            "naive_last_5d_realized_vol": naive_pred,
            "selected_prediction": selected_pred,
        }
    )
    prediction_frame["selected_residual"] = prediction_frame["actual"] - prediction_frame["selected_prediction"]

    model_dir.mkdir(parents=True, exist_ok=True)
    model_bundle = {
        "model_name": best_name,
        "selection_method": "TimeSeriesSplit validation inside the development period only with a five-row purge gap",
        "target_horizon_rows": TARGET_HORIZON_ROWS,
        "purge_gap_rows": PURGE_GAP_ROWS,
        "pipeline": selected_model,
        "feature_columns": feature_columns,
        "target_column": TARGET_COLUMN,
        "development_start": str(development["date"].min().date()),
        "development_end": str(development["date"].max().date()),
        "purged_gap_start": str(purged_gap["date"].min().date()) if not purged_gap.empty else None,
        "purged_gap_end": str(purged_gap["date"].max().date()) if not purged_gap.empty else None,
        "purged_gap_rows": int(len(purged_gap)),
        "final_test_start": str(test["date"].min().date()),
        "final_test_end": str(test["date"].max().date()),
        "development_rows": int(len(development)),
        "final_test_rows": int(len(test)),
        "validation_metrics": validation_metrics.to_dict(orient="records"),
        "final_test_metrics": test_metrics.to_dict(orient="records"),
    }
    model_path = model_dir / "model.pkl"
    joblib.dump(model_bundle, model_path)
    write_json(
        {k: v for k, v in model_bundle.items() if k != "pipeline"},
        model_dir / "model_metadata.json",
    )

    return {
        "development": development,
        "purged_gap": purged_gap,
        "test": test,
        "feature_columns": feature_columns,
        "validation_metrics": validation_metrics,
        "validation_fold_metrics": validation_fold_metrics,
        "test_metrics": test_metrics,
        "metrics": test_metrics,
        "linear_coefficients": coefficient_table,
        "predictions": prediction_frame,
        "best_model_name": best_name,
        "model_path": model_path,
        "model_bundle": model_bundle,
    }


def save_modeling_outputs(results: dict, reports_dir: Path = REPORTS_DIR) -> dict[str, Path]:
    """Save prediction tables, metrics, and diagnostic figures."""

    tables_dir = reports_dir / "tables"
    figures_dir = reports_dir / "figures"
    processed_dir = reports_dir.parents[0] / "data" / "processed"
    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    outputs = {
        "model_metrics": tables_dir / "model_metrics.csv",
        "model_validation_metrics": tables_dir / "model_validation_metrics.csv",
        "model_validation_fold_metrics": tables_dir / "model_validation_fold_metrics.csv",
        "model_test_metrics": tables_dir / "model_test_metrics.csv",
        "linear_coefficients": tables_dir / "linear_coefficients.csv",
        "volatility_forecasts": processed_dir / "volatility_forecasts.csv",
    }
    results["test_metrics"].to_csv(outputs["model_metrics"], index=False)
    results["validation_metrics"].to_csv(outputs["model_validation_metrics"], index=False)
    results["validation_fold_metrics"].to_csv(outputs["model_validation_fold_metrics"], index=False)
    results["test_metrics"].to_csv(outputs["model_test_metrics"], index=False)
    results["linear_coefficients"].to_csv(outputs["linear_coefficients"], index=False)
    results["predictions"].to_csv(outputs["volatility_forecasts"], index=False)

    sns.set_theme(style="whitegrid")
    pred = results["predictions"].copy()
    pred["date"] = pd.to_datetime(pred["date"])
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(pred["date"], pred["actual"], label="Actual future 5d volatility")
    ax.plot(pred["date"], pred["selected_prediction"], label=f"Selected model: {results['best_model_name']}", alpha=0.85)
    ax.plot(pred["date"], pred["naive_last_5d_realized_vol"], label="Naive baseline", alpha=0.65)
    ax.set_title("Final test: actual vs predicted future 5-day S&P 500 volatility")
    ax.set_ylabel("Daily volatility")
    ax.legend()
    outputs["actual_vs_predicted"] = figures_dir / "actual_vs_predicted_volatility.png"
    fig.tight_layout()
    fig.savefig(outputs["actual_vs_predicted"], dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4))
    validation_plot = results["validation_metrics"].melt(
        id_vars="model",
        value_vars=["validation_MAE", "validation_RMSE"],
        var_name="metric",
        value_name="value",
    )
    sns.barplot(data=validation_plot, x="model", y="value", hue="metric", ax=ax)
    ax.set_title("Development validation error used for model selection (5-row gap)")
    ax.set_xlabel("")
    ax.tick_params(axis="x", rotation=25)
    outputs["model_validation_comparison"] = figures_dir / "model_validation_comparison.png"
    fig.tight_layout()
    fig.savefig(outputs["model_validation_comparison"], dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4))
    plot_metrics = results["test_metrics"].melt(id_vars=["model", "role"], value_vars=["MAE", "RMSE"], var_name="metric", value_name="value")
    sns.barplot(data=plot_metrics, x="model", y="value", hue="metric", ax=ax)
    ax.set_title("Final untouched test error vs naive benchmark")
    ax.set_xlabel("")
    ax.tick_params(axis="x", rotation=20)
    outputs["model_error_comparison"] = figures_dir / "model_error_comparison.png"
    fig.tight_layout()
    fig.savefig(outputs["model_error_comparison"], dpi=160)
    plt.close(fig)

    coef = results["linear_coefficients"].copy()
    if not coef.empty:
        top_features = (
            coef.groupby("feature")["abs_coefficient"]
            .max()
            .sort_values(ascending=False)
            .head(12)
            .index
        )
        plot_coef = coef[coef["feature"].isin(top_features)].copy()
        feature_order = (
            plot_coef.groupby("feature")["abs_coefficient"]
            .max()
            .sort_values(ascending=True)
            .index
        )
        fig, ax = plt.subplots(figsize=(9, 6))
        sns.barplot(data=plot_coef, y="feature", x="coefficient", hue="model", order=feature_order, ax=ax)
        ax.axvline(0, color="black", linewidth=1)
        ax.set_title("Standardized linear-model coefficients")
        ax.set_xlabel("Coefficient after median imputation and standard scaling")
        ax.set_ylabel("")
        outputs["linear_coefficients_plot"] = figures_dir / "linear_coefficients.png"
        fig.tight_layout()
        fig.savefig(outputs["linear_coefficients_plot"], dpi=160)
        plt.close(fig)

    residuals = pred["selected_residual"]
    fitted = pred["selected_prediction"]
    fig, axes = plt.subplots(2, 2, figsize=(10, 8))
    axes[0, 0].scatter(fitted, residuals, alpha=0.5, s=18)
    axes[0, 0].axhline(0, color="black", linewidth=1)
    axes[0, 0].set_title("Residuals vs fitted")
    axes[0, 0].set_xlabel("Fitted volatility")
    axes[0, 0].set_ylabel("Residual")
    axes[0, 1].hist(residuals, bins=30)
    axes[0, 1].set_title("Residual histogram")
    stats.probplot(residuals, dist="norm", plot=axes[1, 0])
    axes[1, 0].set_title("QQ plot")
    axes[1, 1].plot(pred["date"], residuals)
    axes[1, 1].axhline(0, color="black", linewidth=1)
    axes[1, 1].set_title("Residuals over time")
    axes[1, 1].tick_params(axis="x", rotation=25)
    outputs["residual_diagnostics"] = figures_dir / "residual_diagnostics.png"
    fig.tight_layout()
    fig.savefig(outputs["residual_diagnostics"], dpi=160)
    plt.close(fig)

    return outputs
