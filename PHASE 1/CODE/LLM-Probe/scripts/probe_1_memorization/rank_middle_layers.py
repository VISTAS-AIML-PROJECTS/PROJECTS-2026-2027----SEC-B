import os
import sys
import pickle
import numpy as np
import pandas as pd

# Include parent folder in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from llm_probe.core.layer_selection import rank_layers

CHECKPOINT_PATH = "data/memorization/labeled/activations_checkpoint.pkl"
DATASET_PATH = "data/memorization/labeled/dataset.parquet"

def main():
    if not os.path.exists(CHECKPOINT_PATH):
        print(f"Error: Checkpoint not found at: {CHECKPOINT_PATH}")
        sys.exit(1)
    if not os.path.exists(DATASET_PATH):
        print(f"Error: Dataset not found at: {DATASET_PATH}")
        sys.exit(1)
        
    # Load dataset
    df = pd.read_parquet(DATASET_PATH)
    labels = np.where(df['label'] == 'memorized', 1, 0)
    
    # Load cached activations
    print("Loading cached activations checkpoint...")
    with open(CHECKPOINT_PATH, 'rb') as f:
        activations_dict = pickle.load(f)
        
    num_examples = len(df)
    hidden_dim = activations_dict[df['source_id'].iloc[0]][0]['last_token'].shape[0]
    
    # Restrict to layers 5 to 15
    middle_layers = list(range(5, 16))
    
    last_token_by_layer = {l: np.zeros((num_examples, hidden_dim), dtype=np.float32) for l in middle_layers}
    mean_pooled_by_layer = {l: np.zeros((num_examples, hidden_dim), dtype=np.float32) for l in middle_layers}
    
    print("Compiling activation matrices for layers 5 to 15...")
    for idx, row in df.iterrows():
        sid = row['source_id']
        if sid not in activations_dict:
            continue
        example_acts = activations_dict[sid]
        for l in middle_layers:
            last_token_by_layer[l][idx] = example_acts[l]['last_token'].astype(np.float32)
            mean_pooled_by_layer[l][idx] = example_acts[l]['mean_pooled'].astype(np.float32)
            
    # Rank layers
    print("Computing Cohen's d for middle layers...")
    rankings_last = rank_layers(last_token_by_layer, labels)
    rankings_mean = rank_layers(mean_pooled_by_layer, labels)
    
    print("\n" + "="*50)
    print(" MIDDLE LAYERS (5-15) COHEN'S D RANKINGS")
    print("="*50)
    print("Top 3 Layers (last_token):")
    for rank_idx, (layer_idx, score) in enumerate(rankings_last[:3]):
        print(f"  Rank {rank_idx+1}: Layer {layer_idx} (d={score:.4f})")
        
    print("\nTop 3 Layers (mean_pooled):")
    for rank_idx, (layer_idx, score) in enumerate(rankings_mean[:3]):
        print(f"  Rank {rank_idx+1}: Layer {layer_idx} (d={score:.4f})")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
