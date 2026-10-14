import os
import re
import sys
import time
import urllib.parse
import logging
import requests
import json
from typing import Set, Tuple

# Set up logging to stdout
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
BOOKS_LIST_FILE = "data/memorization/raw/gutenberg_books.txt"
BOOK_OPENINGS_JSONL = "data/memorization/raw/book_openings.jsonl"
EXTRACTION_LOG_FILE = "data/memorization/raw/book_openings/_extraction_log.txt"
USER_AGENT = "LLMProbeResearchBot/1.0 (academic research; contact: project-llm-probe@example.com)"
RATE_LIMIT_DELAY = 0.5  # seconds
TARGET_WORD_COUNT = 180


def sanitize_filename(title: str) -> str:
    """
    Sanitizes a book title to be a safe Windows filename/id.
    Replaces spaces with underscores and invalid chars with underscores.
    """
    clean = re.sub(r'[\\/*?:"<>|]', '_', title)
    clean = clean.replace(' ', '_')
    clean = re.sub(r'_+', '_', clean)
    return clean.strip('_')


def strip_gutenberg_boilerplate(text: str) -> str:
    """
    Strips Project Gutenberg's start and end boilerplates using regex.
    """
    start_pattern = re.compile(r'(?i)\*\*\*\s*START OF (?:THE|THIS) PROJECT GUTENBERG EBOOK[^*]*\*\*\*')
    end_pattern = re.compile(r'(?i)\*\*\*\s*END OF (?:THE|THIS) PROJECT GUTENBERG EBOOK[^*]*\*\*\*')
    
    start_match = start_pattern.search(text)
    if start_match:
        text = text[start_match.end():]
        
    end_match = end_pattern.search(text)
    if end_match:
        text = text[:end_match.start()]
        
    return text


def is_structural_toc(text: str) -> bool:
    """
    Returns True if more than 30% of the words in the text match Roman numerals 
    or standard table-of-contents structural keywords.
    """
    words = text.split()
    if not words:
        return True
        
    roman_pattern = re.compile(r'^(?:[IVXLCDM]+|[IVXLCDM]+[\.\s:-]+)$', re.IGNORECASE)
    structural_words = {
        "chapter", "chapters", "act", "scene", "book", "part", "section",
        "preface", "introduction", "prologue", "epilogue", "note", "contents",
        "table", "matières", "première", "deuxième", "troisième"
    }
    
    match_count = 0
    for w in words:
        w_clean = re.sub(r'[^\w]', '', w).lower()
        if w_clean in structural_words or roman_pattern.match(w):
            match_count += 1
            
    ratio = match_count / len(words)
    return ratio > 0.3


def extract_narrative_opening(text: str) -> Tuple[str, str]:
    """
    Extracts the opening target narrative text of the book, skipping front matter.
    Returns (extracted_text, success_method).
    """
    patterns = [
        ("matched CHAPTER I/1/ONE pattern", r'(?i)\bCHAPTER\s+(?:I|1|ONE)\b'),
        ("matched BOOK I/1/ONE pattern", r'(?i)\bBOOK\s+(?:I|1|ONE)\b'),
        ("matched PART I/1/ONE pattern", r'(?i)\bPART\s+(?:I|1|ONE)\b'),
        ("matched ACT/SCENE I/1/ONE pattern", r'(?i)\b(?:ACT|SCENE)\s+(?:I|1|ONE)\b'),
        ("matched Roman numeral/digit start pattern", r'(?im)^\s*(?:I|1)\.\s+')
    ]
    
    start_idx = 0
    success_method = "fallback: took first N words after boilerplate strip only"
    
    for method_name, pat in patterns:
        matches = list(re.finditer(pat, text))
        if matches:
            if len(matches) >= 2:
                # If multiple matches, skip past the last match (likely skipping TOC list)
                start_idx = matches[-1].end()
                success_method = f"{method_name} (last match, skipping TOC)"
            else:
                start_idx = matches[0].end()
                success_method = f"{method_name} (first match)"
            break
            
    narrative = text[start_idx:]
    if not narrative.strip():
        narrative = text
        success_method = "fallback: took first N words after boilerplate strip only (empty chapter slice)"
        
    lines = narrative.split('\n')
    clean_lines = []
    skipping_headers = True
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if not skipping_headers:
                clean_lines.append("")
            continue
            
        is_header = False
        if len(stripped) < 60 and stripped.isupper():
            is_header = True
        if re.match(r'(?i)^(?:CHAPTER|Chapter|BOOK|Book|SECTION|Section|Part|PART|ACT|Act|SCENE|Scene|PROLOGUE|Prologue|ETYMOLOGY|Etymology|PREFACE|Preface|INTRODUCTION|Introduction|EPILOGUE|Epilogue)\b', stripped):
            is_header = True
            
        if skipping_headers and is_header:
            continue
            
        skipping_headers = False
        clean_lines.append(stripped)
        
    words_text = " ".join([l for l in clean_lines if l]).strip()
    words = words_text.split()
    first_attempt_text = " ".join(words[:TARGET_WORD_COUNT])
    
    # Validate the first attempt
    if not is_structural_toc(first_attempt_text):
        return first_attempt_text, success_method
        
    # Validation failed (detected TOC structure). Try to skip further ahead.
    logger.info("Validation failed (TOC/Structural elements detected). Retrying by seeking first large prose paragraph...")
    
    paragraphs = narrative.split('\n\n')
    for idx_p, p in enumerate(paragraphs):
        p_clean = " ".join(p.split()).strip()
        p_words = p_clean.split()
        if len(p_words) >= 40 and not is_structural_toc(p_clean):
            subsequent_text = " ".join(paragraphs[idx_p:])
            clean_sub_lines = " ".join(subsequent_text.split()).split()
            retry_text = " ".join(clean_sub_lines[:TARGET_WORD_COUNT])
            return retry_text, f"{success_method} + TOC bypass retry (skipped {idx_p} paragraphs)"
            
    return first_attempt_text, f"{success_method} (failed TOC bypass)"


def main():
    logger.info("=== Starting Project Gutenberg Book Openings Fetching Utility ===")
    
    # 1. Setup Directories
    os.makedirs(os.path.dirname(BOOK_OPENINGS_JSONL), exist_ok=True)
    os.makedirs(os.path.dirname(EXTRACTION_LOG_FILE), exist_ok=True)
    
    if not os.path.exists(BOOKS_LIST_FILE):
        logger.error(f"Books list file not found at: {BOOKS_LIST_FILE}")
        sys.exit(1)
        
    # 2. Read Books list
    books = []
    with open(BOOKS_LIST_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or "|" not in line:
                continue
            title, gutenberg_id = line.split("|", 1)
            books.append((title.strip(), gutenberg_id.strip()))
            
    logger.info(f"Loaded {len(books)} books from {BOOKS_LIST_FILE}")
    
    # Load existing IDs for resumability
    existing_ids = set()
    if os.path.exists(BOOK_OPENINGS_JSONL):
        with open(BOOK_OPENINGS_JSONL, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        item = json.loads(line)
                        if "id" in item:
                            existing_ids.add(item["id"])
                    except Exception:
                        pass
        logger.info(f"Loaded {len(existing_ids)} already existing IDs from {BOOK_OPENINGS_JSONL}")
    
    log_mode = "w" if len(existing_ids) <= 1 else "a"
    
    # Counter metrics
    total_fetched = 0
    total_skipped = 0
    total_failed = 0
    
    headers = {
        "User-Agent": USER_AGENT
    }
    
    # 3. Process each book
    for idx, (title, gutenberg_id) in enumerate(books, 1):
        sanitized = sanitize_filename(title)
        
        # Resumability check
        if sanitized in existing_ids:
            logger.info(f"[{idx}/{len(books)}] [SKIP] '{title}' (ID: {gutenberg_id}) already exists. Skipping.")
            total_skipped += 1
            continue
            
        url = f"https://www.gutenberg.org/cache/epub/{gutenberg_id}/pg{gutenberg_id}.txt"
        
        try:
            logger.info(f"[{idx}/{len(books)}] [FETCHING] Downloading '{title}' (ID: {gutenberg_id})...")
            response = requests.get(url, headers=headers, timeout=15)
            
            # Rate limiting delay
            time.sleep(RATE_LIMIT_DELAY)
            
            if response.status_code == 200:
                raw_text = response.text
                
                # Strip boilerplate
                body_text = strip_gutenberg_boilerplate(raw_text)
                
                # Extract narrative opening
                opening_text, method_used = extract_narrative_opening(body_text)
                
                # Check if we got text
                if not opening_text.strip():
                    logger.error(f"[{idx}/{len(books)}] [FAIL] Extracted text was empty for '{title}' (ID: {gutenberg_id}).")
                    total_failed += 1
                    continue
                    
                # Append to JSONL file
                with open(BOOK_OPENINGS_JSONL, "a", encoding="utf-8") as out_f:
                    item = {
                        "id": sanitized,
                        "content": opening_text,
                        "source_category": "book_openings"
                    }
                    out_f.write(json.dumps(item, ensure_ascii=False) + "\n")
                    
                existing_ids.add(sanitized)
                
                # Write to extraction log
                preview = opening_text[:300] + ("..." if len(opening_text) > 300 else "")
                with open(EXTRACTION_LOG_FILE, log_mode, encoding="utf-8") as log_f:
                    log_f.write(f"Book: {title} (ID: {gutenberg_id})\n")
                    log_f.write(f"ID: {sanitized}\n")
                    log_f.write(f"Method: {method_used}\n")
                    log_f.write(f"Preview (first 300 chars):\n{preview}\n")
                    log_f.write("-" * 50 + "\n")
                log_mode = "a"
                
                word_count = len(opening_text.split())
                logger.info(
                    f"[{idx}/{len(books)}] [SUCCESS] Saved '{title}' ({word_count} words) via '{method_used}' to JSONL"
                )
                total_fetched += 1
                
            else:
                logger.error(f"[{idx}/{len(books)}] [FAIL] HTTP {response.status_code} for '{title}' (ID: {gutenberg_id}).")
                total_failed += 1
                
        except Exception as e:
            logger.error(f"[{idx}/{len(books)}] [ERROR] Failed to download/process '{title}' (ID: {gutenberg_id}): {e}")
            total_failed += 1
            time.sleep(RATE_LIMIT_DELAY)
            
    # Final Reporting
    print("\n" + "=" * 40)
    print(" PROJECT GUTENBERG BOOK OPENINGS FETCH COMPLETE")
    print("=" * 40)
    print(f"Total Books Configured: {len(books)}")
    print(f"  - Successfully Fetched: {total_fetched}")
    print(f"  - Already Existing (skipped): {total_skipped}")
    print(f"  - Failed downloads/processing: {total_failed}")
    print(f"Extraction log written to: {EXTRACTION_LOG_FILE}")
    print("=" * 40 + "\n")


if __name__ == '__main__':
    main()
