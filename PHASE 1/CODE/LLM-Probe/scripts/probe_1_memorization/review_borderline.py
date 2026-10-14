import os
import sys
import pandas as pd

CSV_PATH = "data/memorization/labeled/needs_manual_review.csv"

# ANSI color codes
RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
RED = "\033[31m"

def print_divider(char="=", length=80, color=CYAN):
    print(color + char * length + RESET)

def main():
    if not os.path.exists(CSV_PATH):
        print(f"Error: Manual review file not found at: {CSV_PATH}")
        sys.exit(1)

    print_divider("=")
    print(f"{BOLD}{CYAN}      LLM PROBE - MEMORIZATION MANUAL REVIEW UTILITY{RESET}")
    print_divider("=")

    df = pd.read_csv(CSV_PATH)
    total_records = len(df)
    print(f"Total Borderline Examples Loaded: {BOLD}{total_records}{RESET}\n")

    # 1. Summary Breakdowns
    print(f"{BOLD}{MAGENTA}--- Breakdown by Flag Reason ---{RESET}")
    reason_counts = df["flag_reason"].value_counts(dropna=False)
    for reason, count in reason_counts.items():
        print(f"  * {reason if pd.notna(reason) else 'No Reason Specified'}: {count}")
    print()

    print(f"{BOLD}{MAGENTA}--- Breakdown by Source Category ---{RESET}")
    category_counts = df["source_category"].value_counts(dropna=False)
    for category, count in category_counts.items():
        print(f"  * {category}: {count}")
    print()

    # 2. Sort by rouge_l_score descending
    # Fill NaN ROUGE-L scores with 0.0 for sorting purpose
    df_sorted = df.copy()
    df_sorted["sort_rouge"] = df_sorted["rouge_l_score"].fillna(0.0)
    df_sorted = df_sorted.sort_values(by="sort_rouge", ascending=False).drop(columns=["sort_rouge"])
    df_sorted = df_sorted.reset_index(drop=True)

    page_size = 15
    total_pages = (total_records + page_size - 1) // page_size

    print(f"Press {BOLD}Enter{RESET} to start reviewing the sorted list ({page_size} entries per page)...")
    input()

    for page_num in range(total_pages):
        start_idx = page_num * page_size
        end_idx = min(start_idx + page_size, total_records)
        
        print_divider("-", 80, MAGENTA)
        print(f"{BOLD}{MAGENTA}Page {page_num + 1} of {total_pages} (Items {start_idx + 1} - {end_idx}){RESET}")
        print_divider("-", 80, MAGENTA)

        for i in range(start_idx, end_idx):
            row = df_sorted.iloc[i]
            
            source_id = row.get("source_id", "Unknown")
            flag_reason = row.get("flag_reason", "No reason")
            rouge_l = row.get("rouge_l_score", 0.0)
            matched_tokens = row.get("matched_token_count", 0)
            
            prompt = str(row.get("prompt", "")).strip()
            true_continuation = str(row.get("true_continuation", "")).strip()
            generated_continuation = str(row.get("generated_continuation", "")).strip()
            
            print(f"\n{BOLD}[{i + 1}] ID: {CYAN}{source_id}{RESET}")
            print(f"    {BOLD}ROUGE-L:{RESET} {GREEN}{rouge_l:.3f}{RESET} | {BOLD}Matched Tokens:{RESET} {YELLOW}{matched_tokens}{RESET}")
            print(f"    {BOLD}Flag Reason:{RESET} {flag_reason}")
            
            print(f"    {BOLD}{CYAN}Prompt:{RESET}")
            print(f"      {prompt}")
            
            print(f"    {BOLD}{GREEN}True Continuation:{RESET}")
            print(f"      {true_continuation}")
            
            print(f"    {BOLD}{YELLOW}Generated Continuation:{RESET}")
            print(f"      {generated_continuation}")
            
            print("-" * 60)

        if end_idx < total_records:
            choice = input(f"\n{BOLD}Show next page? [Enter for Next, 'q' to Quit]: {RESET}").strip().lower()
            if choice == 'q':
                print("\nReview session ended.")
                break
        else:
            print("\nReached the end of the manual review list.")

if __name__ == "__main__":
    main()
