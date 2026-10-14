import os
import sys
import logging
import pandas as pd
import datasets

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("=== Starting Step 1: Export Remaining Ambiguous Rows for Review ===")
    
    data_dir = "data/hallucination/labeled"
    input_path = os.path.join(data_dir, "needs_manual_review.csv")
    resolved_path = os.path.join(data_dir, "newly_resolved_review.csv")
    output_path = os.path.join(data_dir, "needs_manual_review_export.csv")
    
    if not os.path.exists(input_path):
        logger.error(f"Input file not found at: {input_path}")
        sys.exit(1)
        
    # Load needs_manual_review rows
    df_needs = pd.read_csv(input_path)
    total_rows = len(df_needs)
    logger.info(f"Total rows in raw needs_manual_review.csv: {total_rows}")
    
    # Load resolved questions if newly_resolved_review.csv exists
    resolved_questions = set()
    if os.path.exists(resolved_path):
        df_resolved = pd.read_csv(resolved_path)
        resolved_questions = set(df_resolved["question"].tolist())
        logger.info(f"Loaded {len(resolved_questions)} resolved questions from {resolved_path}")
    else:
        logger.info("No newly_resolved_review.csv found. Exporting all rows.")
        
    # Filter out already resolved questions
    df_filtered = df_needs[~df_needs["question"].isin(resolved_questions)].reset_index(drop=True)
    logger.info(f"Filtered to {len(df_filtered)} remaining unresolved questions.")
    
    # Load TruthfulQA dataset for references lookup
    logger.info("Loading TruthfulQA dataset for reference lookups...")
    try:
        dataset_dict = datasets.load_dataset("truthful_qa", "generation")
    except Exception as e:
        logger.warning(f"Could not load 'truthful_qa' generation split directly: {e}. Trying fallback 'truthfulqa/truthful_qa'...")
        dataset_dict = datasets.load_dataset("truthfulqa/truthful_qa", "generation")
        
    validation_data = dataset_dict["validation"]
    
    ref_map = {}
    for item in validation_data:
        ref_map[item["question"]] = {
            "correct_answers": str(item["correct_answers"]),
            "incorrect_answers": str(item["incorrect_answers"])
        }
        
    # Prepare review dataframe
    review_rows = []
    for idx, row in df_filtered.iterrows():
        question = row["question"]
        ref = ref_map.get(question, {"correct_answers": "[]", "incorrect_answers": "[]"})
        
        review_row = {
            "row_id": idx,
            "question": question,
            "category": row["category"],
            "generated_answer": row["generated_answer"],
            "best_answer_reference": row["best_answer"],
            "correct_answers": ref["correct_answers"],
            "incorrect_answers": ref["incorrect_answers"],
            "correct_sim_score": row["correct_sim_score"],
            "incorrect_sim_score": row["incorrect_sim_score"],
            "flag_reason": row["flag_reason"],
            "final_decision": ""
        }
        review_rows.append(review_row)
        
    df_review = pd.DataFrame(review_rows)
    
    # Sort by category
    df_review = df_review.sort_values(by="category").reset_index(drop=True)
    
    # Save output
    df_review.to_csv(output_path, index=False)
    
    logger.info(f"Successfully exported {len(df_review)} rows sorted by category.")
    logger.info(f"Review file path: {output_path}")

if __name__ == "__main__":
    main()
