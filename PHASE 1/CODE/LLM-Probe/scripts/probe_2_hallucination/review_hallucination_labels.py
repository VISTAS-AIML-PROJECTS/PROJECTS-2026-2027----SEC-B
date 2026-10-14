import os
import sys
import re
import logging
import argparse
import pandas as pd
import numpy as np
import datasets
from typing import List, Dict, Tuple, Set
from rouge_score import rouge_scorer

# Include parent workspace folder in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from llm_probe.config import MODEL_NAME, DEVICE

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize ROUGE scorer
scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)


def get_words(text: str) -> List[str]:
    """
    Extracts lowercase alphanumeric word tokens from a string.
    """
    if not isinstance(text, str):
        return []
    return re.findall(r'\b\w+\b', text.lower())


def strip_question_boilerplate(text: str, question: str) -> str:
    """
    Strips matching words from the start of the text that appear in the question.
    Stops at the first word that does not appear in the question.
    """
    if not isinstance(text, str) or not isinstance(question, str):
        return ""
    
    q_words = set(get_words(question))
    word_spans = [(m.start(), m.end(), m.group().lower()) for m in re.finditer(r'\b\w+\b', text)]
    
    strip_end_idx = 0
    for start, end, word in word_spans:
        if word in q_words:
            strip_end_idx = end
        else:
            break
            
    return text[strip_end_idx:].strip()


def clean_and_strip(text: str, question: str) -> str:
    """
    Strips boilerplate, but falls back to the original text if nothing is left.
    """
    stripped = strip_question_boilerplate(text, question)
    if len(get_words(stripped)) == 0:
        return text
    return stripped


def get_differentiating_words(incorrect_answers: List[str], correct_answers: List[str]) -> Set[str]:
    """
    Collects lowercase words that appear in the incorrect answers but not in any correct answers.
    """
    correct_words = set()
    for ans in correct_answers:
        correct_words.update(get_words(ans))
        
    diff_words = set()
    for ans in incorrect_answers:
        for w in get_words(ans):
            if w not in correct_words:
                diff_words.add(w)
    return diff_words


def main():
    parser = argparse.ArgumentParser(description="Post-processing Cleanup for Hallucination Dataset (Probe 2)")
    parser.add_argument("--data_dir", type=str, default="data/hallucination/labeled", help="Directory where dataset files reside")
    args = parser.parse_args()
    
    logger.info("=== Starting Hallucination Label Cleanup Script ===")
    
    parquet_path = os.path.join(args.data_dir, "dataset.parquet")
    csv_path = os.path.join(args.data_dir, "needs_manual_review.csv")
    
    reconsidered_path = os.path.join(args.data_dir, "reconsidered.csv")
    newly_resolved_path = os.path.join(args.data_dir, "newly_resolved.csv")
    spotcheck_path = os.path.join(args.data_dir, "cleanup_spotcheck_30.md")
    
    if not os.path.exists(parquet_path):
        logger.error(f"dataset.parquet not found at {parquet_path}. Run dataset generation first.")
        sys.exit(1)
    if not os.path.exists(csv_path):
        logger.error(f"needs_manual_review.csv not found at {csv_path}. Run dataset generation first.")
        sys.exit(1)
        
    # 1. Load source TruthfulQA dataset for reference answers
    logger.info("Loading TruthfulQA dataset for correct/incorrect reference lists...")
    try:
        dataset_dict = datasets.load_dataset("truthful_qa", "generation")
    except Exception as e:
        logger.warning(f"Could not load 'truthful_qa' generation split directly: {e}. Trying fallback 'truthfulqa/truthful_qa'...")
        dataset_dict = datasets.load_dataset("truthfulqa/truthful_qa", "generation")
        
    validation_data = dataset_dict["validation"]
    
    ref_map = {}
    for item in validation_data:
        ref_map[item["question"]] = {
            "correct_answers": item["correct_answers"],
            "incorrect_answers": item["incorrect_answers"],
            "best_answer": item["best_answer"]
        }
        
    # Load existing labels
    df_parquet = pd.read_parquet(parquet_path)
    df_csv = pd.read_csv(csv_path)
    
    logger.info(f"Loaded {len(df_parquet)} auto-labeled examples and {len(df_csv)} ambiguous examples.")
    
    # 2. Apply Entity-based Guard to currently hallucinated labels in dataset.parquet
    logger.info("Applying Entity-Based Guard to currently hallucinated labels...")
    df_hallucinated = df_parquet[df_parquet["label"] == "hallucinated"].copy()
    
    reconsidered_rows = []
    
    for idx, row in df_hallucinated.iterrows():
        question = row["question"]
        gen_answer = row["generated_answer"]
        
        ref = ref_map.get(question)
        if not ref:
            continue
            
        correct_ans = ref["correct_answers"]
        incorrect_ans = ref["incorrect_answers"]
        
        diff_words = get_differentiating_words(incorrect_ans, correct_ans)
        gen_words = set(get_words(gen_answer))
        
        # Check if key differentiating entity words appear in the generated answer
        has_key_entity = any(w in gen_words for w in diff_words)
        
        if not has_key_entity:
            # Differentiating entities are missing from generated answer: flag as suspect
            reconsidered_row = row.to_dict()
            reconsidered_row["flag_reason"] = f"Entity Guard: Differentiating entities {list(diff_words)[:5]} missing from generated answer."
            reconsidered_rows.append(reconsidered_row)
            
    df_reconsidered = pd.DataFrame(reconsidered_rows)
    df_reconsidered.to_csv(reconsidered_path, index=False)
    logger.info(f"Flagged {len(df_reconsidered)} currently hallucinated rows as suspect. Saved to {reconsidered_path}.")
    
    # 3. Re-score the Ambiguous Set (needs_manual_review.csv)
    logger.info("Re-scoring needs_manual_review.csv using boilerplate stripping...")
    newly_resolved_rows = []
    
    for idx, row in df_csv.iterrows():
        question = row["question"]
        gen_answer = row["generated_answer"]
        
        ref = ref_map.get(question)
        if not ref:
            continue
            
        correct_ans = ref["correct_answers"]
        incorrect_ans = ref["incorrect_answers"]
        category = row["category"]
        best_answer = row["best_answer"]
        
        # Strip boilerplate from the generated answer and references
        stripped_gen = clean_and_strip(gen_answer, question)
        
        stripped_correct = [clean_and_strip(ans, question) for ans in correct_ans]
        stripped_incorrect = [clean_and_strip(ans, question) for ans in incorrect_ans]
        
        # Compute stripped scores
        correct_sims = [scorer.score(ans, stripped_gen)['rougeL'].recall for ans in stripped_correct]
        correct_sim_score = max(correct_sims) if correct_sims else 0.0
        
        incorrect_sims = [scorer.score(ans, stripped_gen)['rougeL'].recall for ans in stripped_incorrect]
        incorrect_sim_score = max(incorrect_sims) if incorrect_sims else 0.0
        
        # Check if the margin widens past 0.1 and check confidence
        is_ambiguous = False
        label = ""
        label_reason = ""
        
        if correct_sim_score >= 0.3 and incorrect_sim_score >= 0.3 and abs(correct_sim_score - incorrect_sim_score) <= 0.1:
            is_ambiguous = True
        elif correct_sim_score < 0.3 and incorrect_sim_score < 0.3:
            label = "hallucinated"
            label_reason = "low_similarity_floor"
        elif (correct_sim_score > incorrect_sim_score) and (correct_sim_score > 0.5):
            label = "grounded"
            label_reason = "correct_sim_high"
        elif (incorrect_sim_score > correct_sim_score) and (incorrect_sim_score > 0.5):
            label = "hallucinated"
            label_reason = "incorrect_sim_high"
        else:
            is_ambiguous = True
            
        if not is_ambiguous:
            # Successfully resolved!
            resolved_row = {
                "question": question,
                "generated_answer": gen_answer,
                "best_answer": best_answer,
                "category": category,
                "correct_sim_score": correct_sim_score,
                "incorrect_sim_score": incorrect_sim_score,
                "label": label,
                "label_reason": label_reason,
                "old_label": "ambiguous"
            }
            newly_resolved_rows.append(resolved_row)
            
    df_newly_resolved = pd.DataFrame(newly_resolved_rows)
    df_newly_resolved.to_csv(newly_resolved_path, index=False)
    
    # 4. Print Counts
    new_grounded = len(df_newly_resolved[df_newly_resolved["label"] == "grounded"]) if len(df_newly_resolved) > 0 else 0
    new_hallucinated = len(df_newly_resolved[df_newly_resolved["label"] == "hallucinated"]) if len(df_newly_resolved) > 0 else 0
    
    logger.info("=== Diagnostic Counts ===")
    logger.info(f"Hallucinated rows flagged as suspect (reconsidered.csv): {len(df_reconsidered)}")
    logger.info(f"Ambiguous rows newly resolved (newly_resolved.csv): {len(df_newly_resolved)}")
    logger.info(f"  * Grounded: {new_grounded}")
    logger.info(f"  * Hallucinated: {new_hallucinated}")
    
    # 5. Mandatory Spot-check Sample MD Output
    logger.info("Generating spot-check markdown file...")
    
    spotcheck_lines = [
        "# Hallucination Cleanup Spot-check Report\n",
        "This file contains a sample of 30 parsed rows staged for manual verification. ",
        "Do not merge these back into `dataset.parquet` until this spot-check has been approved.\n",
        "## Summary of Changes",
        f"- Suspect Hallucinated Rows Flagged: **{len(df_reconsidered)}**",
        f"- Ambiguous Rows Newly Resolved: **{len(df_newly_resolved)}** (Grounded: {new_grounded}, Hallucinated: {new_hallucinated})\n",
        "---"
    ]
    
    np.random.seed(42)  # For reproducible samples
    
    # Sample 15 from reconsidered
    spotcheck_lines.append("## Staged from reconsidered.csv (Suspect Hallucinations - 15 Samples)\n")
    if len(df_reconsidered) > 0:
        sample_rec = df_reconsidered.sample(min(15, len(df_reconsidered)))
        for i, (_, row) in enumerate(sample_rec.iterrows()):
            question = row["question"]
            ref = ref_map.get(question, {})
            spotcheck_lines.append(f"### {i+1}. Q: {question}")
            spotcheck_lines.append(f"**Category**: {row['category']} | **Correct Sim**: {row['correct_sim_score']:.3f} | **Incorrect Sim**: {row['incorrect_sim_score']:.3f}")
            spotcheck_lines.append(f"**Best Answer Reference**: {row['best_answer']}")
            spotcheck_lines.append(f"**Incorrect Answers**: `{ref.get('incorrect_answers', [])}`")
            spotcheck_lines.append(f"**Reason for Flag**: {row['flag_reason']}")
            spotcheck_lines.append("**Generated Answer**:")
            spotcheck_lines.append(f"```\n{row['generated_answer']}\n```")
            spotcheck_lines.append("\n---\n")
    else:
        spotcheck_lines.append("*No reconsidered samples flagged.*\n")
        
    # Sample 15 from newly resolved (proportional)
    spotcheck_lines.append("## Staged from newly_resolved.csv (Newly Resolved - 15 Samples)\n")
    if len(df_newly_resolved) > 0:
        # Sample proportionally from grounded vs hallucinated
        resolved_gr = df_newly_resolved[df_newly_resolved["label"] == "grounded"]
        resolved_hl = df_newly_resolved[df_newly_resolved["label"] == "hallucinated"]
        
        n_gr = min(len(resolved_gr), 15 * len(resolved_gr) // len(df_newly_resolved)) if len(df_newly_resolved) > 0 else 0
        n_hl = min(len(resolved_hl), 15 - n_gr)
        
        gr_sample = resolved_gr.sample(n_gr) if n_gr > 0 else pd.DataFrame()
        hl_sample = resolved_hl.sample(n_hl) if n_hl > 0 else pd.DataFrame()
        
        resolved_sample = pd.concat([gr_sample, hl_sample]).sample(frac=1.0) # shuffle
        
        for i, (_, row) in enumerate(resolved_sample.iterrows()):
            question = row["question"]
            ref = ref_map.get(question, {})
            spotcheck_lines.append(f"### {i+1}. Q: {question}")
            spotcheck_lines.append(f"**Category**: {row['category']} | **Correct Sim**: {row['correct_sim_score']:.3f} | **Incorrect Sim**: {row['incorrect_sim_score']:.3f}")
            spotcheck_lines.append(f"**Best Answer Reference**: {row['best_answer']}")
            spotcheck_lines.append(f"**Correct Answers**: `{ref.get('correct_answers', [])}`")
            spotcheck_lines.append(f"**Incorrect Answers**: `{ref.get('incorrect_answers', [])}`")
            spotcheck_lines.append(f"**Original Label**: {row['old_label']} -> **New Label**: {row['label']} ({row['label_reason']})")
            spotcheck_lines.append("**Generated Answer**:")
            spotcheck_lines.append(f"```\n{row['generated_answer']}\n```")
            spotcheck_lines.append("\n---\n")
    else:
        spotcheck_lines.append("*No newly resolved samples.*\n")
        
    with open(spotcheck_path, "w", encoding="utf-8") as f:
        f.write("\n".join(spotcheck_lines))
        
    logger.info(f"Staged spotcheck report written to {spotcheck_path}.")


if __name__ == "__main__":
    main()
