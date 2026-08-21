"""
Downloads the NSL-KDD dataset (train + test) from a public GitHub mirror.

NSL-KDD is a well-known benchmark for network intrusion detection research.
Source repo: https://github.com/Mamcose/NSL-KDD-Network-Intrusion-Detection

Usage:
    python data/download_data.py
"""

import os
from pathlib import Path
import urllib.request

DATA_DIR = Path(__file__).resolve().parent

FILES = {
    "KDDTrain.csv": (
        "https://raw.githubusercontent.com/Mamcose/"
        "NSL-KDD-Network-Intrusion-Detection/master/NSL_KDD_Train.csv"
    ),
    "KDDTest.csv": (
        "https://raw.githubusercontent.com/Mamcose/"
        "NSL-KDD-Network-Intrusion-Detection/master/NSL_KDD_Test.csv"
    ),
}


def download():
    os.makedirs(DATA_DIR, exist_ok=True)
    for filename, url in FILES.items():
        dest = os.path.join(DATA_DIR, filename)
        if os.path.exists(dest):
            print(f"[skip] {filename} already exists")
            continue
        print(f"[download] {filename} <- {url}")
        urllib.request.urlretrieve(url, dest)
        print(f"[done] saved to {dest}")


if __name__ == "__main__":
    download()