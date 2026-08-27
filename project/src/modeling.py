"""Model training and diagnostics for future volatility prediction."""

from __future__ import annotations

from pathlib import Path

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
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.config import MODEL_DIR, REPORTS_DIR
from src.features import BASE_FEATURES, TARGET_COLUMN
from src.utils import write_json


def chronological_train_test_split(dataframe: pd.DataFrame, test_size: float = 0.2) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split time-series rows chronologically without shuffling."""

    if not 0 < test_size < 1:
        raise ValueError("test_size must be between zero and one")
    data = dataframe.sort_values("date").reset_index(drop=True)
    split_index = int(len(data) * (1 - test_size))
    if split_index <= 0 or split_index >= len(data):
        raise ValueError("Invalid split produced an empty train or test set")
    return data.iloc[:split_index].copy(), data.iloc[split_index:].copy()


def regression_pipeline(model) -> Pipeline:
    """Build a sklearn pipeline with imputation, scaling, and a regressor."""

    return Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("model", model),
        ]
    )


def _metrics(y_true: pd.Series, y_pred: np.ndarray) -> dict[str, float]:
    rmse = mean_squared_error(y_true, y_pred) ** 0.5
    return {
        "MAE": float(mean_absolute_error(y_true, y_pred)),
        "RMSE": float(rmse),
        "R2": float(r2_score(y_true, y_pred)),
    }


def train_and_evaluate_models(
    model_ready: pd.DataFrame,
    feature_columns: list[str] | None = None,
    model_dir: Path = MODEL_DIR,
) -> dict:
    """Train benchmark, linear baseline, and alternative project models."""

    feature_columns = feature_columns or BASE_FEATURES.copy()
    train, test = chronological_train_test_split(model_ready)
    X_train = train[feature_columns]
    y_train = train[TARGET_COLUMN]
    X_test = test[feature_columns]
    y_test = test[TARGET_COLUMN]

    naive_pred = test["realized_volatility_5d"].to_numpy()
    candidates = {
        "linear_regression": regression_pipeline(LinearRegression()),
        "ridge": regression_pipeline(Ridge(alpha=1.0)),
        "random_forest": Pipeline(
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

    metrics_rows = [{"model": "naive_last_5d_realized_vol", **_metrics(y_test, naive_pred)}]
    fitted = {}
    predictions = {
        "date": test["date"].to_numpy(),
        "actual": y_test.to_numpy(),
        "naive_last_5d_realized_vol": naive_pred,
    }

    for name, pipeline in candidates.items():
        pipeline.fit(X_train, y_train)
        pred = pipeline.predict(X_test)
        fitted[name] = pipeline
        predictions[name] = pred
        metrics_rows.append({"model": name, **_metrics(y_test, pred)})

    metrics = pd.DataFrame(metrics_rows)
    naive_mae = metrics.loc[metrics["model"] == "naive_last_5d_realized_vol", "MAE"].iloc[0]
    naive_rmse = metrics.loc[metrics["model"] == "naive_last_5d_realized_vol", "RMSE"].iloc[0]
    metrics["MAE_improvement_vs_naive"] = (naive_mae - metrics["MAE"]) / naive_mae
    metrics["RMSE_improvement_vs_naive"] = (naive_rmse - metrics["RMSE"]) / naive_rmse

    model_order = metrics.loc[metrics["model"] != "naive_last_5d_realized_vol"].sort_values(["MAE", "RMSE"])
    best_name = str(model_order.iloc[0]["model"])
    best_model = fitted[best_name]
    prediction_frame = pd.DataFrame(predictions)
    prediction_frame["selected_prediction"] = prediction_frame[best_name]
    prediction_frame["selected_residual"] = prediction_frame["actual"] - prediction_frame["selected_prediction"]

    model_dir.mkdir(parents=True, exist_ok=True)
    model_bundle = {
        "model_name": best_name,
        "pipeline": best_model,
        "feature_columns": feature_columns,
        "target_column": TARGET_COLUMN,
        "train_start": str(train["date"].min().date()),
        "train_end": str(train["date"].max().date()),
        "test_start": str(test["date"].min().date()),
        "test_end": str(test["date"].max().date()),
        "metrics": metrics.to_dict(orient="records"),
    }
    model_path = model_dir / "model.pkl"
    joblib.dump(model_bundle, model_path)
    write_json(
        {k: v for k, v in model_bundle.items() if k != "pipeline"},
        model_dir / "model_metadata.json",
    )

    return {
        "train": train,
        "test": test,
        "feature_columns": feature_columns,
        "metrics": metrics,
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
        "volatility_forecasts": processed_dir / "volatility_forecasts.csv",
    }
    results["metrics"].to_csv(outputs["model_metrics"], index=False)
    results["predictions"].to_csv(outputs["volatility_forecasts"], index=False)

    sns.set_theme(style="whitegrid")
    pred = results["predictions"].copy()
    pred["date"] = pd.to_datetime(pred["date"])
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(pred["date"], pred["actual"], label="Actual future 5d volatility")
    ax.plot(pred["date"], pred["selected_prediction"], label=f"Selected model: {results['best_model_name']}", alpha=0.85)
    ax.plot(pred["date"], pred["naive_last_5d_realized_vol"], label="Naive baseline", alpha=0.65)
    ax.set_title("Actual vs predicted future 5-day S&P 500 volatility")
    ax.set_ylabel("Daily volatility")
    ax.legend()
    outputs["actual_vs_predicted"] = figures_dir / "actual_vs_predicted_volatility.png"
    fig.tight_layout()
    fig.savefig(outputs["actual_vs_predicted"], dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4))
    plot_metrics = results["metrics"].melt(id_vars="model", value_vars=["MAE", "RMSE"], var_name="metric", value_name="value")
    sns.barplot(data=plot_metrics, x="model", y="value", hue="metric", ax=ax)
    ax.set_title("Model error vs naive benchmark")
    ax.set_xlabel("")
    ax.tick_params(axis="x", rotation=25)
    outputs["model_error_comparison"] = figures_dir / "model_error_comparison.png"
    fig.tight_layout()
    fig.savefig(outputs["model_error_comparison"], dpi=160)
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
