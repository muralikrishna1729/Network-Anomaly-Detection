import numpy as np
from . import config
from . import data_loader
from . import preprocessing
from . import dimensionality_reduction
from . import clustering
from . import evaluation
from . import visualization as viz
from . import persistence
from .logging_utils import get_logger

logger = get_logger(__name__)

def run_pipeline(eps=None, min_samples=None, pca_components=None, sample_size=None, seed=None, save_model=False, verbose=True):
    # Run the full pipeline: load -> preprocess -> reduce -> cluster -> evaluate.
    eps = eps if eps is not None else config.DBSCAN_EPS
    min_samples = min_samples or config.DBSCAN_MIN_SAMPLES
    pca_components = pca_components or config.PCA_N_COMPONENTS
    sample_size = sample_size if sample_size is not None else config.TRAIN_SAMPLE_SIZE
    seed = seed if seed is not None else config.RANDOM_SEED

    logger.info(f"eps={eps}, min_samples={min_samples}, pca_components={pca_components}, sample_size={sample_size}, seed={seed}")
    train_df, test_df = data_loader.load_labeled_data()
    logger.info(f"Train: {train_df.shape}, Test: {test_df.shape}")
    logger.info("Datasets Loading..")

    preprocess = preprocessing.preprocess(train_df, test_df)
    logger.info("STEP 2: Preprocess (encode + scale)")
    logger.info(f"Encoded+scaled train: {preprocess['X_train_scaled'].shape}")
    logger.info(f"Encoded+scaled test:  {preprocess['X_test_scaled'].shape}")

    X_train_pca, X_test_pca, pca = dimensionality_reduction.reduce(
        preprocess["X_train_scaled"], preprocess["X_test_scaled"], n_components=pca_components
    )
    logger.info(f"Reduced train: {X_train_pca.shape}, "
                f"variance explained: {pca.explained_variance_ratio_.sum():.4f}")

    cumulative_variance = dimensionality_reduction.explained_variance_curve(
        preprocess["X_train_scaled"]
    )
    viz.plot_pca_variance(cumulative_variance, pca_components)

    logger.info("\n" + "=" * 60)
    logger.info("STEP 4: Subsample training data for tuning-speed clustering")
    logger.info("=" * 60)

    if sample_size and sample_size < len(X_train_pca):
        np.random.seed(seed)
        sample_idx = np.random.choice(len(X_train_pca), size=sample_size, replace=False)
        X_train_sample = X_train_pca[sample_idx]
        y_train_sample = train_df["is_attack"].iloc[sample_idx].reset_index(drop=True)
        cat_train_sample = train_df["attack_category"].iloc[sample_idx].reset_index(drop=True)
    else:
        X_train_sample = X_train_pca
        y_train_sample = train_df["is_attack"]
        cat_train_sample = train_df["attack_category"]
    logger.info(f"Sample size: {X_train_sample.shape[0]}")

    logger.info("\n" + "=" * 60)
    logger.info(f"STEP 5: DBSCAN (eps={eps}, min_samples={min_samples}) on training sample")
    logger.info("=" * 60)

    k_dist = clustering.k_distance_values(X_train_sample, min_samples = min_samples)
    viz.plot_k_distance(k_dist, min_samples, filename="k_distance_train.png")

    labels_train, dbscan_model = clustering.run_dbscan(
        X_train_sample, eps=eps, min_samples=min_samples
    )
    logger.info(str(clustering.cluster_summary(labels_train)))

    train_eval = evaluation.evaluate(labels_train, y_train_sample, cat_train_sample)
    if verbose:
        evaluation.print_report(train_eval, title="Training sample evaluation")
    viz.plot_clusters_2d(X_train_sample, labels_train,
                          filename="clusters_2d_train.png", title="DBSCAN Results (Train Sample)")
    viz.plot_ground_truth_2d(X_train_sample, cat_train_sample,
                              filename="ground_truth_2d_train.png", title="Ground Truth (Train Sample)")

    logger.info("\n" + "=" * 60)
    logger.info("STEP 6: Validate on held-out TEST set (includes novel attack types)")
    logger.info("=" * 60)
    labels_test, _ = clustering.run_dbscan(X_test_pca, eps=eps, min_samples=min_samples)
    logger.info(str(clustering.cluster_summary(labels_test)))

    test_eval = evaluation.evaluate(labels_test, test_df["is_attack"], test_df["attack_category"])
    if verbose:
        evaluation.print_report(test_eval, title="TEST SET evaluation (final result)")

    viz.plot_clusters_2d(X_test_pca, labels_test,
                          filename="clusters_2d_test.png", title="DBSCAN Results (Test Set)")
    viz.plot_ground_truth_2d(X_test_pca, test_df["attack_category"],
                              filename="ground_truth_2d_test.png", title="Ground Truth (Test Set)")

    if save_model:
        logger.info("\n" + "=" * 60)
        logger.info("Saving fitted artifacts to outputs/models/")
        logger.info("=" * 60)
        persistence.save_artifacts(
            scaler=preprocess["scaler"],
            pca=pca,
            dbscan_params={"eps": eps, "min_samples": min_samples},
            feature_names=preprocess["feature_names"],
            train_coords=X_train_sample,
        )
    logger.info("\n" + "=" * 60)
    logger.info(f"DONE. Figures saved to: {config.FIGURES_DIR}")
    logger.info("=" * 60)

    return {
        "train_eval": train_eval,
        "test_eval": test_eval,
        "scaler": preprocess["scaler"],
        "pca": pca,
        "dbscan_model": dbscan_model,
        "feature_names": preprocess["feature_names"],
    }












