import os

SUPPLEMENTAL_FILE = "data/memorization/raw/supplemental_code_snippets.txt"
CODE_SNIPPETS_DIR = "data/memorization/raw/code_snippets"

def main():
    if not os.path.exists(SUPPLEMENTAL_FILE):
        print(f"Supplemental file not found at {SUPPLEMENTAL_FILE}")
        return
        
    with open(SUPPLEMENTAL_FILE, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Split on "===" delimiters
    blocks = content.split("===")
    
    total_saved = 0
    total_skipped = 0
    
    os.makedirs(CODE_SNIPPETS_DIR, exist_ok=True)
    
    for block in blocks:
        block = block.strip()
        if not block:
            continue
            
        # Split on "---"
        parts = block.split("---", 1)
        if len(parts) != 2:
            print("Warning: Invalid block format. Skipping.")
            continue
            
        filename = parts[0].strip()
        code = parts[1].strip()
        
        # Map .py to .txt extension so they are recognized by build_memorization_dataset.py
        if filename.endswith(".py"):
            filename = filename[:-3] + ".txt"
        elif not filename.endswith(".txt"):
            filename += ".txt"
            
        filepath = os.path.join(CODE_SNIPPETS_DIR, filename)
        
        # Skip if already exists
        if os.path.exists(filepath):
            print(f"[SKIP] {filename} already exists.")
            total_skipped += 1
            continue
            
        with open(filepath, "w", encoding="utf-8") as out_f:
            out_f.write(code + "\n")
            
        print(f"[SAVED] {filename}")
        total_saved += 1
        
    print(f"\nSupplemental Merge Complete:")
    print(f"  - Saved:   {total_saved}")
    print(f"  - Skipped: {total_skipped}")

if __name__ == "__main__":
    main()
