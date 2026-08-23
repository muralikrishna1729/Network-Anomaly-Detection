"""
Dimensionality reduction via PCA.

Why this matters here specifically: one-hot encoding produces ~122 columns,
many of them sparse (the `service` categorical alone expands into ~70 mostly-
zero columns). High dimensionality makes DBSCAN's distance calculations less
meaningful ("curse of dimensionality") and, empirically on this dataset,
carrying too many low-signal components actually hurt anomaly separation
rather than helping it -- see README for the component-count sweep that
justified settling on config.PCA_N_COMPONENTS.
"""

import numpy as np
from sklearn.decomposition import PCA
from . import config

def fit_pca(X_train_scaled, n_components = None):
    """Fit PCA on train only, return fitted transformer."""
    n_components = n_components or config.PCA_N_COMPONENTS
    pca = PCA(n_components=n_components)
    pca.fit(X_train_scaled)
    return pca

def reduce(X_train_scaled, X_test_scaled, n_components=None):
    """Fit PCA on train, transform both train and test."""
    pca = fit_pca(X_train_scaled, n_components=n_components)
    X_train_pca = pca.transform(X_train_scaled)
    X_test_pca = pca.transform(X_test_scaled)
    return X_train_pca, X_test_pca, pca

def explained_variance_curve(X_train_scaled):
    """Full-component PCA fit, for plotting cumulative explained variance."""
    pca_full = PCA()
    pca_full.fit(X_train_scaled)
    cumulative_variance = np.cumsum(pca_full.explained_variance_ratio_)
    return cumulative_variance
