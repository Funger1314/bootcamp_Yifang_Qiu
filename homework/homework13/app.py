from pathlib import Path
import logging
import math
import os

import joblib
from flask import Flask, jsonify, request

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model" / "model.pkl"

# Loaded ONCE when the application starts.
model = joblib.load(MODEL_PATH)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("prediction_api")

app = Flask(__name__)


def validate_features(features):
    if features is None:
        return None, "Missing 'features' key."

    if not isinstance(features, (list, tuple)) or len(features) != 2:
        return None, "'features' must contain exactly 2 values."

    try:
        numeric = [float(value) for value in features]
    except (TypeError, ValueError):
        return None, "Both feature values must be numeric."

    if not all(math.isfinite(value) for value in numeric):
        return None, "Both feature values must be finite numbers."

    return numeric, None


@app.route("/predict", methods=["POST"])
def predict_post():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        logger.warning("Rejected POST /predict: invalid or missing JSON body")
        return jsonify({"error": "Request body must be a JSON object."}), 400

    features, error = validate_features(data.get("features"))
    if error:
        logger.warning("Rejected POST /predict: %s", error)
        return jsonify({"error": error}), 400

    prediction = float(model.predict([features])[0])
    logger.info("POST /predict features=%s prediction=%s", features, prediction)
    return jsonify({"prediction": prediction}), 200


@app.route("/predict/<f1>/<f2>", methods=["GET"])
def predict_get(f1, f2):
    try:
        features = [float(f1), float(f2)]
    except (TypeError, ValueError):
        error = "Path parameters f1 and f2 must be numeric."
        logger.warning("Rejected GET prediction: %s", error)
        return jsonify({"error": error}), 400

    if not all(math.isfinite(value) for value in features):
        error = "Path parameters f1 and f2 must be finite numbers."
        logger.warning("Rejected GET prediction: %s", error)
        return jsonify({"error": error}), 400

    prediction = float(model.predict([features])[0])
    logger.info("GET prediction features=%s prediction=%s", features, prediction)
    return jsonify({"prediction": prediction}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="127.0.0.1", port=port, debug=False)
