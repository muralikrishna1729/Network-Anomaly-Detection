"""
Clustering: DBSCAN as the primary model, plus the k-distance graph helper
used to choose `eps`. HDBSCAN was evaluated during development as an
alternative (see README) but is not part of the final pipeline -- it produced
higher aggregate recall at the cost of fragmenting the dense DoS cluster,
which broke the rarity-to-noise-rate pattern that is the actual signal of
interest for this project.
"""

import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.neighbors import NearestNeighbors
from . import config

def k_distance_values(X, min_samples=None):
    """
    For each point, compute distance to its min_samples-th nearest neighbor,
    sorted ascending. Used to visually/programmatically find the eps elbow:
    the boundary between dense ('normal') and sparse ('anomalous') regions.
    """
    min_samples = min_samples or config.DBSCAN_MIN_SAMPLES
    neighbors = NearestNeighbors(n_neighbors=min_samples)
    neighbors.fit(X)
    distances, _ = neighbors.kneighbors(X)
    return np.sort(distances[:, -1])

def run_dbscan(X, eps=None, min_samples=None):
    """Run DBSCAN with given (or config default) parameters."""
    eps = eps if eps is not None else config.DBSCAN_EPS
    min_samples = min_samples or config.DBSCAN_MIN_SAMPLES
    model = DBSCAN(eps=eps, min_samples=min_samples)
    labels = model.fit_predict(X)
    return labels, model


def cluster_summary(labels):
    """Basic cluster/noise counts for a DBSCAN label array."""
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = int((labels == -1).sum())
    return {
        "n_clusters": n_clusters,
        "n_noise": n_noise,
        "noise_pct": round(n_noise / len(labels) * 100, 2),
    }