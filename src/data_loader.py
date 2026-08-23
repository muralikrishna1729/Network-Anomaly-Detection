import os
import joblib
# urllib.request is a built-in Python module (no pip install needed)
# used to open and fetch data from URLs — most commonly for making HTTP requests.

import urllib.request
import urllib.error
import pandas as pd

from . import config
from .exceptions import DataDownloadError, InvalidRecordError
from .logging_utils import get_logger

logger = get_logger(__name__)

def download_if_missing():
    os.makedirs(config.DATA_DIR, exist_ok=True)
    for path,url in [(config.TRAIN_PATH, config.TRAIN_URL),(config.TEST_PATH, config.TEST_URL)]:
        if os.path.exists(path):
            logger.info(f"{os.path.basename(path)} already exists, skipping download.")
            continue
        logger.info(f"Downloading {os.path.basename(path)} from {url}")
        try:
            urllib.request.urlretrieve(url,path)
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
            logger.exception(f"Failed to download {os.path.basename(path)}")
            raise DataDownloadError(
                f"Could not download {os.path.basename(path)} from {url}: {e}"
            ) from e
        logger.info(f"Saved to {path}")

def load_raw():
    """Load train/test CSVs with proper column names."""
    try:
        train = pd.read_csv(config.TRAIN_PATH, names = config.COLUMN_NAMES)
        test = pd.read_csv(config.TEST_PATH, names = config.COLUMN_NAMES)
    except (FileNotFoundError, pd.error.ParseError) as e:
        logger.exception("Failed to load csv files")
        raise DataDownloadError(f"Could not read dataset files: {e}") from e
    return train, test

def add_labels(df):
    """
    Attach derived label columns without touching the raw 'label' column:
    - attack_category: normal / DoS / Probe / R2L / U2R
    - is_attack: 0/1 binary version, used only for post-hoc evaluation
    """
    df = df.copy()
    df["attack_category"] = df["label"].map(config.ATTACK_MAPPING)
    unmapped = df[df["attack_category"].isnull()]["label"].unique()
    if len(unmapped)>0:
        logger.error(f"Unmapped attack labels found: {list(unmapped)}")
        raise InvalidRecordError(
            f"Unmapped attack labels found: {list(unmapped)}. "
            f"Add them to config.ATTACK_MAPPING."
        )
    df["is_attack"] = (df["label"] != "normal").astype(int)
    return df

def load_labeled_data():
    "Full Load: download if needed and load raw and attach labels to it"
    download_if_missing()
    train,test = load_raw()
    train = add_labels(train)
    test = add_labels(test)
    logger.info(f"Loaded labeled data: train={train.shape}, test={test.shape}")
    return train, test


if __name__ == "__main__":
    load_labeled_data()
