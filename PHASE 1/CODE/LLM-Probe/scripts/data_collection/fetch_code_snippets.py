import os
import re
import sys
import time
import urllib.parse
import logging
import requests
import json
from typing import List, Set

# Set up logging to stdout
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
TASKS_FILE = "data/memorization/raw/rosetta_tasks.txt"
CODE_SNIPPETS_JSONL = "data/memorization/raw/code_snippets.jsonl"
USER_AGENT = "LLMProbeResearchBot/1.0 (academic research; contact: project-llm-probe@example.com)"
RATE_LIMIT_DELAY = 0.5  # seconds


def sanitize_filename(title: str) -> str:
    """
    Sanitizes a task title to be a safe Windows filename/id.
    Replaces spaces with underscores and invalid chars with underscores.
    """
    # Keep only alphanumeric, spaces, hyphens, and underscores, replacing others with underscore
    clean = re.sub(r'[\\/*?:"<>|]', '_', title)
    clean = clean.replace(' ', '_')
    # Deduplicate underscores
    clean = re.sub(r'_+', '_', clean)
    return clean.strip('_')


def extract_python_section(wikitext: str) -> str:
    """
    Isolates the wikitext section for Python, stopping at the next section of equal or higher level.
    """
    header_match = re.search(r'^(==+)\s*(?:\{\{header\|)?[Pp]ython(?:\}\})?\s*==+', wikitext, re.MULTILINE)
    if not header_match:
        return ""
    
    header_level = len(header_match.group(1))
    start_pos = header_match.end()
    
    # Match any header of equal or higher level (fewer or equal '=' signs)
    pattern = r'^={1,' + str(header_level) + r'}[^=]'
    next_header_match = re.search(pattern, wikitext[start_pos:], re.MULTILINE)
    if next_header_match:
        return wikitext[start_pos : start_pos + next_header_match.start()]
    return wikitext[start_pos:]


def extract_code_blocks(section_text: str) -> List[str]:
    """
    Extracts all Python code blocks from the Python section text.
    Handles <lang python>, <syntaxhighlight lang="python">, and ```python markdown fences.
    """
    blocks = []
    
    # 1. <lang python>...</lang> (case insensitive)
    lang_pattern = re.compile(
        r'<lang\s+[^>]*python[^>]*>(.*?)</lang>',
        re.DOTALL | re.IGNORECASE
    )
    for match in lang_pattern.finditer(section_text):
        blocks.append(match.group(1).strip())
        
    # 2. <syntaxhighlight lang="python">...</syntaxhighlight> (case-insensitive)
    syntax_pattern = re.compile(
        r'<syntaxhighlight\s+[^>]*python[^>]*>(.*?)</syntaxhighlight>',
        re.DOTALL | re.IGNORECASE
    )
    for match in syntax_pattern.finditer(section_text):
        blocks.append(match.group(1).strip())
        
    # 3. ```python ... ``` (case-insensitive)
    fence_pattern = re.compile(
        r'```python\s*\n(.*?)\n```',
        re.DOTALL | re.IGNORECASE
    )
    for match in fence_pattern.finditer(section_text):
        blocks.append(match.group(1).strip())
        
    return [b for b in blocks if b]


def clean_code_block(code: str) -> str:
    """
    Strips wiki markup/comments and removes execution/driver code at the bottom.
    """
    # Remove HTML/wiki comments
    code = re.sub(r'<!--.*?-->', '', code, flags=re.DOTALL)
    
    lines = code.splitlines()
    
    # 1. Remove standard main blocks
    cutoff = len(lines)
    for i, line in enumerate(lines):
        if "__name__" in line and "__main__" in line:
            cutoff = i
            break
    lines = lines[:cutoff]
    
    # Trim trailing empty lines
    while lines and not lines[-1].strip():
        lines.pop()
        
    # 2. Trim trailing driver code/print statements at 0-indentation at the bottom
    has_defs = any(line.startswith(("def ", "class ")) for line in lines)
    if has_defs:
        last_valid = 0
        for i in range(len(lines)):
            line = lines[i]
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if line.startswith(("def ", "class ", "import ", "from ", "@")):
                last_valid = i
            elif line[0].isspace():
                last_valid = i
        lines = lines[:last_valid + 1]
        
    return "\n".join(lines).strip()


def select_best_block(cleaned_blocks: List[str]) -> str:
    """
    Selects the best fitting Python block aiming for 20-60 lines.
    Falls back to smaller/larger blocks and truncates to 60 lines if necessary.
    """
    if not cleaned_blocks:
        return ""
        
    # Priority 1: Ideal 20-60 line range
    for block in cleaned_blocks:
        line_count = len(block.splitlines())
        if 20 <= line_count <= 60:
            return block
            
    # Priority 2: 15-80 line range
    for block in cleaned_blocks:
        line_count = len(block.splitlines())
        if 15 <= line_count <= 80:
            if line_count > 60:
                return "\n".join(block.splitlines()[:60])
            return block
            
    # Priority 3: 10+ lines
    for block in cleaned_blocks:
        line_count = len(block.splitlines())
        if line_count >= 10:
            if line_count > 60:
                return "\n".join(block.splitlines()[:60])
            return block
            
    # Fallback: First block, truncated if > 60 lines
    first_block = cleaned_blocks[0]
    lines = first_block.splitlines()
    if len(lines) > 60:
        return "\n".join(lines[:60])
    return first_block


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fetch Rosetta Code Python snippets.")
    parser.add_argument("--start", type=int, default=1, help="Start line index (1-based, inclusive)")
    parser.add_argument("--end", type=int, default=None, help="End line index (1-based, inclusive)")
    args = parser.parse_args()

    logger.info("=== Starting Rosetta Code Snippet Fetching Utility ===")
    
    # 1. Setup Directories
    os.makedirs(os.path.dirname(CODE_SNIPPETS_JSONL), exist_ok=True)
    
    if not os.path.exists(TASKS_FILE):
        logger.error(f"Tasks file not found at: {TASKS_FILE}")
        sys.exit(1)
        
    # 2. Read Tasks
    with open(TASKS_FILE, "r", encoding="utf-8") as f:
        tasks = [line.strip() for line in f if line.strip()]
        
    original_count = len(tasks)
    start_idx = max(1, args.start) - 1
    end_idx = args.end if args.end is not None else original_count
    sliced_tasks = tasks[start_idx:end_idx]
    
    logger.info(
        f"Loaded {original_count} tasks. "
        f"Processing slice from index {args.start} to {end_idx} (total {len(sliced_tasks)} tasks)."
    )
    
    # Load existing IDs from JSONL for resumability
    existing_ids = set()
    if os.path.exists(CODE_SNIPPETS_JSONL):
        with open(CODE_SNIPPETS_JSONL, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        item = json.loads(line)
                        if "id" in item:
                            existing_ids.add(item["id"])
                    except Exception:
                        pass
        logger.info(f"Loaded {len(existing_ids)} already existing IDs from {CODE_SNIPPETS_JSONL}")

    # Metrics counters
    total_fetched = 0
    total_skipped_no_python = 0
    total_skipped_no_valid_code = 0
    total_already_existing = 0
    total_failed_404 = 0
    total_failed_network = 0
    total_failed_other = 0
    
    headers = {
        "User-Agent": USER_AGENT
    }
    
    # 3. Process each task
    for idx, task in enumerate(sliced_tasks, 1):
        sanitized = sanitize_filename(task)
        
        # Resumability check
        if sanitized in existing_ids:
            logger.info(f"[{idx}/{len(sliced_tasks)}] [EXISTING] Skipping '{task}' (ID already exists: {sanitized})")
            total_already_existing += 1
            continue
            
        encoded_title = urllib.parse.quote(task)
        url = f"https://rosettacode.org/w/api.php?action=parse&page={encoded_title}&format=json&prop=wikitext"
        
        try:
            logger.info(f"[{idx}/{len(sliced_tasks)}] [FETCHING] Getting wikitext for '{task}'...")
            response = requests.get(url, headers=headers, timeout=15)
            
            # Rate limiting
            time.sleep(RATE_LIMIT_DELAY)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if the page exists/failed to parse
                if "error" in data:
                    err_code = data["error"].get("code", "unknown")
                    if err_code == "missingtitle":
                        logger.error(f"[{idx}/{len(sliced_tasks)}] [FAIL] 404 Not Found for task '{task}'.")
                        total_failed_404 += 1
                    else:
                        logger.error(f"[{idx}/{len(sliced_tasks)}] [FAIL] API Error '{err_code}': {data['error'].get('info')}")
                        total_failed_other += 1
                    continue
                    
                wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")
                if not wikitext:
                    logger.warning(f"[{idx}/{len(sliced_tasks)}] [SKIP] Page for '{task}' has empty content.")
                    total_skipped_no_valid_code += 1
                    continue
                    
                # Isolate Python section
                python_section = extract_python_section(wikitext)
                if not python_section.strip():
                    logger.warning(f"[{idx}/{len(sliced_tasks)}] [SKIP] '{task}' has no Python section.")
                    total_skipped_no_python += 1
                    continue
                    
                # Extract code blocks
                raw_blocks = extract_code_blocks(python_section)
                if not raw_blocks:
                    logger.warning(f"[{idx}/{len(sliced_tasks)}] [SKIP] Could not find structured python tags in '{task}'.")
                    total_skipped_no_valid_code += 1
                    continue
                    
                # Clean blocks and select the best fit
                cleaned_blocks = [clean_code_block(b) for b in raw_blocks]
                cleaned_blocks = [b for b in cleaned_blocks if b]
                
                selected_code = select_best_block(cleaned_blocks)
                if not selected_code.strip():
                    logger.warning(f"[{idx}/{len(sliced_tasks)}] [SKIP] Extracted code blocks for '{task}' were empty after cleaning.")
                    total_skipped_no_valid_code += 1
                    continue
                    
                # Append to JSONL
                with open(CODE_SNIPPETS_JSONL, "a", encoding="utf-8") as out_f:
                    item = {
                        "id": sanitized,
                        "content": selected_code,
                        "source_category": "code_snippets"
                    }
                    out_f.write(json.dumps(item, ensure_ascii=False) + "\n")
                    
                existing_ids.add(sanitized)
                
                word_count = len(selected_code.split())
                line_count = len(selected_code.splitlines())
                logger.info(f"[{idx}/{len(sliced_tasks)}] [SUCCESS] Saved '{task}' ({line_count} lines, {word_count} words) to JSONL")
                total_fetched += 1
                
            else:
                logger.error(f"[{idx}/{len(sliced_tasks)}] [FAIL] HTTP {response.status_code} for task '{task}'.")
                total_failed_other += 1
                
        except requests.RequestException as e:
            logger.error(f"[{idx}/{len(sliced_tasks)}] [ERROR] Request failed for task '{task}': {e}")
            total_failed_network += 1
            time.sleep(RATE_LIMIT_DELAY)
        except Exception as e:
            logger.error(f"[{idx}/{len(sliced_tasks)}] [ERROR] Unexpected error processing '{task}': {e}")
            total_failed_other += 1
            
    # Final Reporting
    total_skipped = total_skipped_no_python + total_skipped_no_valid_code
    total_failures = total_failed_404 + total_failed_network + total_failed_other
    print("\n" + "=" * 40)
    print(" ROSETTA CODE SNIPPETS FETCH COMPLETE")
    print("=" * 40)
    print(f"Total Tasks Configured: {len(sliced_tasks)}")
    print(f"  - Already Existing (skipped): {total_already_existing}")
    print(f"  - Successfully Fetched:       {total_fetched}")
    print(f"  - Skipped (no Python):        {total_skipped_no_python}")
    print(f"  - Skipped (no valid code):    {total_skipped_no_valid_code}")
    print(f"  - Total Failed:               {total_failures}")
    print(f"    * 404 Not Found:            {total_failed_404}")
    print(f"    * Network Errors:           {total_failed_network}")
    print(f"    * Other Errors:             {total_failed_other}")
    print("=" * 40 + "\n")


if __name__ == '__main__':
    main()
