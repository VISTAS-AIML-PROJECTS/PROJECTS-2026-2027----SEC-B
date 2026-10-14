import os
import sys
import logging
import argparse
import torch
import warnings
import pandas as pd
from typing import List, Dict, Tuple, Set

# Suppress FutureWarnings from pandas
warnings.simplefilter(action='ignore', category=FutureWarning)

# Include parent workspace folder in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from llm_probe.config import MODEL_NAME, DEVICE
from llm_probe.models.loader import load_model, load_tokenizer
from rouge_score import rouge_scorer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
PROMPT_TOKEN_LEN = 40
MAX_TOTAL_TOKENS = 100
SIMIDUP_THRESHOLD = 0.95
MIN_PREFIX_MATCH_TOKENS = 10
BATCH_SIZE = 16

# Initialize ROUGE scorer
scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)


def longest_common_ngram_len(text1: str, text2: str) -> int:
    """
    Computes the word-level longest common contiguous sequence of words (n-gram).
    """
    words1 = text1.split()
    words2 = text2.split()
    if not words1 or not words2:
        return 0
    m, n = len(words1), len(words2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    longest = 0
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if words1[i - 1].lower() == words2[j - 1].lower():
                dp[i][j] = dp[i - 1][j - 1] + 1
                longest = max(longest, dp[i][j])
            else:
                dp[i][j] = 0
    return longest


def get_matched_token_count(gen_text: str, true_text: str, tokenizer) -> int:
    """
    Computes the length of the matching prefix of token IDs between generated and true text.
    """
    if not true_text:
        return 0
    gen_ids = tokenizer.encode(gen_text.strip(), add_special_tokens=False)
    true_ids = tokenizer.encode(true_text.strip(), add_special_tokens=False)
    count = 0
    for g, t in zip(gen_ids, true_ids):
        if g == t:
            count += 1
        else:
            break
    return count


def cap_example_tokens(
    prompt_text: str, 
    continuation_text: str, 
    true_continuation_text: str, 
    tokenizer
) -> Tuple[str, str, str]:
    """
    Truncates prompt and continuation texts so that their combined token length is <= 100.
    Preserves the prompt length as much as possible.
    """
    p_ids = tokenizer.encode(prompt_text, add_special_tokens=False)
    p_len = len(p_ids)
    
    if p_len >= MAX_TOTAL_TOKENS:
        # In the extreme case prompt is too long, cap prompt at 50 to leave room for generation
        p_ids = p_ids[:50]
        p_len = 50
        prompt_text = tokenizer.decode(p_ids, skip_special_tokens=True)
        
    max_c_len = MAX_TOTAL_TOKENS - p_len
    
    c_ids = tokenizer.encode(continuation_text, add_special_tokens=False)
    if len(c_ids) > max_c_len:
        c_ids = c_ids[:max_c_len]
        continuation_text = tokenizer.decode(c_ids, skip_special_tokens=True)
        
    if true_continuation_text:
        t_ids = tokenizer.encode(true_continuation_text, add_special_tokens=False)
        if len(t_ids) > max_c_len:
            t_ids = t_ids[:max_c_len]
            true_continuation_text = tokenizer.decode(t_ids, skip_special_tokens=True)
            
    return prompt_text, continuation_text, true_continuation_text


def is_duplicate_tfidf(candidate_text: str, existing_texts: List[str], threshold: float = SIMIDUP_THRESHOLD) -> bool:
    """
    Checks if candidate_text has cosine similarity > threshold with any text in existing_texts.
    """
    if not existing_texts:
        return False
    if candidate_text in existing_texts:
        return True
    try:
        vectorizer = TfidfVectorizer()
        all_texts = existing_texts + [candidate_text]
        tfidf_matrix = vectorizer.fit_transform(all_texts)
        sims = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])
        if (sims > threshold).any():
            return True
    except Exception:
        # Fallback to exact match if TF-IDF fails
        pass
    return False


def load_processed_ids(parquet_path: str, csv_path: str) -> Set[str]:
    """
    Loads all source_id identifiers that have already been saved to the parquet or csv review files.
    """
    processed = set()
    if os.path.exists(parquet_path):
        try:
            df = pd.read_parquet(parquet_path)
            if 'source_id' in df.columns:
                processed.update(df['source_id'].dropna().tolist())
        except Exception as e:
            logger.warning(f"Could not load existing parquet: {e}")
            
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            if 'source_id' in df.columns:
                processed.update(df['source_id'].dropna().tolist())
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
    parser = argparse.ArgumentParser(description="Memorization Dataset Construction Pipeline")
    parser.add_argument("--raw_dir", type=str, default="data/memorization/raw", help="Path to raw texts subfolders")
    parser.add_argument("--output_dir", type=str, default="data/memorization/labeled", help="Path to save output files")
    args = parser.parse_args()
    
    logger.info("=== Starting Memorization Dataset Construction ===")
    
    # 1. Setup Directories
    os.makedirs(args.output_dir, exist_ok=True)
    parquet_out = os.path.join(args.output_dir, "dataset.parquet")
    csv_out = os.path.join(args.output_dir, "needs_manual_review.csv")
    
    # 2. Check Existing Outputs for Resumability
    processed_ids = load_processed_ids(parquet_out, csv_out)
    logger.info(f"Loaded {len(processed_ids)} already processed source texts.")
    
    # 3. Load Model and Tokenizer
    logger.info(f"Loading model '{MODEL_NAME}' on '{DEVICE}'...")
    tokenizer = load_tokenizer(MODEL_NAME)
    model = load_model(MODEL_NAME, DEVICE)
    
    # 4. Find All Source Files
    categories = ["book_openings", "lyrics", "code_snippets", "wiki_leads", "novel_prompts"]
    source_files: List[Tuple[str, str, str]] = []  # (category, item_id, content)
    import json
    
    for cat in categories:
        jsonl_path = os.path.join(args.raw_dir, f"{cat}.jsonl")
        if not os.path.exists(jsonl_path):
            logger.warning(f"Category JSONL file not found: {jsonl_path}")
            continue
            
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                    item_id = item.get("id")
                    content = item.get("content", "").strip()
                    if item_id and content:
                        source_files.append((cat, item_id, content))
                except Exception as e:
                    logger.error(f"Error parsing line in {jsonl_path}: {e}")
                    
    logger.info(f"Found {len(source_files)} total raw examples.")
    
    # 5. Load Combined Text for TF-IDF Deduplication Cache
    existing_combined_texts: List[str] = []
    if os.path.exists(parquet_out):
        try:
            df = pd.read_parquet(parquet_out)
            existing_combined_texts.extend((df['prompt'] + " " + df['generated_continuation']).tolist())
        except Exception:
            pass
    if os.path.exists(csv_out):
        try:
            df = pd.read_csv(csv_out)
            existing_combined_texts.extend((df['prompt'] + " " + df['generated_continuation']).tolist())
        except Exception:
            pass
            
    # Separate novel prompts (processed individually) and regular files
    novel_files = []
    regular_files = []
    
    for cat, item_id, content in source_files:
        source_id = f"{cat}/{item_id}.txt"
        if source_id in processed_ids:
            logger.info(f"Skipping already processed file: {source_id}")
            continue
        if cat == "novel_prompts":
            novel_files.append((cat, item_id, content))
        else:
            regular_files.append((cat, item_id, content))

    logger.info(f"Queue: {len(novel_files)} novel files, {len(regular_files)} regular files to process.")

    # 1. Process regular files in batches
    tokenizer.padding_side = "left"
    for start_idx in range(0, len(regular_files), BATCH_SIZE):
        batch = regular_files[start_idx : start_idx + BATCH_SIZE]
        logger.info(f"Processing batch of {len(batch)} regular files ({start_idx+1}-{start_idx+len(batch)} of {len(regular_files)}) ...")
        
        valid_items = []
        for cat, item_id, content in batch:
            source_id = f"{cat}/{item_id}.txt"
            try:
                if not content:
                    logger.warning(f"Empty content for {source_id}, skipping.")
                    processed_ids.add(source_id)
                    continue
                    
                tokens = tokenizer.encode(content, add_special_tokens=False)
                if len(tokens) < 50:
                    logger.warning(f"File {source_id} has only {len(tokens)} tokens (min 50 required), skipping.")
                    processed_ids.add(source_id)
                    continue
                    
                prompt_tokens = tokens[:PROMPT_TOKEN_LEN]
                continuation_tokens = tokens[PROMPT_TOKEN_LEN : PROMPT_TOKEN_LEN + 100]
                
                prompt_text = tokenizer.decode(prompt_tokens, skip_special_tokens=True)
                true_continuation_text = tokenizer.decode(continuation_tokens, skip_special_tokens=True)
                expected_gen_len = len(continuation_tokens)
                
                valid_items.append({
                    "source_id": source_id,
                    "prompt_text": prompt_text,
                    "true_continuation_text": true_continuation_text,
                    "expected_gen_len": expected_gen_len,
                    "cat": cat
                })
            except Exception as e:
                logger.exception(f"Error parsing source {source_id}: {e}")
                processed_ids.add(source_id)
                
        if not valid_items:
            continue
            
        # Run batch model inference
        prompt_texts = [item["prompt_text"] for item in valid_items]
        try:
            inputs = tokenizer(prompt_texts, return_tensors="pt", padding=True).to(next(model.parameters()).device)
            input_len = inputs["input_ids"].shape[1]
            
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=100,  # Generate up to 100 tokens
                    do_sample=False,
                    pad_token_id=tokenizer.eos_token_id
                )
                
            # Process outputs per batch item
            for i, item in enumerate(valid_items):
                source_id = item["source_id"]
                prompt_text = item["prompt_text"]
                true_continuation_text = item["true_continuation_text"]
                expected_gen_len = item["expected_gen_len"]
                cat = item["cat"]
                
                # Extract generated slice
                gen_tokens = outputs[i][input_len:]
                # Truncate to the expected continuation length
                gen_tokens = gen_tokens[:expected_gen_len]
                generated_continuation_text = tokenizer.decode(gen_tokens, skip_special_tokens=True)
                
                # Cap example prompt + continuation combined at 100 tokens
                prompt_text, generated_continuation_text, true_continuation_text = cap_example_tokens(
                    prompt_text, 
                    generated_continuation_text, 
                    true_continuation_text, 
                    tokenizer
                )
                
                # TF-IDF Cosine Similarity Deduplication Check
                combined_candidate = prompt_text + " " + generated_continuation_text
                if is_duplicate_tfidf(combined_candidate, existing_combined_texts):
                    logger.warning(f"Skipping duplicate sequence detected by similarity check for {source_id}.")
                    processed_ids.add(source_id)
                    continue
                    
                existing_combined_texts.append(combined_candidate)
                
                # Compute verification metrics
                rouge_l = scorer.score(true_continuation_text, generated_continuation_text)['rougeL'].fmeasure
                matched_tokens = get_matched_token_count(generated_continuation_text, true_continuation_text, tokenizer)
                longest_ngram = longest_common_ngram_len(generated_continuation_text, true_continuation_text)
                
                # Check borderline cases
                if 0.5 <= rouge_l <= 0.7:
                    is_borderline = True
                    flag_reason = "Borderline ROUGE-L (0.5-0.7)"
                    label = "borderline"
                elif rouge_l <= 0.7 and matched_tokens >= MIN_PREFIX_MATCH_TOKENS:
                    is_borderline = True
                    flag_reason = f"Low ROUGE-L ({rouge_l:.2f}) with high exact prefix match ({matched_tokens} tokens)"
                    label = "borderline"
                else:
                    is_borderline = False
                    flag_reason = None
                    label = "memorized" if rouge_l > 0.7 else "novel"
                    
                row = {
                    "source_id": source_id,
                    "prompt": prompt_text,
                    "generated_continuation": generated_continuation_text,
                    "true_continuation": true_continuation_text,
                    "label": label,
                    "source_category": cat,
                    "rouge_l_score": rouge_l,
                    "matched_token_count": int(matched_tokens),
                    "longest_common_ngram_len": int(longest_ngram)
                }
                
                if is_borderline:
                    row["flag_reason"] = flag_reason
                    append_row_to_csv(csv_out, row)
                    logger.info(f"Example {source_id} flagged for review: {flag_reason}")
                else:
                    append_row_to_parquet(parquet_out, row)
                    logger.info(f"Example {source_id} auto-labeled as '{label}' (ROUGE-L={rouge_l})")
                    
                processed_ids.add(source_id)
                
        except Exception as e:
            logger.error(f"Error processing batch: {e}")
            for item in valid_items:
                processed_ids.add(item["source_id"])

    # 2. Process novel prompts (individually)
    for cat, item_id, content in novel_files:
        source_id = f"{cat}/{item_id}.txt"
        logger.info(f"Processing novel prompt source: {source_id} ...")
        
        try:
            if not content:
                logger.warning(f"Empty content for {source_id}, skipping.")
                processed_ids.add(source_id)
                continue
                
            # Novel prompts: prompt is whole text (cap at 50 tokens)
            p_ids = tokenizer.encode(content, add_special_tokens=False)
            if len(p_ids) > 50:
                p_ids = p_ids[:50]
            prompt_text = tokenizer.decode(p_ids, skip_special_tokens=True)
            true_continuation_text = None
            expected_gen_len = 100 - len(p_ids)
            
            inputs = tokenizer(prompt_text, return_tensors="pt").to(next(model.parameters()).device)
            prompt_encoded_len = inputs["input_ids"].shape[1]
            
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=expected_gen_len,
                    do_sample=False,
                    pad_token_id=tokenizer.eos_token_id
                )
                
            gen_tokens = outputs[0][prompt_encoded_len:]
            generated_continuation_text = tokenizer.decode(gen_tokens, skip_special_tokens=True)
            
            # Cap combined tokens
            prompt_text, generated_continuation_text, true_continuation_text = cap_example_tokens(
                prompt_text, 
                generated_continuation_text, 
                true_continuation_text, 
                tokenizer
            )
            
            # TF-IDF Cosine Similarity Deduplication Check
            combined_candidate = prompt_text + " " + generated_continuation_text
            if is_duplicate_tfidf(combined_candidate, existing_combined_texts):
                logger.warning(f"Skipping duplicate sequence detected by similarity check for {source_id}.")
                processed_ids.add(source_id)
                continue
                
            existing_combined_texts.append(combined_candidate)
            
            row = {
                "source_id": source_id,
                "prompt": prompt_text,
                "generated_continuation": generated_continuation_text,
                "true_continuation": true_continuation_text,
                "label": "novel",
                "source_category": cat,
                "rouge_l_score": None,
                "matched_token_count": 0,
                "longest_common_ngram_len": 0
            }
            
            append_row_to_parquet(parquet_out, row)
            logger.info(f"Example {source_id} auto-labeled as 'novel'")
            processed_ids.add(source_id)
            
        except Exception as e:
            logger.exception(f"Error processing novel prompt file {filepath}: {e}")
            processed_ids.add(source_id)
            
    # 6. Final Reporting
    logger.info("=== Labeled Dataset Summary ===")
    
    total_clean = 0
    clean_counts = {}
    cat_counts = {}
    
    if os.path.exists(parquet_out):
        try:
            df = pd.read_parquet(parquet_out)
            total_clean = len(df)
            clean_counts = df['label'].value_counts().to_dict()
            for cat, count in df['source_category'].value_counts().to_dict().items():
                cat_counts[cat] = cat_counts.get(cat, 0) + count
        except Exception as e:
            logger.error(f"Error summarising parquet: {e}")
            
    total_review = 0
    review_counts = {}
    
    if os.path.exists(csv_out):
        try:
            df = pd.read_csv(csv_out)
            total_review = len(df)
            review_counts = df['flag_reason'].value_counts().to_dict()
            for cat, count in df['source_category'].value_counts().to_dict().items():
                cat_counts[cat] = cat_counts.get(cat, 0) + count
        except Exception as e:
            logger.error(f"Error summarising review CSV: {e}")
            
    print("\n" + "=" * 40)
    print(" PIPELINE PROCESS COMPLETE")
    print("=" * 40)
    print(f"Total Examples Written to clean parquet: {total_clean}")
    for lbl, count in clean_counts.items():
        print(f"  - {lbl}: {count}")
    print(f"\nTotal Borderline/Manual Review Examples: {total_review}")
    for reason, count in review_counts.items():
        print(f"  - {reason}: {count}")
    print("\nTotal Examples by Category Subfolder:")
    for cat, count in cat_counts.items():
        print(f"  - {cat}: {count}")
    print("=" * 40 + "\n")


if __name__ == '__main__':
    main()
