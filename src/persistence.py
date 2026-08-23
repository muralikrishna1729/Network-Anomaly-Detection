"""
Persist and reload fitted pipeline artifacts (scaler, PCA, DBSCAN parameters).
"""

import os
import joblib

from . import config
from .exceptions import ModelNotFoundError
from .logging_utils import get_logger

logger = get_logger(__name__)

os.makedirs(config.MODELS_DIR, exist_ok=True)

SCALER_PATH = os.path.join(config.MODELS_DIR, "scaler.joblib")
PCA_PATH = os.path.join(config.MODELS_DIR, "pca.joblib")
DBSCAN_PARAMS_PATH = os.path.join(config.MODELS_DIR, "dbscan_params.joblib")
FEATURE_NAMES_PATH = os.path.join(config.MODELS_DIR, "feature_names.joblib")
TRAIN_COORDS_PATH = os.path.join(config.MODELS_DIR, "train_coords.joblib")

def save_artifacts(scaler, pca, dbscan_params, feature_names, train_coords = None):
    try:
        joblib.dump(scaler, SCALER_PATH)
        joblib.dump(pca, PCA_PATH)
        joblib.dump(dbscan_params, DBSCAN_PARAMS_PATH)
        joblib.dump(feature_names, FEATURE_NAMES_PATH)
        if train_coords is not None:
            joblib.dump(train_coords, TRAIN_COORDS_PATH)
    except OSError as e:
        logger.exception("Failed to save model artifacts.")
        raise ModelNotFoundError(f"Could not save model artifacts: {e}") from e


def load_artifacts():
    if not os.path.exists(SCALER_PATH):
        logger.error(f"No saved model found at {SCALER_PATH}")
        raise ModelNotFoundError(
            f"No saved model found at {SCALER_PATH}. "
            f"Run `python main.py --save-model` first."
        )
    try:
        artifacts = {
            "scaler": joblib.load(SCALER_PATH),
            "pca": joblib.load(PCA_PATH),
            "dbscan_params": joblib.load(DBSCAN_PARAMS_PATH),
            "feature_names": joblib.load(FEATURE_NAMES_PATH),
            "train_coords": joblib.load(TRAIN_COORDS_PATH) if os.path.exists(TRAIN_COORDS_PATH) else None,
        }
    except Exception as e:
        logger.exception("Failed to load saved model artifacts.")
        raise ModelNotFoundError(f"Could not load model artifacts: {e}") from e

    logger.info("Model artifacts loaded successfully.")
    return artifacts