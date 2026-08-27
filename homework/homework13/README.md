# Stage 13 Homework — Prediction API

This API serves predictions from a two-feature linear regression model trained on a reproducible synthetic dataset created with `make_regression`. The trained model is persisted in `model/model.pkl` with `joblib` and loaded once when the Flask application starts.

## Files

```text
homework13/
├── homework13_productization_submission.ipynb
├── app.py
├── README.md
└── model/
    └── model.pkl
```

## Install dependencies

```bash
pip install flask requests scikit-learn joblib
```

## Start the API

From `homework/homework13/` run exactly:

```bash
python app.py
```

The server starts at:

```text
http://127.0.0.1:5000
```

The model is loaded once at application startup and reused for every request.

## POST /predict

Send a JSON object containing exactly two feature values.

### curl

```bash
curl -X POST http://127.0.0.1:5000/predict   -H "Content-Type: application/json"   -d '{"features": [0.1, 0.2]}'
```

Example response:

```json
{"prediction": 23.589611712973284}
```

### Python requests

```python
import requests

response = requests.post(
    "http://127.0.0.1:5000/predict",
    json={"features": [0.1, 0.2]},
)
print(response.status_code)
print(response.json())
```

## GET /predict/<f1>/<f2>

### curl

```bash
curl http://127.0.0.1:5000/predict/0.1/0.2
```

Example response:

```json
{"prediction": 23.589611712973284}
```

### Python requests

```python
import requests

response = requests.get(
    "http://127.0.0.1:5000/predict/0.1/0.2"
)
print(response.status_code)
print(response.json())
```

## Bad input

Invalid input returns **HTTP 400** and a JSON object with an `error` field instead of a server traceback.

Examples:

Missing `features`:

```bash
curl -X POST http://127.0.0.1:5000/predict   -H "Content-Type: application/json"   -d '{"wrong_key": [0.1, 0.2]}'
```

Response:

```json
{"error": "Missing 'features' key."}
```

Wrong number of POST features:

```json
{"features": [0.1]}
```

Response:

```json
{"error": "'features' must contain exactly 2 values."}
```

Non-numeric GET parameter:

```bash
curl http://127.0.0.1:5000/predict/abc/0.2
```

Response:

```json
{"error": "Path parameters f1 and f2 must be numeric."}
```

## Notes

- `model/model.pkl` is created with `joblib`, not `pickle`.
- `app.py` resolves the model path relative to itself, so model loading does not depend on the shell's current working directory.
- Successful and rejected requests are logged by the Flask application.
