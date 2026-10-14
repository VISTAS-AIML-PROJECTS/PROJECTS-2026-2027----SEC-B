import os
import json

RAW_DIR = "data/memorization/raw"
CATEGORIES = ["wiki_leads", "book_openings", "code_snippets", "lyrics", "novel_prompts"]

def main():
    print("=== Starting Text to JSONL Migration ===")
    
    for category in CATEGORIES:
        category_dir = os.path.join(RAW_DIR, category)
        jsonl_path = os.path.join(RAW_DIR, f"{category}.jsonl")
        
        if not os.path.isdir(category_dir):
            print(f"Directory not found for category '{category}': {category_dir}. Skipping.")
            continue
            
        print(f"Migrating category '{category}' from {category_dir} to {jsonl_path}...")
        
        files = [f for f in os.listdir(category_dir) if f.endswith(".txt")]
        # Sort files to ensure deterministic ordering in JSONL
        files.sort()
        
        count = 0
        with open(jsonl_path, "w", encoding="utf-8") as out_f:
            for filename in files:
                filepath = os.path.join(category_dir, filename)
                
                try:
                    with open(filepath, "r", encoding="utf-8") as in_f:
                        content = in_f.read().strip()
                        
                    # ID is the filename without extension
                    item_id = os.path.splitext(filename)[0]
                    
                    item = {
                        "id": item_id,
                        "content": content,
                        "source_category": category
                    }
                    
                    out_f.write(json.dumps(item, ensure_ascii=False) + "\n")
                    count += 1
                except Exception as e:
                    print(f"Error migrating file {filename}: {e}")
                    
        print(f"Successfully migrated {count} files for '{category}'.")

    print("=== Migration Completed ===")

if __name__ == "__main__":
    main()
