import os
import sys
import logging
import argparse
import torch
import warnings
import pandas as pd
from typing import List, Dict, Tuple, Set

# Suppress warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

# Include parent workspace folder in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from llm_probe.config import MODEL_NAME, DEVICE
from llm_probe.models.loader import load_model, load_tokenizer
from rouge_score import rouge_scorer
import datasets

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize ROUGE scorer
scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)


def load_processed_questions(parquet_path: str, csv_path: str) -> Set[str]:
    """
    Loads all question identifiers that have already been saved to the parquet or csv review files.
    """
    processed = set()
    if os.path.exists(parquet_path):
        try:
            df = pd.read_parquet(parquet_path)
            if 'question' in df.columns:
                processed.update(df['question'].dropna().tolist())
        except Exception as e:
            logger.warning(f"Could not load existing parquet: {e}")
            
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            if 'question' in df.columns:
                processed.update(df['question'].dropna().tolist())
        except Exception as e:
            logger.warning(f"Could not load existing CSV: {e}")
            
    return processed


def append_row_to_parquet(file_path: str, row_dict: Dict) -> None:
    """
    Appends a new example row to the parquet file, utilizing atomic updates.
    """
    new_df = pd.DataFrame([row_dict])
    if os.path.exists(file_path):
        try:
            existing_df = pd.read_parquet(file_path)
            df = pd.concat([existing_df, new_df], ignore_index=True)
        except Exception:
            df = new_df
    else:
        df = new_df
        
    temp_path = file_path + ".tmp"
    df.to_parquet(temp_path, index=False)
    if os.path.exists(file_path):
        os.remove(file_path)
    os.rename(temp_path, file_path)


def append_row_to_csv(file_path: str, row_dict: Dict) -> None:
    """
    Appends a new example row to the CSV file, utilizing atomic updates.
    """
    new_df = pd.DataFrame([row_dict])
    if os.path.exists(file_path):
        try:
            existing_df = pd.read_csv(file_path)
            df = pd.concat([existing_df, new_df], ignore_index=True)
        except Exception:
            df = new_df
    else:
        df = new_df
        
    temp_path = file_path + ".tmp"
    df.to_csv(temp_path, index=False)
    if os.path.exists(file_path):
        os.remove(file_path)
    os.rename(temp_path, file_path)


def main():
    parser = argparse.ArgumentParser(description="Hallucination Dataset Construction Pipeline (Probe 2)")
    parser.add_argument("--output_dir", type=str, default="data/hallucination/labeled", help="Path to save output files")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of questions to process (useful for testing)")
    parser.add_argument("--force", action="store_true", help="Force rebuild, ignoring existing processed checkpoints")
    args = parser.parse_args()
    
    logger.info("=== Starting Hallucination Dataset Construction ===")
    
    # 1. Setup Directories
    os.makedirs(args.output_dir, exist_ok=True)
    parquet_out = os.path.join(args.output_dir, "dataset.parquet")
    csv_out = os.path.join(args.output_dir, "needs_manual_review.csv")
    
    # 2. Load Source Data
    logger.info("Loading TruthfulQA dataset...")
    try:
        dataset_dict = datasets.load_dataset("truthful_qa", "generation")
    except Exception as e:
        logger.warning(f"Could not load 'truthful_qa' generation split directly: {e}. Trying fallback 'truthfulqa/truthful_qa'...")
        dataset_dict = datasets.load_dataset("truthfulqa/truthful_qa", "generation")
        
    validation_data = dataset_dict["validation"]
    total_questions = len(validation_data)
    logger.info(f"Loaded {total_questions} questions from TruthfulQA.")
    
    # Print sample items for sanity-checking
    logger.info("Sanity check - Sample items:")
    for i in range(min(2, total_questions)):
        item = validation_data[i]
        logger.info(f"Sample {i+1}:")
        logger.info(f"  Question: {item['question']}")
        logger.info(f"  Best Answer: {item['best_answer']}")
        logger.info(f"  Correct Answers: {item['correct_answers']}")
        logger.info(f"  Incorrect Answers: {item['incorrect_answers']}")
        logger.info(f"  Category: {item['category']}")
        logger.info("-" * 40)
        
    # Check existing checkpoints unless force flag is active
    if args.force:
        processed_questions = set()
        logger.info("Force flag active. Re-processing all examples.")
        if os.path.exists(parquet_out):
            os.remove(parquet_out)
        if os.path.exists(csv_out):
            os.remove(csv_out)
    else:
        processed_questions = load_processed_questions(parquet_out, csv_out)
        logger.info(f"Loaded {len(processed_questions)} already processed questions from checkpoints.")
        
    # 3. Load Model and Tokenizer
    logger.info(f"Loading model '{MODEL_NAME}' on '{DEVICE}'...")
    tokenizer = load_tokenizer(MODEL_NAME)
    model = load_model(MODEL_NAME, DEVICE)
    device = next(model.parameters()).device
    
    # Filter dataset items to process
    items_to_process = []
    for item in validation_data:
        q = item["question"]
        if q in processed_questions:
            continue
        items_to_process.append(item)
        
    if args.limit is not None:
        logger.info(f"Limiting execution to the first {args.limit} unprocessed items for testing.")
        items_to_process = items_to_process[:args.limit]
        
    if not items_to_process:
        logger.info("No new items to process. Dataset construction is complete or fully cached.")
        # Print summary of what currently exists
        print_summary(parquet_out, csv_out)
        return
        
    logger.info(f"Queue size: {len(items_to_process)} questions to generate answers and label.")
    
    # 4. Run Generation & Labeling Loop
    for idx, item in enumerate(items_to_process):
        question = item["question"]
        best_answer = item["best_answer"]
        correct_answers = item["correct_answers"]
        incorrect_answers = item["incorrect_answers"]
        category = item["category"]
        
        logger.info(f"[{idx+1}/{len(items_to_process)}] Processing question: {question}")
        
        # Generation: deterministic, max_new_tokens=100, no special chat templates beyond direct tokenization
        try:
            inputs = tokenizer(question, return_tensors="pt").to(device)
            prompt_len = inputs["input_ids"].shape[1]
            
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=100,
                    do_sample=False,
                    pad_token_id=tokenizer.eos_token_id
                )
                
            gen_tokens = outputs[0][prompt_len:]
            generated_answer = tokenizer.decode(gen_tokens, skip_special_tokens=True).strip()
            
            logger.info(f"Generated answer: {generated_answer}")
            
            # Compute ROUGE-L similarity scores (using recall to avoid precision penalty on verbose generated answers)
            correct_sims = [scorer.score(ans, generated_answer)['rougeL'].recall for ans in correct_answers]
            correct_sim_score = max(correct_sims) if correct_sims else 0.0
            
            incorrect_sims = [scorer.score(ans, generated_answer)['rougeL'].recall for ans in incorrect_answers]
            incorrect_sim_score = max(incorrect_sims) if incorrect_sims else 0.0
            
            # Labeling Logic
            is_ambiguous = False
            flag_reason = ""
            label_reason = ""
            label = ""
            
            # Check for ambiguity: scores are close and both above floor
            if correct_sim_score >= 0.3 and incorrect_sim_score >= 0.3 and abs(correct_sim_score - incorrect_sim_score) <= 0.1:
                is_ambiguous = True
                flag_reason = f"Ambiguous: scores close (correct: {correct_sim_score:.3f}, incorrect: {incorrect_sim_score:.3f})"
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
                # Weak scores or unclassified margin (e.g. correct_sim=0.4, incorrect_sim=0.2)
                is_ambiguous = True
                flag_reason = f"Weak match: correct {correct_sim_score:.3f}, incorrect {incorrect_sim_score:.3f}"
                
            row = {
                "question": question,
                "generated_answer": generated_answer,
                "best_answer": best_answer,
                "category": category,
                "correct_sim_score": correct_sim_score,
                "incorrect_sim_score": incorrect_sim_score
            }
            
            if is_ambiguous:
                row["label"] = "ambiguous"
                row["flag_reason"] = flag_reason
                append_row_to_csv(csv_out, row)
                logger.info(f"-> Flagged for manual review. Reason: {flag_reason}")
            else:
                row["label"] = label
                row["label_reason"] = label_reason
                append_row_to_parquet(parquet_out, row)
                logger.info(f"-> Auto-labeled as '{label}'. Reason: {label_reason} (correct_sim={correct_sim_score:.3f}, incorrect_sim={incorrect_sim_score:.3f})")
                
        except Exception as ex:
            logger.error(f"Failed to process example: '{question}'. Error: {ex}")
            
    # Print final summary
    print_summary(parquet_out, csv_out)


def print_summary(parquet_path: str, csv_path: str):
    """
    Reads files and prints stats.
    """
    logger.info("=== Construction Summary ===")
    
    total_labeled = 0
    label_counts = {}
    cat_counts = {}
    
    if os.path.exists(parquet_path):
        try:
            df = pd.read_parquet(parquet_path)
            total_labeled = len(df)
            for l in df['label'].tolist():
                label_counts[l] = label_counts.get(l, 0) + 1
            for c in df['category'].tolist():
                cat_counts[c] = cat_counts.get(c, 0) + 1
        except Exception as e:
            logger.error(f"Error summarising parquet: {e}")
            
    total_ambiguous = 0
    if os.path.exists(csv_path):
        try:
            df_csv = pd.read_csv(csv_path)
            total_ambiguous = len(df_csv)
            for c in df_csv['category'].tolist():
                cat_counts[c] = cat_counts.get(c, 0) + 1
        except Exception as e:
            logger.error(f"Error summarising CSV: {e}")
            
    logger.info(f"Total processed: {total_labeled + total_ambiguous}")
    logger.info(f"  - Auto-labeled (parquet): {total_labeled}")
    for lbl, cnt in label_counts.items():
        logger.info(f"    * {lbl}: {cnt}")
    logger.info(f"  - Flagged for review (csv): {total_ambiguous}")
    
    logger.info("Category breakdown (combined):")
    for cat, cnt in sorted(cat_counts.items(), key=lambda x: x[1], reverse=True):
        logger.info(f"  - {cat}: {cnt}")


if __name__ == "__main__":
    main()
