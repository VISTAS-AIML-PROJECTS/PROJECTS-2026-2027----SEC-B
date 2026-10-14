import os
import re
import sys
import time
import urllib.parse
import logging
import requests
import json
from typing import Set

# Set up logging to stdout
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
TOPICS_FILE = "data/memorization/raw/wiki_topics.txt"
WIKI_LEADS_JSONL = "data/memorization/raw/wiki_leads.jsonl"
USER_AGENT = "LLMProbeResearchBot/1.0 (academic research; contact: project-llm-probe@example.com)"
RATE_LIMIT_DELAY = 0.5  # seconds
MIN_WORD_COUNT = 30


def sanitize_filename(title: str) -> str:
    """
    Sanitizes a page title to be a safe Windows filename/id.
    Replaces spaces with underscores and invalid chars with underscores.
    """
    clean = re.sub(r'[\\/*?:"<>|]', '_', title)
    clean = clean.replace(' ', '_')
    clean = re.sub(r'_+', '_', clean)
    return clean.strip('_')


def clean_summary_text(text: str) -> str:
    """
    Collapses whitespace and strips citation brackets (e.g., [1], [citation needed]).
    """
    cleaned = re.sub(r'\s+', ' ', text).strip()
    cleaned = re.sub(r'\[\d+\]', '', cleaned)
    cleaned = re.sub(r'\[citation needed\]', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fetch Wikipedia lead paragraphs.")
    parser.add_argument("--start", type=int, default=1, help="Start line index (1-based, inclusive)")
    parser.add_argument("--end", type=int, default=None, help="End line index (1-based, inclusive)")
    args = parser.parse_args()

    logger.info("=== Starting Wikipedia Lead Paragraph Fetching Utility ===")
    
    # 1. Setup Directories
    os.makedirs(os.path.dirname(WIKI_LEADS_JSONL), exist_ok=True)
    
    if not os.path.exists(TOPICS_FILE):
        logger.error(f"Topics file not found at: {TOPICS_FILE}")
        sys.exit(1)
        
    # 2. Read Topics
    with open(TOPICS_FILE, "r", encoding="utf-8") as f:
        topics = [line.strip() for line in f if line.strip()]
        
    original_count = len(topics)
    start_idx = max(1, args.start) - 1
    end_idx = args.end if args.end is not None else original_count
    sliced_topics = topics[start_idx:end_idx]
    
    logger.info(
        f"Loaded {original_count} topics. "
        f"Processing slice from index {args.start} to {end_idx} (total {len(sliced_topics)} topics)."
    )
    
    # Load existing IDs from JSONL for resumability
    existing_ids = set()
    if os.path.exists(WIKI_LEADS_JSONL):
        with open(WIKI_LEADS_JSONL, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        item = json.loads(line)
                        if "id" in item:
                            existing_ids.add(item["id"])
                    except Exception:
                        pass
        logger.info(f"Loaded {len(existing_ids)} already existing IDs from {WIKI_LEADS_JSONL}")

    # Counter metrics
    total_fetched = 0
    total_skipped_too_short = 0
    total_skipped_disambiguation = 0
    total_already_existing = 0
    total_failed_404 = 0
    total_failed_429 = 0
    total_failed_other_http = 0
    total_failed_network = 0
    
    headers = {
        "User-Agent": USER_AGENT
    }
    
    # 3. Process each topic
    for idx, topic in enumerate(sliced_topics, 1):
        sanitized = sanitize_filename(topic)
        
        # Resumability check
        if sanitized in existing_ids:
            logger.info(f"[{idx}/{len(sliced_topics)}] [EXISTING] Skipping '{topic}' (ID already exists: {sanitized})")
            total_already_existing += 1
            continue
            
        encoded_title = urllib.parse.quote(topic.replace(' ', '_'))
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_title}"
        
        try:
            logger.info(f"[{idx}/{len(sliced_topics)}] [FETCHING] Getting summary for '{topic}'...")
            response = requests.get(url, headers=headers, timeout=10)
            
            # Rate limiting
            time.sleep(RATE_LIMIT_DELAY)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for disambiguation page
                page_type = data.get("type", "standard")
                if page_type == "disambiguation":
                    logger.warning(f"[{idx}/{len(sliced_topics)}] [SKIP] '{topic}' resolved to a disambiguation page. Skipping.")
                    total_skipped_disambiguation += 1
                    continue
                    
                extract = data.get("extract", "")
                cleaned_text = clean_summary_text(extract)
                
                # Check word count
                word_count = len(cleaned_text.split())
                if word_count < MIN_WORD_COUNT:
                    logger.warning(
                        f"[{idx}/{len(sliced_topics)}] [SKIP] Summary for '{topic}' is too short "
                        f"({word_count} words, min {MIN_WORD_COUNT} required). Skipping."
                    )
                    total_skipped_too_short += 1
                    continue
                    
                # Append to JSONL file
                with open(WIKI_LEADS_JSONL, "a", encoding="utf-8") as out_f:
                    item = {
                        "id": sanitized,
                        "content": cleaned_text,
                        "source_category": "wiki_leads"
                    }
                    out_f.write(json.dumps(item, ensure_ascii=False) + "\n")
                    
                existing_ids.add(sanitized)
                logger.info(f"[{idx}/{len(sliced_topics)}] [SUCCESS] Saved '{topic}' summary ({word_count} words) to JSONL")
                total_fetched += 1
                
            elif response.status_code == 404:
                logger.error(f"[{idx}/{len(sliced_topics)}] [FAIL] 404 Not Found for topic '{topic}'. Check if spelling matches Wikipedia.")
                total_failed_404 += 1
            elif response.status_code == 429:
                logger.error(f"[{idx}/{len(sliced_topics)}] [FAIL] 429 Too Many Requests (Rate Limited) for topic '{topic}'.")
                total_failed_429 += 1
            else:
                logger.error(f"[{idx}/{len(sliced_topics)}] [FAIL] HTTP {response.status_code} for topic '{topic}'.")
                total_failed_other_http += 1
                
        except requests.RequestException as e:
            logger.error(f"[{idx}/{len(sliced_topics)}] [ERROR] Request failed for topic '{topic}': {e}")
            total_failed_network += 1
            time.sleep(RATE_LIMIT_DELAY)
            
    # Final Reporting
    total_failures = total_failed_404 + total_failed_429 + total_failed_other_http + total_failed_network
    print("\n" + "=" * 40)
    print(" WIKIPEDIA LEAD FETCH COMPLETE")
    print("=" * 40)
    print(f"Total Topics Configured: {len(sliced_topics)}")
    print(f"  - Already Existing (skipped): {total_already_existing}")
    print(f"  - Successfully Fetched:       {total_fetched}")
    print(f"  - Skipped (disambiguation):   {total_skipped_disambiguation}")
    print(f"  - Skipped (too short):        {total_skipped_too_short}")
    print(f"  - Total Failed:               {total_failures}")
    print(f"    * 404 Not Found:            {total_failed_404}")
    print(f"    * 429 Rate Limited:         {total_failed_429}")
    print(f"    * Other HTTP Errors:        {total_failed_other_http}")
    print(f"    * Network/Timeout Errors:   {total_failed_network}")
    print("=" * 40 + "\n")


if __name__ == '__main__':
    main()
