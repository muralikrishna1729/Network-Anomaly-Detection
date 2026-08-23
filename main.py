import argparse
from src import config
from src.pipeline import run_pipeline

def parse_args():
    parser = argparse.ArgumentParser(
        description="Network Intrusion Anomaly Detection (NSL-KDD)"
    )
    parser.add_argument("--eps", type=float ,default=config.DBSCAN_EPS,
                        help=f"DBSCAN eps (default: {config.DBSCAN_EPS})")
    parser.add_argument("--min-samples", type=float ,default=config.DBSCAN_MIN_SAMPLES,
                            help=f"DBSCAN Min samples (default: {config.DBSCAN_MIN_SAMPLES})")
    parser.add_argument("--pca-components", type=int, default=config.PCA_N_COMPONENTS,
                         help=f"Number of PCA components (default: {config.PCA_N_COMPONENTS})")
    parser.add_argument("--sample-size", type=int, default=config.TRAIN_SAMPLE_SIZE,
                         help=f"Training subsample size, 0 = use full training set "
                              f"(default: {config.TRAIN_SAMPLE_SIZE})")
    parser.add_argument("--seed", type=int, default=config.RANDOM_SEED,
                         help=f"Random seed for subsampling (default: {config.RANDOM_SEED})")
    parser.add_argument("--save-model", action="store_true",
                         help="Persist fitted scaler/PCA/DBSCAN artifacts to outputs/models/ "
                              "(required before running the Flask app)")
    return parser.parse_args()


def main():
    args = parse_args()
    run_pipeline(
        eps = args.eps,
        min_samples = args.min_samples,
        pca_components = args.pca_components,
        sample_size = args.sample_size,
        seed = args.seed,
        save_model = args.save_model,
    )

if __name__ == "__main__":
    main()