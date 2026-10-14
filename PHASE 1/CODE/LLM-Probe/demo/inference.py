"""
Live CLI Inference for LLM Probe.
Performs autoregressive generation with simultaneous dual-probe scoring for
both memorization and hallucination detection.
"""

import os
import sys
import argparse
import joblib
import torch
import numpy as np

# Include repository root in path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.append(REPO_ROOT)

from llm_probe.config import MODEL_NAME, DEVICE
from llm_probe.models.loader import load_model, load_tokenizer
from demo.render import render_terminal, CYAN, BOLD_CYAN, YELLOW, BOLD, RESET, GRAY


class ProbeResults(list):
    """List subclass holding generated token dicts with token counts metadata."""
    def __init__(self, items=(), token_counts=None):
        super().__init__(items)
        self.token_counts = token_counts or {}


MEM_PROBE_DEFAULT = "results/memorization/probe_prefix_k5.joblib"
HALLUC_PROBE_DEFAULT = "results/hallucination/probe_prefix_k5.joblib"


def load_probe_payload(probe_path="results/memorization/probe.joblib"):
    """
    Loads a saved probe and scaler payload.
    """
    if not os.path.exists(probe_path):
        raise FileNotFoundError(f"Trained probe payload not found at: {probe_path}")
    payload = joblib.load(probe_path)
    return payload


def generate_with_probe(
    prompt,
    model,
    tokenizer,
    probe,
    scaler,
    selected_layers,
    representation_type,
    max_tokens=100,
    halluc_probe=None,
    halluc_scaler=None,
    halluc_layers=None,
    halluc_representation_type=None,
):
    """
    Generates text token-by-token and predicts probe risk scores for each new token.
    Can run memorization probe alone, or memorization and hallucination probes simultaneously.

    Args:
        prompt: input text prompt
        model: loaded transformer model
        tokenizer: loaded tokenizer
        probe: primary probe classifier (memorization)
        scaler: primary scaler
        selected_layers: list of int layers for primary probe
        representation_type: 'mean_pooled' or 'last_token'
        max_tokens: maximum token limit for the generated answer
        halluc_probe: optional secondary probe classifier (hallucination)
        halluc_scaler: secondary scaler
        halluc_layers: list of int layers for secondary probe
        halluc_representation_type: secondary representation type

    Returns:
        ProbeResults (list of dicts containing 'token', 'score', 'mem_score', and optionally 'halluc_score')
        with .token_counts attribute containing prompt, generated, total counts, and max_tokens limit.
    """
    # 1. Encode prompt
    prompt_ids = tokenizer.encode(prompt, add_special_tokens=True)
    prompt_len = len(prompt_ids)

    device = next(model.parameters()).device

    # 2. Initial forward pass to predict the first token
    input_ids_tensor = torch.tensor([prompt_ids], dtype=torch.long, device=device)
    attention_mask_tensor = torch.ones_like(input_ids_tensor, device=device)
    with torch.no_grad():
        outputs = model(
            input_ids=input_ids_tensor,
            attention_mask=attention_mask_tensor,
            output_hidden_states=True,
        )

    next_token_logits = outputs.logits[0, -1, :]
    next_token_id = torch.argmax(next_token_logits).item()

    gen_ids = []
    token_entries = []

    # 3. Autoregressive generation and probing loop
    while len(gen_ids) < max_tokens:
        if next_token_id == tokenizer.eos_token_id:
            break

        gen_ids.append(next_token_id)
        token_str = tokenizer.decode([next_token_id])

        # Forward pass on the updated sequence (prompt + generated tokens)
        combined_ids = prompt_ids + gen_ids
        input_ids_tensor = torch.tensor([combined_ids], dtype=torch.long, device=device)
        attention_mask_tensor = torch.ones_like(input_ids_tensor, device=device)

        with torch.no_grad():
            outputs = model(
                input_ids=input_ids_tensor,
                attention_mask=attention_mask_tensor,
                output_hidden_states=True,
            )

        hidden_states = outputs.hidden_states

        # 4. Extract layer representations for the new prefix continuation
        #
        # NOTE — train/inference representation mismatch (documented limitation):
        # During training, each example's activations were extracted from the model
        # running over the FULL generated continuation in one forward pass, producing
        # a single sequence-level feature vector per example (mean_pooled or last_token
        # over all N continuation tokens).
        # Here, the probe is applied after every newly generated token, meaning the
        # feature at step t is computed over only t tokens of the growing continuation.
        # The distribution of mean_pooled(t tokens) differs from mean_pooled(N tokens),
        # so scores at early generation steps are produced from an out-of-distribution
        # feature space relative to the probe's training inputs.
        # Scores become more representative as the continuation grows toward the lengths
        # seen during training.  The sequence-level headline F1 evaluation is unaffected
        # by this gap — only the per-token display is subject to it.
        token_entry = {"token": token_str}

        # Memorization probe scoring
        if probe is not None and scaler is not None and selected_layers is not None:
            example_feat = []
            for layer in selected_layers:
                layer_hidden_seq = hidden_states[layer][0]
                continuation_hidden = layer_hidden_seq[prompt_len:, :]

                if representation_type == "last_token":
                    feat_vec = continuation_hidden[-1, :]
                else:
                    feat_vec = continuation_hidden.mean(dim=0)

                example_feat.append(feat_vec.cpu().to(torch.float32).numpy())

            X_token = np.concatenate(example_feat).reshape(1, -1)
            X_token_scaled = scaler.transform(X_token)
            mem_score = float(probe.predict_proba(X_token_scaled)[0, 1])
            token_entry["mem_score"] = mem_score
            token_entry["score"] = mem_score  # Backwards compatibility

        # Hallucination probe scoring (simultaneous evaluation)
        if (
            halluc_probe is not None
            and halluc_scaler is not None
            and halluc_layers is not None
        ):
            h_feat = []
            for layer in halluc_layers:
                layer_hidden_seq = hidden_states[layer][0]
                continuation_hidden = layer_hidden_seq[prompt_len:, :]

                if halluc_representation_type == "last_token":
                    feat_vec = continuation_hidden[-1, :]
                else:
                    feat_vec = continuation_hidden.mean(dim=0)

                h_feat.append(feat_vec.cpu().to(torch.float32).numpy())

            X_h = np.concatenate(h_feat).reshape(1, -1)
            X_h_scaled = halluc_scaler.transform(X_h)
            halluc_score = float(halluc_probe.predict_proba(X_h_scaled)[0, 1])
            token_entry["halluc_score"] = halluc_score
            if "score" not in token_entry:
                token_entry["score"] = halluc_score

        token_entries.append(token_entry)

        # 5. Determine next token for the next step
        next_token_logits = outputs.logits[0, -1, :]
        next_token_id = torch.argmax(next_token_logits).item()

    full_generated_text = tokenizer.decode(gen_ids, skip_special_tokens=True)

    token_counts = {
        "prompt_tokens": prompt_len,
        "generated_tokens": len(gen_ids),
        "total_tokens": prompt_len + len(gen_ids),
        "max_tokens": max_tokens,
        "generated_text": full_generated_text,
    }

    return ProbeResults(token_entries, token_counts=token_counts)


def run_interactive_session(
    model,
    tokenizer,
    mem_payload=None,
    halluc_payload=None,
    max_tokens=100,
):
    """
    Runs an interactive REPL loop evaluating both memorization and hallucination
    simultaneously on every prompt without reloading the LLM.
    """
    has_mem = mem_payload is not None
    has_halluc = halluc_payload is not None

    banner_width = 62
    print(f"\n{BOLD_CYAN}{'=' * banner_width}{RESET}")
    print(f"{BOLD_CYAN}{'LLM PROBE - INTERACTIVE DUAL-PROBE CLI':^{banner_width}}{RESET}")
    print(f"{BOLD_CYAN}{'=' * banner_width}{RESET}")
    if has_mem and has_halluc:
        print(f"  {BOLD}Active Mode{RESET}     : {BOLD_CYAN}Dual Probing (Memorization + Hallucination){RESET}")
        print(f"  {BOLD}Memorization{RESET}    : Layers {mem_payload['selected_layers']} ({mem_payload['representation_type']})")
        print(f"  {BOLD}Hallucination{RESET}   : Layers {halluc_payload['selected_layers']} ({halluc_payload['representation_type']})")
    elif has_halluc:
        print(f"  {BOLD}Active Mode{RESET}     : Hallucination Only (Layers {halluc_payload['selected_layers']})")
    else:
        print(f"  {BOLD}Active Mode{RESET}     : Memorization Only (Layers {mem_payload['selected_layers']})")

    print(f"  {BOLD}Token Limit{RESET}     : {max_tokens} tokens")
    print(f"{GRAY}{'-' * banner_width}{RESET}")
    print(f"  {BOLD}Commands{RESET}:")
    print(f"    - Enter any prompt to generate & score with both probes")
    print(f"    - {CYAN}/tokens <n>{RESET} : Adjust generated answer token limit (e.g. /tokens 50)")
    print(f"    - {CYAN}/help{RESET}       : Show commands")
    print(f"    - {CYAN}/exit{RESET}, {CYAN}quit{RESET} : Exit session")
    print(f"{BOLD_CYAN}{'=' * banner_width}{RESET}\n")

    while True:
        try:
            prompt_input = input(f"{BOLD_CYAN}Prompt >> {RESET}").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting interactive session.")
            break

        if not prompt_input:
            continue

        if prompt_input.lower() in ("/exit", "quit", "exit", "/quit"):
            print("Goodbye!")
            break

        if prompt_input.lower().startswith("/tokens "):
            parts = prompt_input.split()
            if len(parts) == 2 and parts[1].isdigit():
                max_tokens = int(parts[1])
                print(f"{YELLOW}Generated answer token limit updated to: {max_tokens}{RESET}")
            else:
                print(f"{YELLOW}Usage: /tokens <positive_integer>{RESET}")
            continue

        if prompt_input.lower() in ("/help", "help"):
            print("\nEnter prompt text to analyze, or use /tokens <n>, /exit.")
            continue

        print(f"\n{GRAY}Generating response (up to {max_tokens} tokens) with simultaneous dual-probing...{RESET}")

        results = generate_with_probe(
            prompt=prompt_input,
            model=model,
            tokenizer=tokenizer,
            probe=mem_payload["probe"] if has_mem else None,
            scaler=mem_payload["scaler"] if has_mem else None,
            selected_layers=mem_payload["selected_layers"] if has_mem else None,
            representation_type=mem_payload["representation_type"] if has_mem else None,
            max_tokens=max_tokens,
            halluc_probe=halluc_payload["probe"] if has_halluc else None,
            halluc_scaler=halluc_payload["scaler"] if has_halluc else None,
            halluc_layers=halluc_payload["selected_layers"] if has_halluc else None,
            halluc_representation_type=halluc_payload["representation_type"] if has_halluc else None,
        )

        task_mode = "both" if (has_mem and has_halluc) else ("hallucination" if has_halluc else "memorization")
        render_terminal(results, task=task_mode, token_counts=results.token_counts)


def main():
    parser = argparse.ArgumentParser(
        description="LLM Probe Live CLI Inference (Simultaneous Memorization & Hallucination Probing)"
    )
    parser.add_argument(
        "--task",
        type=str,
        choices=["both", "memorization", "hallucination"],
        default="both",
        help="Probes to run: 'both' (default, evaluates both simultaneously), 'memorization', or 'hallucination'",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default=None,
        help="Input prompt to generate from. If omitted, launches interactive REPL mode.",
    )
    parser.add_argument(
        "--max_tokens",
        type=int,
        default=100,
        help="Maximum number of tokens to generate in the answer (token limit, default: 100)",
    )
    parser.add_argument(
        "--mem_probe_path",
        type=str,
        default=MEM_PROBE_DEFAULT,
        help=f"Path to memorization probe.joblib (default: {MEM_PROBE_DEFAULT})",
    )
    parser.add_argument(
        "--halluc_probe_path",
        type=str,
        default=HALLUC_PROBE_DEFAULT,
        help=f"Path to hallucination probe.joblib (default: {HALLUC_PROBE_DEFAULT})",
    )
    parser.add_argument(
        "--probe_path",
        type=str,
        default=None,
        help="Override probe path for single-task runs (backwards compatibility)",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Force launch interactive CLI REPL session",
    )
    args = parser.parse_args()

    # Determine which payloads to load
    run_mem = args.task in ("both", "memorization")
    run_halluc = args.task in ("both", "hallucination")

    # Handle probe_path override if provided
    mem_path = args.probe_path if (args.probe_path and args.task == "memorization") else args.mem_probe_path
    halluc_path = args.probe_path if (args.probe_path and args.task == "hallucination") else args.halluc_probe_path

    mem_payload = None
    if run_mem:
        print(f"Loading Memorization probe from: {mem_path}...")
        mem_payload = load_probe_payload(mem_path)

    halluc_payload = None
    if run_halluc:
        print(f"Loading Hallucination probe from: {halluc_path}...")
        halluc_payload = load_probe_payload(halluc_path)

    # Load shared LLM
    print(f"Loading LLM model '{MODEL_NAME}' on '{DEVICE}'...")
    model = load_model(MODEL_NAME, DEVICE)
    tokenizer = load_tokenizer(MODEL_NAME)

    # Interactive mode check
    if args.interactive or args.prompt is None:
        run_interactive_session(
            model=model,
            tokenizer=tokenizer,
            mem_payload=mem_payload,
            halluc_payload=halluc_payload,
            max_tokens=args.max_tokens,
        )
    else:
        # Single prompt execution
        print(f"Prompt: {args.prompt}")
        print(f"Generating answer (token limit: {args.max_tokens})...")

        results = generate_with_probe(
            prompt=args.prompt,
            model=model,
            tokenizer=tokenizer,
            probe=mem_payload["probe"] if run_mem else None,
            scaler=mem_payload["scaler"] if run_mem else None,
            selected_layers=mem_payload["selected_layers"] if run_mem else None,
            representation_type=mem_payload["representation_type"] if run_mem else None,
            max_tokens=args.max_tokens,
            halluc_probe=halluc_payload["probe"] if run_halluc else None,
            halluc_scaler=halluc_payload["scaler"] if run_halluc else None,
            halluc_layers=halluc_payload["selected_layers"] if run_halluc else None,
            halluc_representation_type=halluc_payload["representation_type"] if run_halluc else None,
        )

        render_terminal(results, task=args.task, token_counts=results.token_counts)


if __name__ == "__main__":
    main()
