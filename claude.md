# Network Anomaly Detection

## Overview
A Python pipeline for detecting anomalies in network traffic data. The pipeline includes data download, loading, preprocessing, dimensionality reduction (PCA), clustering (DBSCAN), evaluation of noise rates and precision/recall, and visualization of results.

## Directory Structure
- `main.py` – entry point to run the full pipeline.
- `download_data.py` – script to fetch raw network data.
- `requirements.txt` – Python package dependencies.
- `.gitignore` – files to exclude from version control.
- `src/` – source modules:
  - `config.py` – central configuration (paths, hyperparameters).
  - `data_loader.py` – download, load, and label data.
  - `preprocessing.py` – encoding, scaling, feature engineering.
  - `dimensionality_reduction.py` – PCA implementation.
  - `clustering.py` – DBSCAN and k‑distance helper functions.
  - `evaluation.py` – per‑category noise rate, precision, recall metrics.
  - `visualization.py` – generate plots and dashboards.
- `outputs/` – generated artifacts:
  - `figures/` – auto‑generated plots.
  - `models/` – saved models.

## Getting Started
1. **Create a virtual environment** (recommended):
   ```bash
   python -m venv .venv
   # Activate:
   # Linux/macOS: source .venv/bin/activate
   # Windows: .venv\Scripts\activate
   ```
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the pipeline**:
   ```bash
   python main.py
   ```

## Usage
- Edit `src/config.py` to point to your data source and adjust any hyperparameters.
- The pipeline will download data (if needed), preprocess, reduce dimensionality, cluster, evaluate, and save figures/models to `outputs/`.

## License
MIT License.