import os
import sys
import logging
import pandas as pd

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("=== Starting Step 2: Apply Reconsidered Decisions ===")
    
    data_dir = "data/hallucination/labeled"
    review_path = os.path.join(data_dir, "reconsidered_review.csv")
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
            decisions[row["question"]] = decision_str
            
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
    duplicate_mask = df_dataset.duplicated(subset=["question"], keep="first")
    if duplicate_mask.any():
        duplicate_questions = df_dataset[duplicate_mask]["question"].tolist()
        logger.warning(f"Found {len(duplicate_questions)} duplicate question(s) already in dataset.parquet. Excluding them...")
        df_dataset = df_dataset.drop_duplicates(subset=["question"], keep="first")
        logger.info(f"Cleaned dataset shape: {df_dataset.shape}")
        
    # 4. Apply Decisions
    kept_hallucinated = 0
    flipped_grounded = 0
    excluded_count = 0
    
    rows_to_keep = []
    
    for idx, row in df_dataset.iterrows():
        question = row["question"]
        if question in decisions:
            decision = decisions[question]
            if decision == "exclude":
                logger.info(f"Excluding question: {question}")
                excluded_count += 1
                continue
                
            row_dict = row.to_dict()
            row_dict["label"] = decision
            row_dict["label_reason"] = "manual_review"
            rows_to_keep.append(row_dict)
            
            if decision == "grounded":
                flipped_grounded += 1
            else:
                kept_hallucinated += 1
        else:
            rows_to_keep.append(row.to_dict())
            
    df_dataset = pd.DataFrame(rows_to_keep)
    
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
    logger.info(f"  * Kept 'hallucinated': {kept_hallucinated}")
    logger.info(f"  * Flipped to 'grounded': {flipped_grounded}")
    logger.info(f"  * Excluded (dropped entirely): {excluded_count}")
    logger.info(f"Dataset saved back to: {parquet_path}")
    logger.info(f"Before label counts: {before_counts}")
    logger.info(f"After label counts: {after_counts}")
    logger.info("Step 2 completed successfully!")

if __name__ == "__main__":
    main()
