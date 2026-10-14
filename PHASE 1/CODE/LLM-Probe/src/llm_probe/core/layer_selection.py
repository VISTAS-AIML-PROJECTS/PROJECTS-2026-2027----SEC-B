import os
import numpy as np
import matplotlib.pyplot as plt

def rank_layers(activations_by_layer, labels):
    """
    Rank layers by mean absolute Cohen's d across all hidden dimensions.

    Args:
        activations_by_layer: dict of np.ndarray per layer, shape (num_examples, hidden_dim),
                              or np.ndarray of shape (num_layers, num_examples, hidden_dim).
        labels: np.ndarray of shape (num_examples,) with binary values (0 or 1).

    Returns:
        list of (layer_index, mean_absolute_cohens_d) tuples, sorted descending.
    """
    if isinstance(activations_by_layer, np.ndarray):
        activations_dict = {i: activations_by_layer[i] for i in range(activations_by_layer.shape[0])}
    else:
        activations_dict = activations_by_layer

    labels = np.array(labels)
    idx_0 = np.where(labels == 0)[0]
    idx_1 = np.where(labels == 1)[0]
    n1, n2 = len(idx_0), len(idx_1)

    if n1 < 2 or n2 < 2:
        raise ValueError("Must have at least 2 examples in each class to compute Cohen's d.")

    rankings = []
    for layer_idx, acts in activations_dict.items():
        group0 = acts[idx_0, :]
        group1 = acts[idx_1, :]
        mean0 = np.mean(group0, axis=0)
        mean1 = np.mean(group1, axis=0)
        var0 = np.var(group0, axis=0, ddof=1)
        var1 = np.var(group1, axis=0, ddof=1)
        pooled_std = np.sqrt(((n1 - 1) * var0 + (n2 - 1) * var1) / (n1 + n2 - 2))
        d_vals = np.zeros_like(mean0)
        valid_mask = pooled_std > 0
        d_vals[valid_mask] = (mean0[valid_mask] - mean1[valid_mask]) / pooled_std[valid_mask]
        mean_abs_d = np.mean(np.abs(d_vals))
        rankings.append((layer_idx, mean_abs_d))

    rankings.sort(key=lambda x: x[1], reverse=True)
    return rankings

def plot_layer_rankings(rankings, save_path: str):
    sorted_by_layer = sorted(rankings, key=lambda x: x[0])
    layers = [item[0] for item in sorted_by_layer]
    effect_sizes = [item[1] for item in sorted_by_layer]

    plt.figure(figsize=(10, 5))
    plt.bar(layers, effect_sizes, color='skyblue', edgecolor='black')
    plt.xlabel('Layer Index')
    plt.ylabel("Mean Absolute Cohen's d")
    plt.title("Class Separation Strength (Cohen's d) per Layer")
    plt.xticks(layers)
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    top_layers = sorted(rankings, key=lambda x: x[1], reverse=True)[:3]
    for idx, (layer, size) in enumerate(top_layers):
        plt.bar(layer, size, color='coral', edgecolor='black', label='Top Layers' if idx == 0 else "")

    plt.legend()
    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path)
    plt.close()
