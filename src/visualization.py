"""
Visualization: k-distance graph (for eps selection), PCA variance curve,
and 2D cluster plots (noise vs clustered, and ground-truth categories)
for the README / demo.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA

from . import config

os.makedirs(config.FIGURES_DIR, exist_ok=True)


def plot_k_distance(k_distances, min_samples, filename="k_distance.png", zoom_last_pct=0.10):
    zoom_start = int(len(k_distances) * (1 - zoom_last_pct))

    plt.figure(figsize=(10, 5))
    plt.plot(range(zoom_start, len(k_distances)), k_distances[zoom_start:])
    plt.xlabel(f"Points sorted by distance (zoomed to last {int(zoom_last_pct*100)}%)")
    plt.ylabel(f"Distance to {min_samples}-th nearest neighbor")
    plt.title("K-distance graph for eps selection")
    plt.grid(True)
    path = os.path.join(config.FIGURES_DIR, filename)
    plt.savefig(path, dpi=120, bbox_inches="tight")
    plt.close()
    return path


def plot_pca_variance(cumulative_variance, chosen_n_components, filename="pca_variance.png"):
    plt.figure(figsize=(8, 5))
    plt.plot(range(1, len(cumulative_variance) + 1), cumulative_variance)
    plt.axvline(x=chosen_n_components, color="g", linestyle="--",
                label=f"{chosen_n_components} components (chosen)")
    plt.xlabel("Number of PCA components")
    plt.ylabel("Cumulative explained variance")
    plt.title("PCA: cumulative explained variance")
    plt.legend()
    path = os.path.join(config.FIGURES_DIR, filename)
    plt.savefig(path, dpi=120, bbox_inches="tight")
    plt.close()
    return path


def plot_clusters_2d(X, labels, filename="clusters_2d.png", title="DBSCAN: Noise vs Clustered"):
    """Project X to 2D with a fresh PCA (for visualization only) and plot noise vs clustered."""
    X_2d = PCA(n_components=2).fit_transform(X)

    clustered_mask = labels != -1
    noise_mask = labels == -1

    plt.figure(figsize=(10, 7))
    plt.scatter(X_2d[clustered_mask, 0], X_2d[clustered_mask, 1],
                c="lightgray", s=8, alpha=0.5, label="Clustered (normal density)")
    plt.scatter(X_2d[noise_mask, 0], X_2d[noise_mask, 1],
                c="red", s=20, alpha=0.8, label="Noise (anomaly)")
    plt.xlabel("PCA Component 1")
    plt.ylabel("PCA Component 2")
    plt.title(title)
    plt.legend()
    path = os.path.join(config.FIGURES_DIR, filename)
    plt.savefig(path, dpi=120, bbox_inches="tight")
    plt.close()
    return path


def plot_ground_truth_2d(X, attack_category, filename="ground_truth_2d.png",
                          title="Ground Truth: Attack Categories"):
    X_2d = PCA(n_components=2).fit_transform(X)
    colors = {"normal": "lightgray", "DoS": "orange", "Probe": "blue",
              "R2L": "green", "U2R": "red"}

    plt.figure(figsize=(10, 7))
    for cat, color in colors.items():
        mask = (attack_category == cat).values if hasattr(attack_category, "values") else (attack_category == cat)
        size = 80 if cat == "U2R" else (30 if cat == "R2L" else 8)
        plt.scatter(X_2d[mask, 0], X_2d[mask, 1], c=color, s=size, alpha=0.6, label=cat)
    plt.xlabel("PCA Component 1")
    plt.ylabel("PCA Component 2")
    plt.title(title)
    plt.legend()
    path = os.path.join(config.FIGURES_DIR, filename)
    plt.savefig(path, dpi=120, bbox_inches="tight")
    plt.close()
    return path