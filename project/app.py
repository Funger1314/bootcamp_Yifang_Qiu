"""Flask API for the S&P 500 volatility project model."""

from __future__ import annotations

from pathlib import Path
import os

import joblib
import numpy as np
import pandas as pd
from flask import Flask, jsonify, request


BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model" / "model.pkl"

# Load once at application startup, not per request.
MODEL_BUNDLE = joblib.load(MODEL_PATH)
PIPELINE = MODEL_BUNDLE["pipeline"]
FEATURE_COLUMNS = MODEL_BUNDLE["feature_columns"]
TARGET_COLUMN = MODEL_BUNDLE["target_column"]
MODEL_NAME = MODEL_BUNDLE["model_name"]

app = Flask(__name__)


def _validate_payload(payload: dict | None) -> tuple[list[float] | None, str | None]:
    if not isinstance(payload, dict):
        return None, "Request body must be a JSON object."
    features = payload.get("features")
    if isinstance(features, dict):
        missing = [column for column in FEATURE_COLUMNS if column not in features]
        if missing:
            return None, f"Missing feature values: {missing}"
        values = [features[column] for column in FEATURE_COLUMNS]
    elif isinstance(features, list):
        if len(features) != len(FEATURE_COLUMNS):
            return None, f"'features' must contain exactly {len(FEATURE_COLUMNS)} values."
        values = features
    else:
        return None, "'features' must be either a list or an object keyed by feature name."

    try:
        numeric = [float(value) for value in values]
    except (TypeError, ValueError):
        return None, "All feature values must be numeric."
    if not all(np.isfinite(numeric)):
        return None, "All feature values must be finite numbers."
    return numeric, None


@app.get("/health")
def health():
    return jsonify({"status": "ok", "model": MODEL_NAME, "target": TARGET_COLUMN})


@app.get("/features")
def features():
    return jsonify({"feature_columns": FEATURE_COLUMNS})


@app.post("/predict")
def predict():
    values, error = _validate_payload(request.get_json(silent=True))
    if error:
        return jsonify({"error": error}), 400
    prediction_frame = pd.DataFrame([dict(zip(FEATURE_COLUMNS, values, strict=True))])
    prediction = float(PIPELINE.predict(prediction_frame)[0])
    return jsonify({"model": MODEL_NAME, "prediction": prediction})


if __name__ == "__main__":
    host = os.environ.get("API_HOST", "127.0.0.1")
    port = int(os.environ.get("API_PORT", "5000"))
    app.run(host=host, port=port, debug=False)
