import os
import sys
import logging
import pandas as pd
import datasets

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("=== Starting Step 1: Export Newly Resolved Ambiguous Rows for Review ===")
    
    data_dir = "data/hallucination/labeled"
    input_path = os.path.join(data_dir, "newly_resolved.csv")
    output_path = os.path.join(data_dir, "newly_resolved_review.csv")
    
    if not os.path.exists(input_path):
        logger.error(f"Input file not found at: {input_path}")
        sys.exit(1)
        
    # Load newly resolved rows
    df_resolved = pd.read_csv(input_path)
    total_rows = len(df_resolved)
    logger.info(f"Loaded {total_rows} rows from {input_path}")
    
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
    for idx, row in df_resolved.iterrows():
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
            "current_label": row["label"],
            "correct_sim_score": row["correct_sim_score"],
            "incorrect_sim_score": row["incorrect_sim_score"],
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
