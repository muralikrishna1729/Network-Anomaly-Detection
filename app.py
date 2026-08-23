from flask import Flask ,request, jsonify
from src import config
from src import persistence
from src.inference import preprocess_single_record, score_point
from src.exceptions import InvalidRecordError, PreprocessingError, ModelNotFoundError
from src.logging_utils import get_logger

logger = get_logger(__name__)
app = Flask(__name__)

# Load the saved model artifacts ONCE at startup, not per-request.
try:
    ARTIFACTS = persistence.load_artifacts()
    MODEL_LOADED = True
    MODEL_LOAD_ERROR = None
    logger.info("Model artifacts loaded successfully at startup.")
except FileNotFoundError as e:
    ARTIFACTS = None
    MODEL_LOADED = False
    MODEL_LOAD_ERROR = str(e)
    logger.error(f"Model artifacts not found at startup: {e}")

REQUIRED_FIELDS = [c for c in config.COLUMN_NAMES if c != "label"]

@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "service": "network-anomaly-detection",
        "status": "ok" if MODEL_LOADED else "model_not_loaded",
        "endpoints": {
            "health": "GET /health",
            "predict": "POST /predict",
        },
    }), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok" if MODEL_LOADED else "model_not_loaded",
        "model_loaded": MODEL_LOADED,
        "error": MODEL_LOAD_ERROR,
    }), 200 if MODEL_LOADED else 503

@app.route("/predict", methods=["POST"])
def predict_endpoint():
    if not MODEL_LOADED:
        logger.warning("Predict called but model is not loaded.")
        return jsonify({
            "error": "model_not_loaded",
            "message": "Model not loaded. Run `python main.py --save-model` first."
        }), 503

    record = request.get_json(silent=True)
    if record is None:
        logger.warning("Predict called with invalid/non-JSON body.")
        return jsonify({
            "error": "invalid_json",
            "message": "Request body must be valid JSON."
        }), 400

    missing = [f for f in REQUIRED_FIELDS if f not in record]
    if missing:
        logger.warning(f"Predict called with missing fields: {missing}")
        return jsonify({
            "error": "missing_fields",
            "message": "Request is missing required fields.",
            "missing_fields": missing,
        }), 400

    try:
        X_pca_point = preprocess_single_record(
            record, ARTIFACTS["feature_names"], ARTIFACTS["scaler"], ARTIFACTS["pca"]
        )
        result = score_point(
            X_pca_point,
            ARTIFACTS["train_coords"],
            eps=ARTIFACTS["dbscan_params"]["eps"],
            min_samples=ARTIFACTS["dbscan_params"]["min_samples"],
        )

    except InvalidRecordError as e:
        logger.warning(f"Invalid record: {e}")
        return jsonify({"error": "invalid_record", "message": str(e)}), 400
    except PreprocessingError as e:
        logger.error(f"Preprocessing error: {e}")
        return jsonify({"error": "preprocessing_error", "message": str(e)}), 422
    except ModelNotFoundError as e:
        logger.error(f"Model error during predict: {e}")
        return jsonify({"error": "model_error", "message": str(e)}), 503
    except Exception as e:
        logger.exception("Unexpected error during prediction.")
        return jsonify({
            "error": "internal_error",
            "message": "An unexpected error occurred."
        }), 500

    return jsonify(result), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)