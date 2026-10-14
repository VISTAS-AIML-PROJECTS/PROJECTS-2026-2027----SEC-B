import os
import sys
import logging
import pandas as pd

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("=== Starting Step 2: Apply Newly Resolved Decisions ===")
    
    data_dir = "data/hallucination/labeled"
    review_path = os.path.join(data_dir, "newly_resolved_review.csv")
    parquet_path = os.path.join(data_dir, "dataset.parquet")
    
    if not os.path.exists(review_path):
        logger.error(f"Review file not found at: {review_path}. Run Step 1 first.")
        sys.exit(1)
    if not os.path.exists(parquet_path):
        logger.error(f"Dataset parquet file not found at: {parquet_path}.")
        sys.exit(1)
        
    # 1. Load and Validate Review File
    df_review = pd.read_csv(review_path)
    logger.info(f"Loaded {len(df_review)} rows for review from {review_path}")
    
    unresolved_ids = []
    decisions = {}
    
    for idx, row in df_review.iterrows():
        row_id = row["row_id"]
        decision = row.get("final_decision")
        
        # Check if empty/NaN
        if pd.isna(decision):
            unresolved_ids.append(row_id)
            continue
            
        decision_str = str(decision).strip().lower()
        if decision_str not in ["grounded", "hallucinated", "exclude"]:
            unresolved_ids.append(row_id)
        else:
            decisions[row["question"]] = {
                "decision": decision_str,
                "current_label": row["current_label"],
                # Store full row details to reconstruct for parquet merge
                "category": row["category"],
                "generated_answer": row["generated_answer"],
                "best_answer": row["best_answer_reference"],
                "correct_sim_score": row["correct_sim_score"],
                "incorrect_sim_score": row["incorrect_sim_score"]
            }
            
    if unresolved_ids:
        logger.error(f"Validation failed. The following row_id(s) have blank or invalid final_decision: {unresolved_ids}")
        logger.error("STOPPING. No changes have been applied.")
        sys.exit(1)
        
    logger.info("Validation successful! All decisions are valid.")
    
    # 2. Load Parquet Dataset
    df_dataset = pd.read_parquet(parquet_path)
    before_counts = df_dataset["label"].value_counts().to_dict()
    logger.info(f"Original dataset shape: {df_dataset.shape}")
    logger.info(f"Original label counts: {before_counts}")
    
    # 3. Check for duplicates in dataset.parquet before merging
    # (newly resolved rows were previously ambiguous and in needs_manual_review.csv, so they shouldn't be in dataset.parquet,
    # but we must check and drop any matching questions to be safe)
    duplicate_questions = []
    for q in decisions.keys():
        if q in df_dataset["question"].values:
            duplicate_questions.append(q)
            
    if duplicate_questions:
        logger.warning(f"Found {len(duplicate_questions)} question(s) already in dataset.parquet. Dropping from base dataset to avoid duplicates...")
        df_dataset = df_dataset[~df_dataset["question"].isin(duplicate_questions)]
        logger.info(f"Filtered base dataset shape: {df_dataset.shape}")
        
    # 4. Process Decisions & Merge
    kept_count = 0
    flipped_count = 0
    excluded_count = 0
    
    new_rows = []
    
    for question, info in decisions.items():
        decision = info["decision"]
        current_label = info["current_label"]
        
        if decision == "exclude":
            logger.info(f"Excluding question: {question}")
            excluded_count += 1
            continue
            
        # Reconstruct row matching parquet schema
        new_row = {
            "question": question,
            "generated_answer": info["generated_answer"],
            "best_answer": info["best_answer"],
            "category": info["category"],
            "correct_sim_score": info["correct_sim_score"],
            "incorrect_sim_score": info["incorrect_sim_score"],
            "label": decision,
            "label_reason": "manual_review"
        }
        new_rows.append(new_row)
        
        if decision == current_label:
            kept_count += 1
        else:
            flipped_count += 1
            logger.info(f"Flipped label for: '{question}' from '{current_label}' to '{decision}'")
            
    if new_rows:
        df_new = pd.DataFrame(new_rows)
        df_dataset = pd.concat([df_dataset, df_new], ignore_index=True)
        
    # 5. Verify & Save
    after_counts = df_dataset["label"].value_counts().to_dict()
    
    # Save back to dataset.parquet atomically
    temp_path = parquet_path + ".tmp"
    df_dataset.to_parquet(temp_path, index=False)
    if os.path.exists(parquet_path):
        os.remove(parquet_path)
    os.rename(temp_path, parquet_path)
    
    logger.info("=== Apply Summary ===")
    logger.info(f"Decisions processed for {len(decisions)} questions:")
    logger.info(f"  * Kept auto-assigned label: {kept_count}")
    logger.info(f"  * Flipped to other label: {flipped_count}")
    logger.info(f"  * Excluded (dropped entirely): {excluded_count}")
    logger.info(f"Dataset saved back to: {parquet_path}")
    logger.info(f"Before label counts: {before_counts}")
    logger.info(f"After label counts: {after_counts}")
    logger.info("Step 2 completed successfully!")

if __name__ == "__main__":
    main()
