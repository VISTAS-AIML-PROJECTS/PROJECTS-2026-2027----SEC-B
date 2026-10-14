import torch
import numpy as np

def extract_prefix_activations(prompt: str, continuation: str, model, tokenizer, k_prefixes: int = 5):
    """
    Extract mean_pooled hidden states for k_prefixes evenly-spaced prefix lengths of the continuation.

    Runs ONE forward pass on (prompt + full continuation).  Due to causal masking the hidden state
    at position (prompt_len + t - 1) depends only on tokens 0..prompt_len+t-1, so
    mean(h[prompt_len : prompt_len + t]) is identical to what a separate forward pass on
    (prompt + continuation[:t tokens]) would produce.  All K representations are therefore
    obtained at the cost of a single inference call.

    Prefix token lengths:
        t_k = max(1, min(round(N * k / k_prefixes), N))  for k = 1 .. k_prefixes
    k = k_prefixes always yields t = N (the full continuation).

    Returns:
        dict { k (int 1..k_prefixes) : { layer_idx (int) : { 'mean_pooled': np.ndarray(hidden_dim,) } } }
        Representations are returned as float32; callers should cast to float16 for storage if needed.
    """
    prompt_ids = tokenizer.encode(prompt, add_special_tokens=True)
    continuation_ids = tokenizer.encode(continuation, add_special_tokens=False)

    if len(continuation_ids) == 0:
        raise ValueError("Continuation cannot be empty.")

    N = len(continuation_ids)
    prompt_len = len(prompt_ids)
    combined_ids = prompt_ids + continuation_ids

    device = next(model.parameters()).device
    input_ids_tensor = torch.tensor([combined_ids], dtype=torch.long, device=device)
    attention_mask_tensor = torch.ones_like(input_ids_tensor, device=device)

    with torch.no_grad():
        outputs = model(
            input_ids=input_ids_tensor,
            attention_mask=attention_mask_tensor,
            output_hidden_states=True,
        )

    hidden_states = outputs.hidden_states  # tuple: (num_layers+1,) each (1, seq_len, hidden_dim)

    result = {}
    for k in range(1, k_prefixes + 1):
        t = round(N * k / k_prefixes)
        t = max(1, min(t, N))  # always in [1, N]; k=k_prefixes always gives t=N
        k_dict = {}
        for layer_idx, layer_hidden in enumerate(hidden_states):
            layer_seq = layer_hidden[0]  # (seq_len, hidden_dim)
            # Slice only the first t continuation tokens (equivalent to a prefix-only forward pass)
            prefix_slice = layer_seq[prompt_len : prompt_len + t, :]  # (t, hidden_dim)
            mean_pooled = prefix_slice.mean(dim=0)                     # (hidden_dim,)
            k_dict[layer_idx] = {
                'mean_pooled': mean_pooled.cpu().to(torch.float32).numpy()
            }
        result[k] = k_dict

    return result


def extract_activations(prompt: str, continuation: str, model, tokenizer):
    """
    Extract per-layer hidden states for a given prompt and continuation.

    Returns a dict mapping layer index (0 to num_layers) to:
        {'last_token': np.ndarray(hidden_size,), 'mean_pooled': np.ndarray(hidden_size,)}
    """
    prompt_ids = tokenizer.encode(prompt, add_special_tokens=True)
    continuation_ids = tokenizer.encode(continuation, add_special_tokens=False)

    if len(continuation_ids) == 0:
        raise ValueError("Continuation cannot be empty. It must contain at least one token.")

    combined_ids = prompt_ids + continuation_ids
    prompt_len = len(prompt_ids)

    device = next(model.parameters()).device
    input_ids_tensor = torch.tensor([combined_ids], dtype=torch.long, device=device)
    attention_mask_tensor = torch.ones_like(input_ids_tensor, device=device)

    with torch.no_grad():
        outputs = model(
            input_ids=input_ids_tensor,
            attention_mask=attention_mask_tensor,
            output_hidden_states=True
        )

    hidden_states = outputs.hidden_states

    activations = {}
    for layer_idx, layer_hidden in enumerate(hidden_states):
        layer_hidden_seq = layer_hidden[0]
        continuation_hidden = layer_hidden_seq[prompt_len:, :]
        last_token = continuation_hidden[-1, :]
        mean_pooled = continuation_hidden.mean(dim=0)
        activations[layer_idx] = {
            'last_token': last_token.cpu().to(torch.float32).numpy(),
            'mean_pooled': mean_pooled.cpu().to(torch.float32).numpy()
        }

    return activations
