"""
Prefix activation extraction for the hallucination probe (Probe 2).

Runs ONE forward pass per example and saves mean_pooled hidden states at
K=5 evenly-spaced prefix lengths of the generated answer.

New checkpoint path (does NOT overwrite the baseline checkpoint):
    data/hallucination/labeled/prefix_activations_k5_checkpoint.pkl

Checkpoint format:
    {
        question (str): {
            k (int 1..5): {
                layer_idx (int): {
                    'mean_pooled': np.ndarray(hidden_dim,)  [float32]
                }
            }
        }
    }

Float32 is used for storage, consistent with the existing hallucination activation pipeline.
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

DATASET_PATH = "data/hallucination/labeled/dataset.parquet"
PREFIX_CHECKPOINT_PATH = "data/hallucination/labeled/prefix_activations_k5_checkpoint.pkl"
BASELINE_CHECKPOINT_PATH = "data/hallucination/labeled/activations_checkpoint.pkl"
K_PREFIXES = 5
SAVE_INTERVAL = 50


def main():
    logger.info("=== Hallucination Prefix Activation Extraction (K=5) ===")

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
        q = row['question']
        if q not in prefix_ck:
            missing.append((q, row['question'], row['generated_answer']))

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
        for q, question, answer in tqdm(missing, desc="Extracting prefix activations"):
            if not isinstance(answer, str) or not answer.strip():
                logger.warning(f"Skipping question with empty answer: '{q[:60]}...'")
                continue

            try:
                # ONE forward pass → K=5 prefix representations (returned as float32)
                result = extract_prefix_activations(question, answer, model, tokenizer, k_prefixes=K_PREFIXES)
                # Store as float32 (consistent with hallucination baseline pipeline)
                prefix_ck[q] = result
                extracted += 1

            except Exception as e:
                logger.error(f"Failed to extract for question '{q[:60]}...': {e}")
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
    covered = sum(1 for _, row in df.iterrows() if row['question'] in prefix_ck)
    logger.info(f"Coverage: {covered}/{len(df)} dataset examples have prefix activations.")

    # Verify K=5 prefix structure on first available example
    sample_q = next(iter(prefix_ck))
    sample_entry = prefix_ck[sample_q]
    ks = sorted(sample_entry.keys())
    num_layers = len(sample_entry[ks[0]])
    hidden_dim = sample_entry[ks[0]][0]['mean_pooled'].shape[0]
    logger.info(f"Sample entry ks={ks}, num_layers={num_layers}, hidden_dim={hidden_dim}")


if __name__ == "__main__":
    main()
