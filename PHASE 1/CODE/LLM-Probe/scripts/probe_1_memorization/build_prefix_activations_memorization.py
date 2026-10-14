"""
Prefix activation extraction for the memorization probe (Probe 1).

Runs ONE forward pass per example and saves mean_pooled hidden states at
K=5 evenly-spaced prefix lengths of the generated continuation.

New checkpoint path (does NOT overwrite the baseline checkpoint):
    data/memorization/labeled/prefix_activations_k5_checkpoint.pkl

Checkpoint format:
    {
        source_id (str): {
            k (int 1..5): {
                layer_idx (int): {
                    'mean_pooled': np.ndarray(hidden_dim,)  [float16]
                }
            }
        }
    }

Float16 is used for storage, consistent with the existing memorization activation pipeline.
"""

import os
import sys
import pickle
import logging
import numpy as np
import pandas as pd
from tqdm import tqdm

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from llm_probe.config import MODEL_NAME, DEVICE
from llm_probe.models.loader import load_model, load_tokenizer
from llm_probe.core.activations import extract_prefix_activations

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATASET_PATH = "data/memorization/labeled/dataset.parquet"
PREFIX_CHECKPOINT_PATH = "data/memorization/labeled/prefix_activations_k5_checkpoint.pkl"
BASELINE_CHECKPOINT_PATH = "data/memorization/labeled/activations_checkpoint.pkl"
K_PREFIXES = 5
SAVE_INTERVAL = 50


def main():
    logger.info("=== Memorization Prefix Activation Extraction (K=5) ===")

    # Safety check: confirm we are NOT touching the baseline checkpoint
    assert PREFIX_CHECKPOINT_PATH != BASELINE_CHECKPOINT_PATH, \
        "BUG: prefix checkpoint path must differ from baseline checkpoint path."
    logger.info(f"Baseline checkpoint (untouched): {BASELINE_CHECKPOINT_PATH}")
    logger.info(f"New prefix checkpoint:           {PREFIX_CHECKPOINT_PATH}")

    # 1. Load dataset
    if not os.path.exists(DATASET_PATH):
        logger.error(f"Dataset not found: {DATASET_PATH}")
        sys.exit(1)

    df = pd.read_parquet(DATASET_PATH)
    logger.info(f"Loaded {len(df)} examples from {DATASET_PATH}")

    # 2. Load existing prefix checkpoint (for resume)
    prefix_ck = {}
    if os.path.exists(PREFIX_CHECKPOINT_PATH):
        try:
            with open(PREFIX_CHECKPOINT_PATH, 'rb') as f:
                prefix_ck = pickle.load(f)
            logger.info(f"Resumed: {len(prefix_ck)} examples already in prefix checkpoint.")
        except Exception as e:
            logger.warning(f"Could not load prefix checkpoint ({e}). Starting fresh.")

    # 3. Identify missing examples
    missing = []
    for _, row in df.iterrows():
        sid = row['source_id']
        if sid not in prefix_ck:
            missing.append((sid, row['prompt'], row['generated_continuation']))

    logger.info(f"Examples to extract: {len(missing)} / {len(df)}")

    if not missing:
        logger.info("All examples already in prefix checkpoint. Nothing to extract.")
        _report(df, prefix_ck)
        return

    # 4. Load model
    logger.info(f"Loading model '{MODEL_NAME}' on '{DEVICE}'...")
    model = load_model(MODEL_NAME, DEVICE)
    tokenizer = load_tokenizer(MODEL_NAME)

    # 5. Extract prefix activations
    extracted = 0
    try:
        for sid, prompt, continuation in tqdm(missing, desc="Extracting prefix activations"):
            if not isinstance(continuation, str) or not continuation.strip():
                logger.warning(f"Skipping {sid}: empty continuation.")
                continue

            try:
                # ONE forward pass → K=5 prefix representations
                result = extract_prefix_activations(prompt, continuation, model, tokenizer, k_prefixes=K_PREFIXES)

                # Convert mean_pooled arrays to float16 before storing
                result_f16 = {}
                for k, layer_dict in result.items():
                    result_f16[k] = {}
                    for layer_idx, reps in layer_dict.items():
                        result_f16[k][layer_idx] = {
                            'mean_pooled': reps['mean_pooled'].astype(np.float16)
                        }

                prefix_ck[sid] = result_f16
                extracted += 1

            except Exception as e:
                logger.error(f"Failed to extract for {sid}: {e}")
                continue

            if extracted % SAVE_INTERVAL == 0:
                _save(prefix_ck)
                logger.info(f"Checkpoint saved ({len(prefix_ck)} examples total).")

    except KeyboardInterrupt:
        logger.warning("Interrupted. Saving checkpoint before exit...")
        _save(prefix_ck)
        sys.exit(0)

    # 6. Final save
    _save(prefix_ck)
    logger.info(f"Extraction complete. {len(prefix_ck)} examples in prefix checkpoint.")
    _report(df, prefix_ck)


def _save(prefix_ck):
    os.makedirs(os.path.dirname(PREFIX_CHECKPOINT_PATH), exist_ok=True)
    tmp = PREFIX_CHECKPOINT_PATH + ".tmp"
    with open(tmp, 'wb') as f:
        pickle.dump(prefix_ck, f)
    if os.path.exists(PREFIX_CHECKPOINT_PATH):
        os.remove(PREFIX_CHECKPOINT_PATH)
    os.rename(tmp, PREFIX_CHECKPOINT_PATH)


def _report(df, prefix_ck):
    covered = sum(1 for _, row in df.iterrows() if row['source_id'] in prefix_ck)
    logger.info(f"Coverage: {covered}/{len(df)} dataset examples have prefix activations.")

    # Verify K=5 prefix structure on first available example
    sample_sid = next(iter(prefix_ck))
    sample_entry = prefix_ck[sample_sid]
    ks = sorted(sample_entry.keys())
    num_layers = len(sample_entry[ks[0]])
    hidden_dim = sample_entry[ks[0]][0]['mean_pooled'].shape[0]
    logger.info(f"Sample entry '{sample_sid}': k={ks}, num_layers={num_layers}, hidden_dim={hidden_dim}")


if __name__ == "__main__":
    main()
