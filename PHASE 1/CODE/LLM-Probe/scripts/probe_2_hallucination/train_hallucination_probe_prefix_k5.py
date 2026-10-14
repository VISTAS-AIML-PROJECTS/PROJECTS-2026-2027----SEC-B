"""
Prefix-training probe for Probe 2 (Hallucination) — K=5 prefix experiment.

Training strategy: for each labeled example, use K=5 prefix representations
(mean_pooled at t=round(N*k/5) for k=1..5) to build an expanded training matrix.
All K prefix vectors from one example stay in the same split (example-level split).
Labels are propagated: each of the 5 vectors for example i gets label y_i.

Primary evaluation: k=5 vectors from test examples (full-continuation mean_pooled).
OOD generalization: held-out Misconceptions and Law categories.

DOES NOT overwrite:
    data/hallucination/labeled/activations_checkpoint.pkl      (baseline checkpoint)
    results/hallucination/probe.joblib                         (baseline probe)

Writes to:
    results/hallucination/probe_prefix_k5.joblib

Frozen baseline corrected numbers (must remain reproducible):
    Hallucination LR F1 = 0.6864
    OOD Misconceptions F1 = 0.3947, OOD Law F1 = 0.6133
"""

import os
import sys
import pickle
import logging
import warnings
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.exceptions import UndefinedMetricWarning

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from llm_probe.core.layer_selection import rank_layers
from llm_probe.core.probe import train_probe, evaluate_probe, save_probe

DATASET_PATH = "data/hallucination/labeled/dataset.parquet"
PREFIX_CHECKPOINT_PATH = "data/hallucination/labeled/prefix_activations_k5_checkpoint.pkl"
BASELINE_CHECKPOINT_PATH = "data/hallucination/labeled/activations_checkpoint.pkl"
BASELINE_PROBE_PATH = "results/hallucination/probe.joblib"
PREFIX_PROBE_PATH = "results/hallucination/probe_prefix_k5.joblib"
RESULTS_DIR = "results/hallucination"
K_PREFIXES = 5


def main():
    logger.info("=== Hallucination Prefix-Training Probe (K=5) ===")
    _assert_baseline_untouched()

    # 1. Load dataset
    if not os.path.exists(DATASET_PATH):
        logger.error(f"Dataset not found: {DATASET_PATH}")
        sys.exit(1)
    df = pd.read_parquet(DATASET_PATH)
    labels_raw = np.where(df['label'] == 'hallucinated', 1, 0)
    logger.info(f"Loaded {len(df)} examples. Hallucinated: {labels_raw.sum()}, Grounded: {(labels_raw == 0).sum()}")

    # 2. Load prefix checkpoint
    if not os.path.exists(PREFIX_CHECKPOINT_PATH):
        logger.error(f"Prefix checkpoint not found: {PREFIX_CHECKPOINT_PATH}")
        logger.error("Run build_prefix_activations_hallucination.py first.")
        sys.exit(1)
    with open(PREFIX_CHECKPOINT_PATH, 'rb') as f:
        prefix_ck = pickle.load(f)
    logger.info(f"Loaded prefix checkpoint: {len(prefix_ck)} examples.")

    # 3. Filter to examples with prefix activations (mirrors baseline hallucination script)
    valid_indices = []
    valid_labels = []
    valid_rows = []
    for idx, row in df.iterrows():
        q = row['question']
        if q in prefix_ck:
            valid_indices.append(idx)
            valid_labels.append(labels_raw[idx])
            valid_rows.append(row)

    df = pd.DataFrame(valid_rows).reset_index(drop=True)
    labels = np.array(valid_labels)
    num_examples = len(df)
    logger.info(f"Valid examples (in checkpoint): {num_examples}")
    if num_examples == 0:
        logger.error("No valid examples with prefix activations. Exiting.")
        sys.exit(1)

    # 4. Compile prefix_by_layer[k][l] = shape (n_examples, hidden_dim) float32
    sample_q = df['question'].iloc[0]
    num_layers = len(prefix_ck[sample_q][1])
    hidden_dim = prefix_ck[sample_q][1][0]['mean_pooled'].shape[0]
    logger.info(f"Architecture: {num_layers} layers, hidden_dim={hidden_dim}")

    logger.info("Compiling prefix feature matrices (K=5 × num_layers)...")
    prefix_by_layer = {
        k: {l: np.zeros((num_examples, hidden_dim), dtype=np.float32) for l in range(num_layers)}
        for k in range(1, K_PREFIXES + 1)
    }
    for i, row in df.iterrows():
        q = row['question']
        for k in range(1, K_PREFIXES + 1):
            for l in range(num_layers):
                prefix_by_layer[k][l][i] = prefix_ck[q][k][l]['mean_pooled'].astype(np.float32)

    # 5. Example-level stratified 80/20 split
    indices = np.arange(num_examples)
    train_idx, test_idx, y_train, y_test = train_test_split(
        indices, labels, test_size=0.2, stratify=labels, random_state=42
    )
    logger.info(
        f"Example-level split: {len(train_idx)} train / {len(test_idx)} test "
        f"(hallucinated: {y_train.sum()} train / {y_test.sum()} test)"
    )

    # 6. Build expanded training matrix
    logger.info("Building expanded training matrix (5 prefix vectors per example)...")
    train_expanded_by_layer = {}
    for l in range(num_layers):
        parts = [prefix_by_layer[k][l][train_idx] for k in range(1, K_PREFIXES + 1)]
        train_expanded_by_layer[l] = np.stack(parts, axis=1).reshape(len(train_idx) * K_PREFIXES, hidden_dim)

    y_train_expanded = np.repeat(y_train, K_PREFIXES)
    logger.info(f"Expanded train matrix: {len(y_train_expanded)} rows "
                f"(hallucinated: {y_train_expanded.sum()}, grounded: {(y_train_expanded == 0).sum()})")

    # 7. Layer selection on expanded training data (mean_pooled only, train split only)
    logger.info("Ranking layers via Cohen's d on expanded training data (mean_pooled only)...")
    rankings = rank_layers(train_expanded_by_layer, y_train_expanded)

    logger.info("=== Top 5 Layers (prefix-expanded mean_pooled, train only) ===")
    for rank_i, (layer_idx, score) in enumerate(rankings[:5]):
        logger.info(f"  Rank {rank_i+1}: Layer {layer_idx} (d={score:.4f})")

    selected_layers = [item[0] for item in rankings[:3]]
    logger.info(f"Selected top-3 layers: {selected_layers}")

    # 8. Assemble training features
    X_train = np.hstack([train_expanded_by_layer[l] for l in selected_layers])
    logger.info(f"X_train shape: {X_train.shape}")

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)

    # 9. Train probe on expanded training set
    logger.info("Training Logistic Regression probe on expanded prefix training data...")
    probe = train_probe(X_train_scaled, y_train_expanded, use_mlp=False)

    # 10. Primary evaluation: k=5 test vectors
    logger.info("Evaluating on k=5 (full continuation) test vectors...")
    X_test_k5 = np.hstack([prefix_by_layer[K_PREFIXES][l][test_idx] for l in selected_layers])
    X_test_k5_scaled = scaler.transform(X_test_k5)
    metrics = evaluate_probe(probe, X_test_k5_scaled, y_test)

    logger.info("=== Primary Evaluation (k=5 test features, example-level split) ===")
    logger.info(f"Accuracy : {metrics['accuracy']:.4f}")
    logger.info(f"Precision: {metrics['precision']:.4f}")
    logger.info(f"Recall   : {metrics['recall']:.4f}")
    logger.info(f"F1 Score : {metrics['f1']:.4f}")
    logger.info("\nClassification Report:\n" + metrics['report'])
    logger.info("\nConfusion Matrix:\n" + str(metrics['confusion_matrix']))

    # 11. Save probe (compatible with demo/inference.py payload format)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    probe_dict = {
        'probe': probe,
        'scaler': scaler,
        'selected_layers': selected_layers,
        'representation_type': 'mean_pooled',
    }
    save_probe(probe_dict, PREFIX_PROBE_PATH)
    logger.info(f"Saved prefix probe to: {PREFIX_PROBE_PATH}")
    _assert_baseline_untouched()

    # 12. MLP validation
    logger.info("Training MLP probe for validation...")
    mlp_probe = train_probe(X_train_scaled, y_train_expanded, use_mlp=True)
    mlp_metrics = evaluate_probe(mlp_probe, X_test_k5_scaled, y_test)
    logger.info(f"MLP F1 Score (k=5 test): {mlp_metrics['f1']:.4f}")

    # 13. Per-prefix evaluation on test set — diagnostic only
    logger.info("=== Per-prefix-length evaluation on test set (diagnostic, not for tuning) ===")
    for k in range(1, K_PREFIXES + 1):
        X_test_k = np.hstack([prefix_by_layer[k][l][test_idx] for l in selected_layers])
        X_test_k_scaled = scaler.transform(X_test_k)
        m = evaluate_probe(probe, X_test_k_scaled, y_test)
        logger.info(f"  k={k}: F1={m['f1']:.4f}, Acc={m['accuracy']:.4f}, Rec={m['recall']:.4f}")

    # 14. OOD generalization (Misconceptions and Law held out)
    gen_results = {}
    for holdout_cat in ['Misconceptions', 'Law']:
        logger.info(f"=== OOD Generalization: '{holdout_cat}' held out ===")

        ood_train_mask = (df['category'] != holdout_cat).values
        ood_test_mask  = (df['category'] == holdout_cat).values
        ood_train_idx  = np.where(ood_train_mask)[0]
        ood_test_idx   = np.where(ood_test_mask)[0]

        y_ood_train = labels[ood_train_idx]
        y_ood_test  = labels[ood_test_idx]

        logger.info(f"  Training: {len(ood_train_idx)} examples ({y_ood_train.sum()} hallucinated)")
        logger.info(f"  Testing : {len(ood_test_idx)} examples ({y_ood_test.sum()} hallucinated)")

        if len(ood_test_idx) == 0:
            logger.warning(f"  No examples for '{holdout_cat}'. Skipping.")
            continue

        # Fresh layer selection on OOD training expanded matrix
        ood_train_expanded_by_layer = {}
        for l in range(num_layers):
            parts = [prefix_by_layer[k][l][ood_train_idx] for k in range(1, K_PREFIXES + 1)]
            ood_train_expanded_by_layer[l] = np.stack(parts, axis=1).reshape(len(ood_train_idx) * K_PREFIXES, hidden_dim)

        y_ood_train_expanded = np.repeat(y_ood_train, K_PREFIXES)

        logger.info(f"  OOD '{holdout_cat}': ranking layers on non-holdout expanded training data...")
        ood_rankings = rank_layers(ood_train_expanded_by_layer, y_ood_train_expanded)
        ood_selected_layers = [item[0] for item in ood_rankings[:3]]
        logger.info(f"  OOD selected layers: {ood_selected_layers}")

        X_ood_train = np.hstack([ood_train_expanded_by_layer[l] for l in ood_selected_layers])
        X_ood_test_k5 = np.hstack([prefix_by_layer[K_PREFIXES][l][ood_test_idx] for l in ood_selected_layers])

        ood_scaler = StandardScaler()
        X_ood_train_scaled = ood_scaler.fit_transform(X_ood_train)
        X_ood_test_scaled  = ood_scaler.transform(X_ood_test_k5)

        ood_probe = train_probe(X_ood_train_scaled, y_ood_train_expanded, use_mlp=False)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always", category=UndefinedMetricWarning)
            ood_metrics = evaluate_probe(ood_probe, X_ood_test_scaled, y_ood_test)
            prec_undefined = any(
                "precision" in str(warning.message).lower() or
                "f-score is ill-defined" in str(warning.message).lower()
                for warning in w
            )

        cm = ood_metrics['confusion_matrix']
        pos_preds = cm[0, 1] + cm[1, 1]
        prec_str = "UNDEFINED" if prec_undefined else f"{ood_metrics['precision']:.4f}"

        logger.info(f"  OOD '{holdout_cat}' F1: {ood_metrics['f1']:.4f}")
        logger.info(f"  OOD '{holdout_cat}' Accuracy: {ood_metrics['accuracy']:.4f}")
        logger.info(f"  OOD '{holdout_cat}' Precision: {prec_str} (pos_preds={pos_preds})")
        logger.info(f"  OOD '{holdout_cat}' Recall: {ood_metrics['recall']:.4f}")
        logger.info(f"  OOD Confusion Matrix:\n{cm}")

        gen_results[holdout_cat] = {
            'metrics': ood_metrics,
            'pos_preds': pos_preds,
            'prec_undefined': prec_undefined,
            'selected_layers': ood_selected_layers,
        }

    # 15. Summary
    print("\n" + "=" * 55)
    print(" PREFIX-TRAINING PROBE K=5 — HALLUCINATION SUMMARY")
    print("=" * 55)
    print(f"Representation     : mean_pooled (prefix k=1..5 expanded)")
    print(f"Selected Layers    : {selected_layers}")
    print(f"In-Domain F1 (k=5) : {metrics['f1']:.4f}  (baseline corrected: 0.6864)")
    print(f"MLP F1    (k=5)    : {mlp_metrics['f1']:.4f}")
    print(f"Confusion Matrix (LR, k=5 test):\n{metrics['confusion_matrix']}")
    print("-" * 55)
    baseline_ood = {'Misconceptions': 0.3947, 'Law': 0.6133}
    for holdout_cat, res in gen_results.items():
        m = res['metrics']
        ps = "UNDEFINED" if res['prec_undefined'] else f"{m['precision']:.4f}"
        print(f"OOD '{holdout_cat}' Layers   : {res['selected_layers']}")
        print(f"OOD '{holdout_cat}' F1 (k=5) : {m['f1']:.4f}  (baseline: {baseline_ood.get(holdout_cat, 'N/A')})")
        print(f"OOD '{holdout_cat}' Precision : {ps} (pos_preds={res['pos_preds']})")
        print(f"OOD '{holdout_cat}' Recall    : {m['recall']:.4f}")
        print(f"OOD Confusion Matrix:\n{res['metrics']['confusion_matrix']}")
        print("-" * 55)
    print("=" * 55 + "\n")

    _assert_baseline_untouched()


def _assert_baseline_untouched():
    if os.path.exists(BASELINE_CHECKPOINT_PATH):
        size = os.path.getsize(BASELINE_CHECKPOINT_PATH)
        assert size > 100_000_000, f"Baseline checkpoint looks too small ({size} bytes) — possible corruption."


if __name__ == "__main__":
    main()
