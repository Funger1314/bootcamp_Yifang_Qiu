"""Command-line orchestration for the volatility project pipeline."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT_FOR_IMPORTS = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT_FOR_IMPORTS) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT_FOR_IMPORTS))

from src.acquisition import acquire_raw_data
from src.cleaning import clean_and_align_sources, save_cleaned_dataset
from src.config import DEFAULT_END_DATE, DEFAULT_START_DATE, PROCESSED_DATA_DIR, PROJECT_ROOT, REPORTS_DIR
from src.eda import save_eda_figures, save_eda_tables
from src.evaluation import save_evaluation_outputs
from src.features import build_features, save_feature_outputs
from src.modeling import save_modeling_outputs, train_and_evaluate_models
from src.outliers import outlier_sensitivity_summary
from src.reporting import write_stakeholder_report


LOG_PATH = PROJECT_ROOT / "reports" / "pipeline.log"


def setup_logging() -> None:
    """Configure console and file logging."""

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(LOG_PATH, mode="w", encoding="utf-8")],
        force=True,
    )


def step_ingest(start_date: str = DEFAULT_START_DATE, end_date: str | None = None) -> dict[str, Path]:
    """Download and save raw market data."""

    logging.info("Starting ingest step")
    outputs = acquire_raw_data(start_date=start_date, end_date=end_date or DEFAULT_END_DATE or None)
    logging.info("Finished ingest step; saved sources=%s", sorted(outputs))
    return outputs


def step_clean() -> pd.DataFrame:
    """Clean and align raw sources, then save the cleaned dataset."""

    logging.info("Starting clean step")
    cleaned = clean_and_align_sources()
    save_cleaned_dataset(cleaned)
    logging.info("Finished clean step with %s rows", len(cleaned))
    return cleaned


def step_features() -> tuple[pd.DataFrame, list[str], pd.DataFrame]:
    """Build leakage-safe modeling features and save model-ready data."""

    logging.info("Starting features step")
    cleaned_path = PROCESSED_DATA_DIR / "market_data_cleaned.csv"
    if not cleaned_path.exists():
        step_clean()
    cleaned = pd.read_csv(cleaned_path, parse_dates=["date"])
    model_ready, feature_columns, registry = build_features(cleaned)
    save_feature_outputs(model_ready, registry)
    sensitivity = outlier_sensitivity_summary(model_ready, "future_5d_realized_volatility")
    sensitivity.to_csv(PROCESSED_DATA_DIR / "outlier_sensitivity_summary.csv", index=False)
    logging.info("Finished features step with %s model-ready rows", len(model_ready))
    return model_ready, feature_columns, registry


def step_eda() -> dict[str, Path]:
    """Generate project EDA tables and charts."""

    logging.info("Starting eda step")
    model_ready_path = PROCESSED_DATA_DIR / "model_ready_volatility.csv"
    if not model_ready_path.exists():
        step_features()
    model_ready = pd.read_csv(model_ready_path, parse_dates=["date"])
    outputs = {}
    outputs.update(save_eda_tables(model_ready))
    outputs.update(save_eda_figures(model_ready))
    logging.info("Finished eda step")
    return outputs


def step_model() -> dict:
    """Train project models and save model/prediction artifacts."""

    logging.info("Starting model step")
    model_ready_path = PROCESSED_DATA_DIR / "model_ready_volatility.csv"
    if not model_ready_path.exists():
        step_features()
    model_ready = pd.read_csv(model_ready_path, parse_dates=["date"])
    results = train_and_evaluate_models(model_ready)
    save_modeling_outputs(results)
    logging.info("Finished model step with selected model=%s", results["best_model_name"])
    return results


def step_evaluate() -> dict[str, Path]:
    """Run risk evaluation, uncertainty analysis, and stakeholder reporting."""

    logging.info("Starting evaluate step")
    model_ready = pd.read_csv(PROCESSED_DATA_DIR / "model_ready_volatility.csv", parse_dates=["date"])
    results = train_and_evaluate_models(model_ready)
    save_modeling_outputs(results)
    outputs = save_evaluation_outputs(results, model_ready)
    validation = pd.read_csv(REPORTS_DIR / "tables" / "model_validation_metrics.csv")
    test = pd.read_csv(REPORTS_DIR / "tables" / "model_test_metrics.csv")
    assumption = pd.read_csv(REPORTS_DIR / "tables" / "assumption_sensitivity.csv")
    regime = pd.read_csv(REPORTS_DIR / "tables" / "regime_subgroup_metrics.csv")
    ci = pd.read_csv(REPORTS_DIR / "tables" / "bootstrap_mae_ci.csv")
    report_path = write_stakeholder_report(validation, test, assumption, regime, ci)
    outputs["stakeholder_report"] = report_path
    logging.info("Finished evaluate step")
    return outputs


def run_all(start_date: str = DEFAULT_START_DATE, end_date: str | None = None) -> dict:
    """Run the full idempotent project pipeline."""

    setup_logging()
    artifacts = {
        "ingest": _relative_artifact(step_ingest(start_date=start_date, end_date=end_date)),
        "clean_rows": len(step_clean()),
    }
    model_ready, feature_columns, registry = step_features()
    artifacts["feature_rows"] = len(model_ready)
    artifacts["feature_count"] = len(feature_columns)
    artifacts["eda"] = _relative_artifact(step_eda())
    results = step_model()
    artifacts["selected_model"] = results["best_model_name"]
    artifacts["metrics"] = results["metrics"].to_dict(orient="records")
    artifacts["evaluation"] = _relative_artifact(step_evaluate())
    logging.info("Pipeline complete")
    return artifacts


def _relative_artifact(value):
    """Convert Path artifacts to project-relative strings for clean notebook output."""

    if isinstance(value, Path):
        try:
            return str(value.resolve().relative_to(PROJECT_ROOT))
        except ValueError:
            return str(value)
    if isinstance(value, dict):
        return {key: _relative_artifact(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_relative_artifact(item) for item in value]
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one step of the S&P 500 volatility project pipeline.")
    parser.add_argument(
        "step",
        choices=["ingest", "clean", "features", "eda", "model", "evaluate", "all"],
        help="Pipeline step to run.",
    )
    parser.add_argument("--start-date", default=DEFAULT_START_DATE, help="Start date for data ingestion.")
    parser.add_argument("--end-date", default=DEFAULT_END_DATE or None, help="End date for data ingestion.")
    args = parser.parse_args()

    setup_logging()
    if args.step == "ingest":
        step_ingest(start_date=args.start_date, end_date=args.end_date)
    elif args.step == "clean":
        step_clean()
    elif args.step == "features":
        step_features()
    elif args.step == "eda":
        step_eda()
    elif args.step == "model":
        step_model()
    elif args.step == "evaluate":
        step_evaluate()
    elif args.step == "all":
        run_all(start_date=args.start_date, end_date=args.end_date)
    else:
        raise ValueError(args.step)


if __name__ == "__main__":
    main()
