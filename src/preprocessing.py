import pandas as pd
from sklearn.preprocessing import StandardScaler
from . import config
from .exceptions import PreprocessingError
from .logging_utils import get_logger

logger = get_logger(__name__)

"""
Preprocessing: one-hot encode categorical features (train/test jointly, so
columns align even if a category appears in only one split), then scale
numeric features with StandardScaler (fit on train only -- test is never
used to compute scaling parameters, to avoid leaking its distribution).
"""
def encode_categoricals(train_df, test_df):
    """One-hot encode categoricals for train/test together so both end up
    with identical columns, then split back apart."""
    label_cols= ["label", "attack_category", "is_attack"]
    try:
        X_train = train_df.drop(columns = label_cols)
        X_test = test_df.drop(columns = label_cols)
    except KeyError as e:
        logger.exception("Expected label columns missing from input data.")
        raise PreprocessingError(
            f"Input data is missing expected columns {label_cols}: {e}"
        ) from e
    missing_cat_cols = [c for c in config.CATEGORICAL_COLS if c not in X_train.columns]
    if missing_cat_cols:
        logger.error(f"Missing categorical columns: {missing_cat_cols}")
        raise PreprocessingError(
            f"Expected categorical columns not found in data: {missing_cat_cols}"
        )
    combined = pd.concat([X_train, X_test], keys=["train", "test"])
    combined_encoded = pd.get_dummies(combined, columns=config.CATEGORICAL_COLS)

    X_train_encoded = combined_encoded.loc["train"]
    X_test_encoded = combined_encoded.loc["test"]

    logger.info(f"One-hot encoded: {X_train.shape[1]} -> {X_train_encoded.shape[1]} columns")
    return X_train_encoded, X_test_encoded


def scale_features(X_train_encoded, X_test_encoded):
    """Fit StandardScaler on train only, apply to both."""
    try:
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train_encoded)
        X_test_scaled = scaler.transform(X_test_encoded)
    except ValueError as e:
        logger.exception("Scaling failed -- likely non-numeric data reached the scaler.")
        raise PreprocessingError(f"Failed to scale features: {e}") from e

    logger.info("Scaled numeric features (fit on train, applied to train+test).")
    return X_train_scaled, X_test_scaled, scaler

def preprocess(train_df, test_df):
    """Full preprocessing pipeline: encode -> scale."""
    if train_df.empty or test_df.empty:
        raise PreprocessingError("Train or test DataFrame is empty -- nothing to preprocess.")
    X_train_encoded, X_test_encoded = encode_categoricals(train_df,test_df)
    X_train_scaled, X_test_scaled, scaler = scale_features(
        X_train_encoded, X_test_encoded
    )

    y_train = train_df["is_attack"]
    y_test = test_df["is_attack"]
    return {
        "X_train_scaled": X_train_scaled,
        "X_test_scaled": X_test_scaled,
        "y_train": y_train,
        "y_test": y_test,
        "scaler": scaler,
        "feature_names": X_train_encoded.columns.tolist(),
    }






    










    
















