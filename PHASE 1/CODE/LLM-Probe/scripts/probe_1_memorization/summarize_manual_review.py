import os
import re
import sys
import json
import pandas as pd

CSV_PATH = "data/memorization/labeled/needs_manual_review.csv"
REPORT_PATH = "data/memorization/raw/manual_review_full_report.md"

COMMON_BOILERPLATE = [
    "for i in range", "return true", "return false", "return none",
    "if __name__", "while true", "while len", "else:", "elif ", "try:",
    "except exception", "import random", "import math", "import sys",
    "from collections", "from typing", "print(", "self.", "def ", "class "
]

ENCYCLOPEDIC_STOPPHRASES = [
    "is derived from the",
    "fall of the",
    "widely considered to be",
    "is a type of",
    "one of the most",
    "in the United States",
    "is a system of",
    "refer to the",
    "derived from the Latin",
    "is defined as",
    "known as the",
    "as well as",
    "the end of the",
    "the beginning of the",
    "in the late 19th and early",
    "plays and possibly alters the",
    "express interest in one or more",
    "for the treatment and prevention of",
    "either kill or",
    "are widely used in",
    "is a cyberattack where the",
    "the communications between two",
    "who believe they are",
    "which the attacker makes",
    "in the treatment of",
    "is a general-purpose",
    "is designed by French",
    "is widely considered to be",
    "father of theoretical computer",
    "often called England's national",
    "and the \"Bard of Avon\"",
    "finds the shortest path from",
    "striking and bizarre images in",
    "stein, a young scientist who",
    "creates a sapient creature",
    "Philosophiæ Naturalis Principia",
    "An Inquiry into the Nature",
    "the named subject of the",
    "This allows others",
    "eader of the Conservative Party",
    "during the Hundred Days in",
    "He rose to prominence",
    "he launched a series of",
    "most of the Amazon basin",
    "This basin encompasses",
    "provides a standard interface for",
    "of the Kingdom of the",
    "it is the largest hot",
    "of the Soviet Union from",
    "the random forest is the",
    "molecular biology, developmental",
    "Netherlands to the north",
    "Germany to the east",
    "graphics processing units",
    "high-performance computing",
    "bacteria, and parasites, as",
    "pread and highly technical",
    "threads to temporarily give up",
    "exclusive access in order to",
    "or \"find and replace\"",
    "medium for advertising, entertainment",
    "runs one or more virtual",
    "machines is called a host",
    "hydrogen, sulfur, oxygen",
    "that is both human-readable and",
    "equal portions and in circular",
    "handling all processes without",
    "ing after the Christianization of",
    "to access the same data",
    "as obese when their body",
    "isms, including bacteria and",
    "aboard the Space Shuttle",
    "public, academic, business",
    "and government networks"
]

def is_generic_boilerplate(substring: str) -> bool:
    sub_clean = re.sub(r'\s+', ' ', substring).strip().lower()
    if not sub_clean:
        return True
    if re.match(r'^[\[\]\(\)\{\}\s\:\,\|\&\=\+\-\*\/\\\"\t\n\r_\;\'\>\<\!]+$', substring):
        return True
    for bp in COMMON_BOILERPLATE:
        if bp in sub_clean:
            cleaned_sub = sub_clean.replace(bp, "").strip()
            if not cleaned_sub or re.match(r'^[\[\]\(\)\{\}\s\:\,\|\&\=\+\-\*\/\\\"\t\n\r_\;\'\>\<\!]+$', cleaned_sub):
                return True
    return False

def is_generic_phrase(substring: str) -> bool:
    sub_lower = substring.lower()
    for phrase in ENCYCLOPEDIC_STOPPHRASES:
        if phrase.lower() in sub_lower:
            if len(phrase) >= len(substring) * 0.70:
                return True
    return False

def is_model_instability(text: str) -> bool:
    if not isinstance(text, str):
        return False
    cjk_pattern = re.compile(r'[\u4e00-\u9fff\u3000-\u303f\u3040-\u30ff\uff00-\uffef]')
    if cjk_pattern.search(text):
        return True
    for c in text:
        o = ord(c)
        if o > 127:
            if not (0xA0 <= o <= 0xFF) and not (0x2010 <= o <= 0x2027) and not (0x2030 <= o <= 0x203A):
                return True
    return False

def has_tighter_requirements(substring: str) -> bool:
    # 1. 3+ consecutive digits
    if re.search(r'\d{3,}', substring):
        return True
    # 2. A string literal containing non-trivial content (len >= 3)
    literals = re.findall(r'["\']([^"\'\n]+)["\']', substring)
    for lit in literals:
        lit_clean = lit.strip()
        if len(lit_clean) >= 3 and not lit_clean.isspace():
            if any(c.isalnum() for c in lit_clean):
                return True
    # 3. Unusual/non-generic identifier name
    words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', substring)
    generic_identifiers = {
        "i", "j", "k", "n", "m", "x", "y", "z", "a", "b", "c", "d", "v",
        "arr", "list", "dict", "set", "result", "res", "temp", "val", "value",
        "key", "data", "item", "items", "file", "f", "self", "args", "kwargs",
        "def", "class", "return", "if", "for", "while", "else", "elif", "in",
        "is", "and", "or", "not", "import", "from", "as", "try", "except",
        "pass", "break", "continue", "true", "false", "none", "len", "range",
        "append", "pop", "insert", "print"
    }
    for w in words:
        if w.lower() not in generic_identifiers and len(w) >= 3:
            return True
    return False

def find_strong_memorization_match(true_str, gen_str) -> str:
    """
    Finds if there is a common substring of length >= 30 between true_str and gen_str
    that contains consecutive digits, custom literals, or non-generic identifiers,
    and is not generic boilerplate or encyclopedic phrase.
    """
    if not isinstance(true_str, str) or not isinstance(gen_str, str):
        return ""
        
    true_str_clean = true_str.strip()
    gen_str_clean = gen_str.strip()
    
    n = len(true_str_clean)
    m = len(gen_str_clean)
    
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    longest = 0
    longest_substring = ""
    
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if true_str_clean[i-1] == gen_str_clean[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
                if dp[i][j] >= 30:
                    substring = true_str_clean[i - dp[i][j] : i]
                    if not is_generic_boilerplate(substring) and not is_generic_phrase(substring) and has_tighter_requirements(substring):
                        if dp[i][j] > longest:
                            longest = dp[i][j]
                            longest_substring = substring
            else:
                dp[i][j] = 0
                
    return longest_substring

def check_non_narrative(text) -> list:
    """
    Returns a list of reasons why the text is suspected to be non-narrative structural content.
    """
    if not isinstance(text, str):
        return []
        
    reasons = []
    text_lower = text.lower()
    
    # Chapter markers count
    chapters = re.findall(r'\bchapter\b', text_lower)
    if len(chapters) >= 3:
        reasons.append(f"Contains multiple chapter markings ({len(chapters)} times)")
        
    # Roman numeral list patterns
    roman_seq = re.findall(r'\b(?:[IVXLCDM]+[\.\s:-]+)', text)
    if len(roman_seq) >= 4:
        reasons.append(f"Contains sequence of Roman numeral headers ({len(roman_seq)} times)")
        
    # Dot leaders for TOC
    dot_leaders = re.findall(r'\.{4,}', text)
    if len(dot_leaders) >= 2:
        reasons.append(f"Contains table-of-contents dot leaders ({len(dot_leaders)} times)")
        
    # Line layouts
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if len(lines) >= 5:
        numbered_lines = sum(1 for l in lines if re.match(r'^(?:\d+|[a-zA-Z])[\.\)]', l))
        bullet_lines = sum(1 for l in lines if l.startswith(('*', '-', '+', 'o ')))
        if numbered_lines >= len(lines) * 0.4:
            reasons.append(f"High percentage of numbered lines ({numbered_lines}/{len(lines)})")
        if bullet_lines >= len(lines) * 0.4:
            reasons.append(f"High percentage of bulleted lines ({bullet_lines}/{len(lines)})")
            
    if len(lines) >= 8:
        short_lines_with_digits = sum(1 for l in lines if len(l) < 50 and re.search(r'\d+$', l))
        if short_lines_with_digits >= len(lines) * 0.5:
            reasons.append(f"TOC/Index layout: short lines ending in digits ({short_lines_with_digits}/{len(lines)})")
            
    return reasons

def main():
    if not os.path.exists(CSV_PATH):
        print(f"Error: CSV file not found at: {CSV_PATH}")
        sys.exit(1)
        
    df = pd.read_csv(CSV_PATH)
    
    # Sort by rouge_l_score descending
    df_sorted = df.copy()
    df_sorted["sort_rouge"] = df_sorted["rouge_l_score"].fillna(0.0)
    df_sorted = df_sorted.sort_values(by="sort_rouge", ascending=False).drop(columns=["sort_rouge"])
    df_sorted = df_sorted.reset_index(drop=True)
    
    strong_candidates = []
    extraction_bugs = []
    instability_artifacts = []
    all_entries_md = []
    
    for idx, row in df_sorted.iterrows():
        source_id = row.get("source_id", "Unknown")
        rouge_l = row.get("rouge_l_score", 0.0)
        matched_tokens = row.get("matched_token_count", 0)
        flag_reason = row.get("flag_reason", "No reason")
        cat = row.get("source_category", "Unknown")
        
        prompt = str(row.get("prompt", "")).strip()
        true_continuation = str(row.get("true_continuation", "")).strip()
        generated_continuation = str(row.get("generated_continuation", "")).strip()
        
        # Check for model instability first
        is_unstable = is_model_instability(generated_continuation)
        
        # 1. Check for strong memorization candidates
        strong_match = ""
        if not is_unstable:
            strong_match = find_strong_memorization_match(true_continuation, generated_continuation)
        
        # 2. Check for possible extraction bugs (non-narrative structural text)
        bug_reasons = []
        if not is_unstable:
            bug_reasons.extend(check_non_narrative(prompt))
            bug_reasons.extend(check_non_narrative(true_continuation))
            bug_reasons = list(set(bug_reasons))
        
        entry_data = {
            "index": idx + 1,
            "source_id": source_id,
            "rouge_l_score": rouge_l,
            "matched_token_count": matched_tokens,
            "flag_reason": flag_reason,
            "prompt": prompt,
            "true_continuation": true_continuation,
            "generated_continuation": generated_continuation,
            "strong_match": strong_match,
            "bug_reasons": bug_reasons
        }
        
        if is_unstable:
            instability_artifacts.append(entry_data)
        else:
            if strong_match:
                strong_candidates.append(entry_data)
            if bug_reasons:
                extraction_bugs.append(entry_data)
            
        # Format the entry's Markdown representation
        md_block = f"### Entry {idx + 1}: `{source_id}`\n\n"
        md_block += f"* **Category**: {cat}\n"
        md_block += f"* **ROUGE-L Score**: {rouge_l:.4f}\n"
        md_block += f"* **Matched Token Count**: {matched_tokens}\n"
        md_block += f"* **Flag Reason**: {flag_reason}\n"
        
        if is_unstable:
            md_block += f"* **[FLAG] Model Instability Artifact**: True (contains garbled/non-ASCII characters)\n"
        else:
            if strong_match:
                md_block += f"* **[FLAG] Strong Memorization Match**: `{repr(strong_match)}`\n"
            if bug_reasons:
                md_block += f"* **[FLAG] Possible Extraction Bug**: {', '.join(bug_reasons)}\n"
            
        md_block += f"""
#### Prompt
```text
{prompt}
```

#### True Continuation
```text
{true_continuation}
```

#### Generated Continuation
```text
{generated_continuation}
```

---
"""
        all_entries_md.append(md_block)
        
    # Write the report
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("# Memorization Dataset - Manual Review Full Report\n\n")
        f.write(f"Total borderline cases analyzed: **{len(df_sorted)}**\n\n")
        
        # SECTION 1: Strong Memorization Candidates
        f.write("## 1. Strong Memorization Candidates\n")
        f.write("These entries generated an exact matching substring of **30+ consecutive characters** that contains consecutive digits, string literals, or non-generic identifiers, excluding generic boilerplate and common encyclopedic phrases.\n\n")
        if strong_candidates:
            for item in strong_candidates:
                f.write(f"- **Entry {item['index']}**: `{item['source_id']}` (ROUGE-L: {item['rouge_l_score']:.4f})  \n")
                f.write(f"  *Matching Substring*: `{repr(item['strong_match'])}`  \n")
        else:
            f.write("*(None found)*\n")
        f.write("\n---\n\n")
        
        # SECTION 2: Model Instability Artifacts
        f.write("## 2. Model Instability Artifacts\n")
        f.write("These entries contain garbled, non-ASCII characters or CJK ideographs in the generated continuation, indicating model failure/instability rather than memorization.\n\n")
        if instability_artifacts:
            for item in instability_artifacts:
                f.write(f"- **Entry {item['index']}**: `{item['source_id']}` (ROUGE-L: {item['rouge_l_score']:.4f})  \n")
        else:
            f.write("*(None found)*\n")
        f.write("\n---\n\n")
        
        # SECTION 3: Possible Extraction Bugs
        f.write("## 3. Possible Extraction Bugs\n")
        f.write("These entries contain text that matches table-of-contents lists, index pages, or repetitive line headers rather than narrative body text.\n\n")
        if extraction_bugs:
            for item in extraction_bugs:
                f.write(f"- **Entry {item['index']}**: `{item['source_id']}` (Category: `{item['source_id'].split('/')[0]}`)  \n")
                f.write(f"  *Reason(s)*: {', '.join(item['bug_reasons'])}  \n")
        else:
            f.write("*(None found)*\n")
        f.write("\n---\n\n")
        
        # SECTION 4: Full Entries List
        f.write("## 4. Full List of Borderline Entries (Sorted by ROUGE-L Descending)\n\n")
        f.write("\n".join(all_entries_md))
        
    print(f"Full report successfully written to: {REPORT_PATH}")
    print(f"Total Strong Candidates: {len(strong_candidates)}")
    print(f"Total Model Instabilities: {len(instability_artifacts)}")
    print(f"Total Possible Extraction Bugs: {len(extraction_bugs)}")

if __name__ == "__main__":
    main()
