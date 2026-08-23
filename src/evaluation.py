"""
Evaluation: labels are used HERE ONLY -- this module just
grades the unsupervised result against ground truth.

Per-category noise rate is the PRIMARY metric for this project : overall recall is dominated by DoS's sheer volume and is a
misleading headline number on its own.
"""

import pandas as pd
def evaluate(labels, is_attack, attack_category):
    results = pd.DataFrame({
        "cluster" : labels,
        "is_attack": pd.Series(is_attack).reset_index(drop=True),
        "attack_category": pd.Series(attack_category).reset_index(drop=True)
    })
    noise_mask = results["cluster"] == -1
    n_noise = int(noise_mask.sum())

    if n_noise > 0:
        attacks_in_noise = int(results.loc[noise_mask, "is_attack"].sum())
        precision =  attacks_in_noise/n_noise
        recall = attacks_in_noise/results["is_attack"].sum()

    else:
        precision = 0.0
        recall = 0.0

    noise_rate_by_category = (
        results[noise_mask]["attack_category"].value_counts() / results["attack_category"].value_counts()
        * 100
    ).round(2).sort_values(ascending=False)

    return {
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "noise_rate_by_category": noise_rate_by_category,
        "results_df": results,
    }

def print_report(eval_result, title="Evaluation"):
    print(f"\n=== {title} ===")
    print("Primary metric -- noise rate per category:")
    print(eval_result["noise_rate_by_category"])
    print("\nSecondary metric (context only, dominated by DoS volume):")
    print(f"  Overall precision: {eval_result['precision']}")
    print(f"  Overall recall:    {eval_result['recall']}")