"""
DBSCAN doesn't have a built-in .predict() for unseen points -- it only
assigns labels to the points it was originally fit on. The standard way to
classify a NEW point against an already-fit DBSCAN result is to reuse
DBSCAN's own core rule: check how many of the *original* fitted points fall
within `eps` distance of the new point.
  - If it has at least `min_samples` fitted points within eps -> normal.
  - Otherwise -> noise (anomaly).

This is an approximation of true incremental DBSCAN, but it's the standard,
defensible approach for serving DBSCAN results on new data.
"""

import pandas as pd
from sklearn.neighbors import NearestNeighbors

from . import config
from . import persistence
from .exceptions import InvalidRecordError, PreprocessingError, ModelNotFoundError
from .logging_utils import get_logger

logger = get_logger(__name__)


def preprocess_single_record(record: dict, feature_names: list, scaler, pca):
    """
    Take a single raw record (dict of raw NSL-KDD feature values), one-hot
    encode it to match the training feature columns, scale, and project
    through the saved PCA -- using the exact fitted transformers from
    training time, never refit here.
    """
    if not isinstance(record, dict) or not record:
        raise InvalidRecordError("record must be a non-empty dict of feature values.")

    try:
        df = pd.DataFrame([record])
        df_encoded = pd.get_dummies(df, columns=config.CATEGORICAL_COLS)
        df_aligned = df_encoded.reindex(columns=feature_names, fill_value=0)
        X_scaled = scaler.transform(df_aligned)
        X_pca = pca.transform(X_scaled)
    except Exception as e:
        logger.exception("Preprocessing failed for incoming record.")
        raise PreprocessingError(f"Failed to preprocess record: {e}") from e
    return X_pca

def score_point(X_pca_point, train_coords, eps, min_samples):
    """Apply DBSCAN's core-point rule to a single new point against the saved
    training coordinates: count neighbors within eps, compare to min_samples."""

    neighbors = NearestNeighbors(radius=eps)
    neighbors.fit(train_coords)
    neighbor_counts = neighbors.radius_neighbors(X_pca_point, return_distance=False)
    n_neighbors = len(neighbor_counts[0])

    is_anomaly = n_neighbors < min_samples
    result = {
        "is_anomaly": bool(is_anomaly),
        "verdict": "anomaly" if is_anomaly else "normal",
        "neighbors_within_eps": int(n_neighbors),
        "min_samples_required": min_samples,
    }
    logger.info(f"Scored point: verdict={result['verdict']}, "
                f"neighbors={n_neighbors}/{min_samples}")
    return result

def predict(record: dict):
    """
    Full inference path: load saved artifacts, preprocess, score.
    """
    try:
        artifacts = persistence.load_artifacts()
    except FileNotFoundError as e:
        logger.error("Model artifacts not found.")
        raise ModelNotFoundError(str(e)) from e

    if artifacts["train_coords"] is None:
        raise ModelNotFoundError(
            "No saved training coordinates found -- re-run "
            "`python main.py --save-model` to regenerate them."
        )
    X_pca_point = preprocess_single_record(
        record, artifacts["feature_names"], artifacts["scaler"], artifacts["pca"]
    )
    return score_point(
        X_pca_point,
        artifacts["train_coords"],
        eps=artifacts["dbscan_params"]["eps"],
        min_samples=artifacts["dbscan_params"]["min_samples"],
    )

