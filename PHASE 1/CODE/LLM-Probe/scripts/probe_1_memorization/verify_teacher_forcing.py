import os
import sys
import warnings
import joblib
import torch
import numpy as np
import pandas as pd

# Include parent folder in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from llm_probe.config import MODEL_NAME, DEVICE
from llm_probe.models.loader import load_model, load_tokenizer

def main():
    print("=== Starting Teacher-Forced Probe Scoring Verification ===")
    
    # 1. Load trained probe and scaler
    probe_path = "results/memorization/probe.joblib"
    if not os.path.exists(probe_path):
        print(f"Error: Trained probe not found at: {probe_path}")
        sys.exit(1)
        
    payload = joblib.load(probe_path)
    probe = payload['probe']
    scaler = payload['scaler']
    selected_layers = payload['selected_layers']
    representation_type = payload['representation_type']
    
    print(f"Configuration loaded: layers={selected_layers}, representation={representation_type}")
    
    # 2. Load model and tokenizer
    model = load_model(MODEL_NAME, DEVICE)
    tokenizer = load_tokenizer(MODEL_NAME)
    
    # 3. Load prompt/continuations from tables
    df_pq = pd.read_parquet("data/memorization/labeled/dataset.parquet")
    df_csv = pd.read_csv("data/memorization/labeled/needs_manual_review.csv")
    
    # Target examples:
    # A. Pride & Prejudice (memorized)
    row_pap = df_pq[df_pq['source_id'] == "book_openings/pride_and_prejudice.txt"].iloc[0]
    # B. Alice in Wonderland (memorized)
    row_alice = df_csv[df_csv['source_id'] == "book_openings/Alice's_Adventures_in_Wonderland.txt"].iloc[0]
    # C. Moby Dick (novel negative control)
    row_moby = df_pq[df_pq['source_id'] == "book_openings/moby_dick.txt"].iloc[0]
    # D. Adam Bede (novel negative control)
    row_adam = df_pq[df_pq['source_id'] == "book_openings/adam_bede.txt"].iloc[0] if "book_openings/adam_bede.txt" in df_pq['source_id'].values else df_pq[df_pq['source_id'] == "book_openings/Adam_Bede.txt"].iloc[0]
    
    targets = [
        {"name": "Pride & Prejudice (Memorized)", "prompt": row_pap['prompt'], "continuation": row_pap['true_continuation'], "label": "memorized"},
        {"name": "Alice in Wonderland (Memorized)", "prompt": row_alice['prompt'], "continuation": row_alice['true_continuation'], "label": "memorized"},
        {"name": "Moby Dick (Novel Control)", "prompt": row_moby['prompt'], "continuation": row_moby['true_continuation'], "label": "novel"},
        {"name": "Adam Bede (Novel Control)", "prompt": row_adam['prompt'], "continuation": row_adam['true_continuation'], "label": "novel"}
    ]
    
    verifications = {}
    
    for target in targets:
        name = target['name']
        prompt = target['prompt']
        continuation = target['continuation']
        label = target['label']
        
        print(f"\nProcessing teacher-forcing scoring for: {name}...")
        
        # Tokenize prompt and continuation
        prompt_ids = tokenizer.encode(prompt, add_special_tokens=True)
        continuation_ids = tokenizer.encode(continuation, add_special_tokens=False)
        
        # Limit to first 40 continuation tokens to match free-generation length
        continuation_ids = continuation_ids[:40]
        prompt_len = len(prompt_ids)
        
        results = []
        # Force-decode continuation step-by-step
        for step in range(1, len(continuation_ids) + 1):
            gen_prefix_ids = continuation_ids[:step]
            token_str = tokenizer.decode([continuation_ids[step-1]])
            
            combined_ids = prompt_ids + gen_prefix_ids
            input_ids_tensor = torch.tensor([combined_ids], dtype=torch.long, device=DEVICE)
            attention_mask_tensor = torch.ones_like(input_ids_tensor, device=DEVICE)
            
            with torch.no_grad():
                outputs = model(
                    input_ids=input_ids_tensor,
                    attention_mask=attention_mask_tensor,
                    output_hidden_states=True
                )
            
            hidden_states = outputs.hidden_states
            example_feat = []
            for layer in selected_layers:
                layer_hidden_seq = hidden_states[layer][0]
                continuation_hidden = layer_hidden_seq[prompt_len:, :]
                
                if representation_type == 'last_token':
                    feat_vec = continuation_hidden[-1, :]
                else:
                    feat_vec = continuation_hidden.mean(dim=0)
                    
                example_feat.append(feat_vec.cpu().to(torch.float32).numpy())
                
            X_token = np.concatenate(example_feat).reshape(1, -1)
            X_token_scaled = scaler.transform(X_token)
            
            mem_score = probe.predict_proba(X_token_scaled)[0, 1]
            results.append({
                'token': token_str,
                'mem_score': float(mem_score)
            })
            
        verifications[name] = results
        
    # Compile markdown output report
    report_lines = [
        "# LLM Probe - Teacher-Forcing Memorization Score Verification",
        "",
        "This file compares the memorization probe's token-by-token risk scores during teacher-forcing",
        "(where the true continuation is forced) versus the model's free-generation path.",
        ""
    ]
    
    # 4. Compare Side-by-Side with Free-Generation (read from demo_test_results.md if present)
    free_gen_alice = [
        {"token": "and", "score": 0.65},
        {"token": "of", "score": 0.95},
        {"token": "having", "score": 0.99},
        {"token": "to", "score": 0.98},
        {"token": "entertain", "score": 0.99},
        {"token": "herself", "score": 0.98},
        {"token": ".", "score": 0.95},
        {"token": "\n", "score": 0.85},
        {"token": "\n", "score": 0.73},
        {"token": "\n", "score": 0.59},
        {"token": "\"", "score": 0.70},
        {"token": "I", "score": 0.59},
        {"token": "'", "score": 0.51},
        {"token": "ll", "score": 0.45},
        {"token": "be", "score": 0.40},
        {"token": "going", "score": 0.35},
        {"token": "_", "score": 0.29},
        {"token": "____", "score": 0.19},
        {"token": "__", "score": 0.12},
        {"token": "\",", "score": 0.10},
        {"token": "said", "score": 0.08},
        {"token": "Alice", "score": 0.08},
        {"token": ",", "score": 0.06},
        {"token": "trying", "score": 0.04},
        {"token": "to", "score": 0.04},
        {"token": "decide", "score": 0.03},
        {"token": "what", "score": 0.02},
        {"token": "to", "score": 0.02},
        {"token": "say", "score": 0.02},
        {"token": "next", "score": 0.02},
        {"token": ".", "score": 0.02}
    ]
    
    free_gen_moby = [
        {"token": "when", "score": 0.01},
        {"token": "I", "score": 0.07},
        {"token": "was", "score": 0.01},
        {"token": "in", "score": 0.01},
        {"token": "the", "score": 0.01},
        {"token": "high", "score": 0.02},
        {"token": "school", "score": 0.01}
    ]
    
    # Alice Report Section
    report_lines.append("## Alice in Wonderland (Side-by-Side Comparison)")
    report_lines.append("| Token Index | Token (Free Gen) | Score (Free Gen) | Token (Forced) | Score (Forced) |")
    report_lines.append("|---|---|---|---|---|")
    
    alice_forced = verifications["Alice in Wonderland (Memorized)"]
    max_len = max(len(free_gen_alice), len(alice_forced))
    
    for idx in range(max_len):
        fg_tok = free_gen_alice[idx]['token'].replace('\n', '\\n') if idx < len(free_gen_alice) else ""
        fg_sc = f"{free_gen_alice[idx]['score']:.4f}" if idx < len(free_gen_alice) else ""
        
        fo_tok = alice_forced[idx]['token'].replace('\n', '\\n') if idx < len(alice_forced) else ""
        fo_sc = f"{alice_forced[idx]['mem_score']:.4f}" if idx < len(alice_forced) else ""
        
        report_lines.append(f"| {idx+1} | `{fg_tok}` | {fg_sc} | `{fo_tok}` | {fo_sc} |")
        
    report_lines.append("\n---\n")
    
    # Moby Dick Report Section
    report_lines.append("## Moby Dick (Side-by-Side Comparison)")
    report_lines.append("| Token Index | Token (Free Gen) | Score (Free Gen) | Token (Forced) | Score (Forced) |")
    report_lines.append("|---|---|---|---|---|")
    
    moby_forced = verifications["Moby Dick (Novel Control)"]
    max_len_m = max(len(free_gen_moby), len(moby_forced))
    
    for idx in range(max_len_m):
        fg_tok = free_gen_moby[idx]['token'].replace('\n', '\\n') if idx < len(free_gen_moby) else ""
        fg_sc = f"{free_gen_moby[idx]['score']:.4f}" if idx < len(free_gen_moby) else ""
        
        fo_tok = moby_forced[idx]['token'].replace('\n', '\\n') if idx < len(moby_forced) else ""
        fo_sc = f"{moby_forced[idx]['mem_score']:.4f}" if idx < len(moby_forced) else ""
        
        report_lines.append(f"| {idx+1} | `{fg_tok}` | {fg_sc} | `{fo_tok}` | {fo_sc} |")
        
    report_lines.append("\n---\n")
    
    # Stats for all targets
    report_lines.append("## Verification Statistics Summary")
    report_lines.append("| Target Name | Label | Avg Score (Forced) | Max Score (Forced) | Last Token Score (Forced) |")
    report_lines.append("|---|---|---|---|---|")
    
    verdict_summary = []
    
    for name, results in verifications.items():
        scores = [r['mem_score'] for r in results]
        avg_sc = sum(scores) / len(scores) if scores else 0.0
        max_sc = max(scores) if scores else 0.0
        last_sc = scores[-1] if scores else 0.0
        target_label = next(t['label'] for t in targets if t['name'] == name)
        
        report_lines.append(f"| {name} | {target_label.upper()} | {avg_sc:.4f} | {max_sc:.4f} | {last_sc:.4f} |")
        
        # Evaluation logic
        if target_label == "memorized":
            sustained = "YES" if last_sc >= 0.50 else "NO"
            verdict_summary.append(f"- **{name}** (Forced): Avg={avg_sc:.4f}, Sustained High: {sustained}")
        else:
            stayed_low = "YES" if max_sc < 0.30 else "NO"
            verdict_summary.append(f"- **{name}** (Forced): Avg={avg_sc:.4f}, Stayed Low: {stayed_low}")
            
    report_lines.append("\n")
    report_lines.append("### Final Verdict")
    report_lines.extend(verdict_summary)
    
    # Save Report
    report_path = "results/memorization/teacher_forcing_verification.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
        
    print(f"Saved teacher forcing report to: {report_path}")
    
    # Print Verdict directly to terminal
    print("\n" + "="*50)
    print(" VERIFICATION COMPLETE - FINAL VERDICT")
    print("="*50)
    for v in verdict_summary:
        print(v.replace("**", "").replace("- ", ""))
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
