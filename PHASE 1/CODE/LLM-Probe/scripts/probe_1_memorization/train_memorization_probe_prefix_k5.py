"""
Prefix-training probe for Probe 1 (Memorization) — K=5 prefix experiment.

Training strategy: for each labeled example, use K=5 prefix representations
(mean_pooled at t=round(N*k/5) for k=1..5) to build an expanded training matrix.
All K prefix vectors from one example stay in the same split (example-level split).
Labels are propagated: each of the 5 vectors for example i gets label y_i.

Primary evaluation: k=5 vectors from test examples (full-continuation mean_pooled).
This is the scientifically valid comparison to the baseline corrected experiment.

DOES NOT overwrite:
    data/memorization/labeled/activations_checkpoint.pkl       (baseline checkpoint)
    results/memorization/probe.joblib                          (baseline probe)

Writes to:
    results/memorization/probe_prefix_k5.joblib

Frozen baseline corrected numbers (must remain reproducible):
    Memorization LR F1 = 0.5625, OOD F1 = 0.000
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

DATASET_PATH = "data/memorization/labeled/dataset.parquet"
PREFIX_CHECKPOINT_PATH = "data/memorization/labeled/prefix_activations_k5_checkpoint.pkl"
BASELINE_CHECKPOINT_PATH = "data/memorization/labeled/activations_checkpoint.pkl"
BASELINE_PROBE_PATH = "results/memorization/probe.joblib"
PREFIX_PROBE_PATH = "results/memorization/probe_prefix_k5.joblib"
RESULTS_DIR = "results/memorization"
K_PREFIXES = 5


def main():
    logger.info("=== Memorization Prefix-Training Probe (K=5) ===")
    _assert_baseline_untouched()

    # 1. Load dataset
    if not os.path.exists(DATASET_PATH):
        logger.error(f"Dataset not found: {DATASET_PATH}")
        sys.exit(1)
    df = pd.read_parquet(DATASET_PATH).reset_index(drop=True)
    labels = np.where(df['label'] == 'memorized', 1, 0)
    logger.info(f"Loaded {len(df)} examples. Memorized: {labels.sum()}, Novel: {(labels == 0).sum()}")

    # 2. Load prefix checkpoint
    if not os.path.exists(PREFIX_CHECKPOINT_PATH):
        logger.error(f"Prefix checkpoint not found: {PREFIX_CHECKPOINT_PATH}")
        logger.error("Run build_prefix_activations_memorization.py first.")
        sys.exit(1)
    with open(PREFIX_CHECKPOINT_PATH, 'rb') as f:
        prefix_ck = pickle.load(f)
    logger.info(f"Loaded prefix checkpoint: {len(prefix_ck)} examples.")

    # 3. Filter to examples with prefix activations
    valid_mask = [row['source_id'] in prefix_ck for _, row in df.iterrows()]
    df = df[valid_mask].reset_index(drop=True)
    labels = labels[valid_mask]
    num_examples = len(df)
    logger.info(f"Valid examples (in checkpoint): {num_examples}")

    # 4. Compile prefix_by_layer[k][l] = shape (n_examples, hidden_dim) float32
    sample_sid = df['source_id'].iloc[0]
    num_layers = len(prefix_ck[sample_sid][1])
    hidden_dim = prefix_ck[sample_sid][1][0]['mean_pooled'].shape[0]
    logger.info(f"Architecture: {num_layers} layers, hidden_dim={hidden_dim}")

    logger.info("Compiling prefix feature matrices (K=5 × num_layers)...")
    # prefix_by_layer[k][l] = np.ndarray(n_examples, hidden_dim) float32
    prefix_by_layer = {
        k: {l: np.zeros((num_examples, hidden_dim), dtype=np.float32) for l in range(num_layers)}
        for k in range(1, K_PREFIXES + 1)
    }
    for i, row in df.iterrows():
        sid = row['source_id']
        for k in range(1, K_PREFIXES + 1):
            for l in range(num_layers):
                prefix_by_layer[k][l][i] = prefix_ck[sid][k][l]['mean_pooled'].astype(np.float32)

    # 5. Example-level stratified 80/20 split
    # All K prefix vectors for an example move together into train or test.
    indices = np.arange(num_examples)
    train_idx, test_idx, y_train, y_test = train_test_split(
        indices, labels, test_size=0.2, stratify=labels, random_state=42
    )
    logger.info(
        f"Example-level split: {len(train_idx)} train / {len(test_idx)} test "
        f"(memorized: {y_train.sum()} train / {y_test.sum()} test)"
    )

    # 6. Build expanded training matrix
    # Stack k=1..5 for each train example: shape (5*N_train, hidden_dim) per layer.
    # Row ordering: [ex0_k1, ex0_k2, ..., ex0_k5, ex1_k1, ...] so np.repeat(y_train, 5) is correct.
    logger.info("Building expanded training matrix (5 prefix vectors per example)...")
    train_expanded_by_layer = {}
    for l in range(num_layers):
        parts = [prefix_by_layer[k][l][train_idx] for k in range(1, K_PREFIXES + 1)]
        # parts[i] is (N_train, hidden_dim) for prefix k=i+1
        # np.stack(parts, axis=1) → (N_train, K, hidden_dim); reshape → (N_train*K, hidden_dim)
        train_expanded_by_layer[l] = np.stack(parts, axis=1).reshape(len(train_idx) * K_PREFIXES, hidden_dim)

    y_train_expanded = np.repeat(y_train, K_PREFIXES)
    logger.info(f"Expanded train matrix: {len(y_train_expanded)} rows "
                f"(memorized: {y_train_expanded.sum()}, novel: {(y_train_expanded == 0).sum()})")

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

    # 9. Train probe on expanded (pseudoreplicated) training set
    logger.info("Training Logistic Regression probe on expanded prefix training data...")
    probe = train_probe(X_train_scaled, y_train_expanded, use_mlp=False)

    # 10. Primary evaluation: k=5 test vectors (full continuation mean_pooled)
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

    # 13. Per-prefix evaluation (k=1..5) on test set — diagnostic only, not for tuning
    logger.info("=== Per-prefix-length evaluation on test set (diagnostic, not for tuning) ===")
    for k in range(1, K_PREFIXES + 1):
        X_test_k = np.hstack([prefix_by_layer[k][l][test_idx] for l in selected_layers])
        X_test_k_scaled = scaler.transform(X_test_k)
        m = evaluate_probe(probe, X_test_k_scaled, y_test)
        logger.info(f"  k={k}: F1={m['f1']:.4f}, Acc={m['accuracy']:.4f}, Rec={m['recall']:.4f}")

    # 14. OOD generalization (code_snippets held out)
    logger.info("=== OOD Generalization (code_snippets held out) ===")
    ood_train_mask = (df['source_category'] != 'code_snippets').values
    ood_test_mask  = (df['source_category'] == 'code_snippets').values

    ood_train_idx = np.where(ood_train_mask)[0]
    ood_test_idx  = np.where(ood_test_mask)[0]

    y_ood_train = labels[ood_train_idx]
    y_ood_test  = labels[ood_test_idx]

    logger.info(f"OOD training: {len(ood_train_idx)} non-code examples ({y_ood_train.sum()} memorized)")
    logger.info(f"OOD testing : {len(ood_test_idx)} code examples ({y_ood_test.sum()} memorized)")

    # Fresh layer selection on OOD training expanded matrix
    ood_train_expanded_by_layer = {}
    for l in range(num_layers):
        parts = [prefix_by_layer[k][l][ood_train_idx] for k in range(1, K_PREFIXES + 1)]
        ood_train_expanded_by_layer[l] = np.stack(parts, axis=1).reshape(len(ood_train_idx) * K_PREFIXES, hidden_dim)

    y_ood_train_expanded = np.repeat(y_ood_train, K_PREFIXES)

    logger.info("OOD: ranking layers on non-code expanded training data only...")
    ood_rankings = rank_layers(ood_train_expanded_by_layer, y_ood_train_expanded)
    ood_selected_layers = [item[0] for item in ood_rankings[:3]]
    logger.info(f"OOD selected layers: {ood_selected_layers}")

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
    ood_prec_str = "UNDEFINED" if prec_undefined else f"{ood_metrics['precision']:.4f}"
    logger.info("=== OOD Evaluation (k=5 code_snippets test, LR) ===")
    logger.info(f"OOD Accuracy : {ood_metrics['accuracy']:.4f}")
    logger.info(f"OOD Precision: {ood_prec_str}")
    logger.info(f"OOD Recall   : {ood_metrics['recall']:.4f}")
    logger.info(f"OOD F1 Score : {ood_metrics['f1']:.4f}")
    logger.info(f"Positive predictions: {pos_preds} (TP={cm[1,1]}, FP={cm[0,1]})")
    logger.info(f"OOD Confusion Matrix:\n{cm}")

    # 15. Summary
    print("\n" + "=" * 55)
    print(" PREFIX-TRAINING PROBE K=5 — MEMORIZATION SUMMARY")
    print("=" * 55)
    print(f"Representation     : mean_pooled (prefix k=1..5 expanded)")
    print(f"Selected Layers    : {selected_layers}")
    print(f"In-Domain F1 (k=5) : {metrics['f1']:.4f}  (baseline corrected: 0.5625)")
    print(f"MLP F1    (k=5)    : {mlp_metrics['f1']:.4f}")
    print(f"Confusion Matrix (LR, k=5 test):\n{metrics['confusion_matrix']}")
    print("-" * 55)
    print(f"OOD Selected Layers: {ood_selected_layers}")
    print(f"OOD F1 (k=5 code)  : {ood_metrics['f1']:.4f}  (baseline corrected: 0.000)")
    print(f"OOD Precision      : {ood_prec_str} (pos_preds={pos_preds})")
    print(f"OOD Recall         : {ood_metrics['recall']:.4f}")
    print(f"OOD Confusion Matrix:\n{cm}")
    print("=" * 55 + "\n")

    _assert_baseline_untouched()


def _assert_baseline_untouched():
    if os.path.exists(BASELINE_CHECKPOINT_PATH):
        import stat
        size = os.path.getsize(BASELINE_CHECKPOINT_PATH)
        assert size > 100_000_000, f"Baseline checkpoint looks too small ({size} bytes) — possible corruption."
    assert not os.path.samefile(PREFIX_PROBE_PATH if os.path.exists(PREFIX_PROBE_PATH) else PREFIX_PROBE_PATH,
                                BASELINE_PROBE_PATH) if os.path.exists(BASELINE_PROBE_PATH) and os.path.exists(PREFIX_PROBE_PATH) else True, \
        "BUG: prefix probe path resolves to same file as baseline probe."


if __name__ == "__main__":
    main()
