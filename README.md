# Network Intrusion Anomaly Detection with DBSCAN

Unsupervised anomaly detection on network traffic using density-based clustering (DBSCAN), evaluated against a labeled benchmark dataset to measure how well it catches rare and previously unseen attack patterns.

## Problem

Traditional signature-based and classification-based intrusion detection systems can only recognize attack patterns they were explicitly trained on. In practice, new attack variants appear constantly, and labeled examples of them don't exist yet at detection time.

This project asks a different question: **can we flag anomalous network behavior without ever telling the model what an "attack" looks like** — relying only on the idea that unusual behavior is structurally different from normal behavior, not on having seen it before?

## Dataset

[NSL-KDD](https://www.unb.ca/cic/datasets/nsl.html) — a well-known network intrusion benchmark, 125,973 training rows and 22,544 test rows, 41 connection-level features (duration, protocol, byte counts, login behavior, traffic-rate statistics, etc.).

Each row carries a specific attack label rolling up into 4 families plus normal traffic:
- **DoS** (Denial of Service) — high-volume, repetitive floods (e.g. `neptune`, `smurf`)
- **Probe** — reconnaissance/scanning (e.g. `satan`, `portsweep`)
- **R2L** (Remote-to-Local) — unauthorized remote access (e.g. `guess_passwd`)
- **U2R** (User-to-Root) — privilege escalation after access (e.g. `buffer_overflow`, `rootkit`)

Notably, **NSL-KDD's test set includes attack types that never appear in training** — a deliberate design choice that simulates detecting genuinely novel attacks, and makes this dataset a meaningful test of generalization rather than memorization.

Class balance (training set):

| Category | Count | % of data |
|---|---|---|
| normal | 67,343 | 53.5% |
| DoS | 45,927 | 36.5% |
| Probe | 11,656 | 9.3% |
| R2L | 995 | 0.8% |
| U2R | 52 | 0.04% |

## Approach

1. **Preprocessing** — one-hot encoded categorical features (`protocol_type`, `service`, `flag`), encoded train/test jointly to guarantee identical columns, then scaled numeric features with `StandardScaler` (fit on train only, to avoid leaking test distribution).

2. **Dimensionality reduction (PCA)** — one-hot encoding expanded the feature space to 122 columns, many of them sparse (the `service` column alone contributes ~70 low-signal binary columns). Tested PCA at multiple component counts (20 through 122) and found lower-dimensional projections **matched or exceeded** higher-dimensional ones on anomaly separation, while reducing false positives. Final choice: **20 components**.

3. **Clustering (DBSCAN)** — tuned `eps` via the k-distance graph method (plotting each point's distance to its k-th nearest neighbor, sorted, and identifying the elbow where density drops off), cross-checked with a systematic grid sweep over `eps` and `min_samples`. Final parameters: **eps=0.8, min_samples=5**.

4. **Alternative tested: HDBSCAN** — tried as a way to handle DBSCAN's single global density threshold, since the dataset has both very dense (DoS) and very sparse (U2R) regions. HDBSCAN achieved higher *aggregate* recall, but on inspection this came from fragmenting the naturally dense DoS cluster rather than genuinely improving rare-anomaly detection — it broke the rarity-to-noise-rate pattern that is the actual signal of interest. DBSCAN was kept as the final model.

5. **Evaluation** — labels were used **only after** clustering was complete, purely to score results. They were never seen by the clustering algorithm itself, preserving the unsupervised premise.

## Key Finding

DBSCAN's noise-flagging rate scales **inversely with how common/repetitive an attack pattern is** — confirmed on held-out test data, including attack types the model never saw during training:

| Category | Test-set noise rate |
|---|---|
| U2R | **73.13%** |
| Probe | 9.83% |
| R2L | 4.02% |
| normal | 2.14% |
| DoS | 1.27% |

High-volume attacks like DoS form their own dense, repetitive clusters — structurally indistinguishable from "normal" density patterns, so DBSCAN correctly does *not* flag them as anomalies. Rare, low-frequency attacks like U2R don't have enough volume to form a dense pattern of their own, so they naturally fall out as noise — exactly the behavior the project set out to test.

**This pattern held on held-out test data containing novel attack types**, which is the real validation: the model is catching structurally unusual behavior, not memorized examples.

*(insert 2D PCA visualization pair here — noise-vs-clustered next to ground-truth-by-category)*

## Why clustering instead of classification, and why DBSCAN over Isolation Forest

- **Classification** requires labeled examples of every attack type it should recognize, and is blind to genuinely new attack patterns. NSL-KDD has labels, but they were deliberately ignored during modeling to simulate the real-world case where new attacks are unlabeled by definition.
- **Isolation Forest** (used previously in the AutoInsight API project) isolates points individually via random feature splits — it has no concept of neighborhoods or behavior families. NSL-KDD's traffic naturally clusters into distinct legitimate behavior types (different protocols/services); DBSCAN's density-based approach can represent that structure directly, and a point's "unusualness" is judged relative to nearby behavior, not just isolated in a vacuum.

## Honest Limitations

- **Not a general-purpose attack detector.** Aggregate recall is low (dominated by DoS's sheer volume in the denominator) — the per-category breakdown is the metric that actually reflects the model's value, not a single blended recall number.
- **R2L detection stayed modest (~4%)** even after tuning — R2L attacks (e.g. stolen credentials) may resemble normal traffic more closely in feature space than U2R does, making them structurally harder to separate by density alone.
- **HDBSCAN was tested but not adopted** — a fairer comparison would tune both algorithms with equal rigor across a wider parameter space; time-boxed scope limited this.
- **eps/PCA-component interaction is sensitive** — distances compress in lower-dimensional space, so `eps` had to be re-tuned after changing PCA components. This dependency isn't systematically characterized here, just re-validated at the final configuration.

## Tech Stack

Python, pandas, scikit-learn (DBSCAN, PCA, StandardScaler, NearestNeighbors), HDBSCAN, matplotlib

## Project Structure

```
network-anomaly-detection/
├── data/                  # raw CSVs (gitignored, regenerated via download_data.py)
├── download_data.py       # reproducible dataset fetch
├── notebooks/             # end-to-end analysis notebook
├── src/                   # reusable preprocessing/reduction code
└── outputs/
    ├── figures/           # k-distance graphs, PCA variance curve, cluster plots
    └── models/
```

## Running Locally

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1      # Windows
pip install -r requirements.txt
python download_data.py
# then open notebooks/ in Jupyter/VS Code
```