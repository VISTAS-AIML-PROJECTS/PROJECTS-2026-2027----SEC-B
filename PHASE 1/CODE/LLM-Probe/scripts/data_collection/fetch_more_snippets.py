import os
import re
import sys
import time
import urllib.parse
import logging
import requests
import json
from typing import List, Set

# Include parent workspace folder in path for llm_probe imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from llm_probe.config import MODEL_NAME
from llm_probe.models.loader import load_tokenizer

# Set up logging to stdout
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
CODE_SNIPPETS_JSONL = "data/memorization/raw/code_snippets.jsonl"
USER_AGENT = "LLMProbeResearchBot/1.0 (academic research; contact: project-llm-probe@example.com)"
RATE_LIMIT_DELAY = 0.5  # seconds
TARGET_VALID_COUNT = 300


def sanitize_filename(title: str) -> str:
    """
    Sanitizes a task title to be a safe Windows filename/id.
    """
    clean = re.sub(r'[\\/*?:"<>|]', '_', title)
    clean = clean.replace(' ', '_')
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
    
    pattern = r'^={1,' + str(header_level) + r'}[^=]'
    next_header_match = re.search(pattern, wikitext[start_pos:], re.MULTILINE)
    if next_header_match:
        return wikitext[start_pos : start_pos + next_header_match.start()]
    return wikitext[start_pos:]


def extract_code_blocks(section_text: str) -> List[str]:
    """
    Extracts all Python code blocks from the Python section text.
    """
    blocks = []
    lang_pattern = re.compile(r'<lang\s+[^>]*python[^>]*>(.*?)</lang>', re.DOTALL | re.IGNORECASE)
    for match in lang_pattern.finditer(section_text):
        blocks.append(match.group(1).strip())
        
    syntax_pattern = re.compile(r'<syntaxhighlight\s+[^>]*python[^>]*>(.*?)</syntaxhighlight>', re.DOTALL | re.IGNORECASE)
    for match in syntax_pattern.finditer(section_text):
        blocks.append(match.group(1).strip())
        
    fence_pattern = re.compile(r'```python\s*\n(.*?)\n```', re.DOTALL | re.IGNORECASE)
    for match in fence_pattern.finditer(section_text):
        blocks.append(match.group(1).strip())
        
    return [b for b in blocks if b]


def clean_code_block(code: str) -> str:
    """
    Strips wiki markup/comments and removes execution/driver code at the bottom.
    """
    code = re.sub(r'<!--.*?-->', '', code, flags=re.DOTALL)
    lines = code.splitlines()
    
    cutoff = len(lines)
    for i, line in enumerate(lines):
        if "__name__" in line and "__main__" in line:
            cutoff = i
            break
    lines = lines[:cutoff]
    
    while lines and not lines[-1].strip():
        lines.pop()
        
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
    """
    if not cleaned_blocks:
        return ""
    for block in cleaned_blocks:
        line_count = len(block.splitlines())
        if 20 <= line_count <= 60:
            return block
    for block in cleaned_blocks:
        line_count = len(block.splitlines())
        if 15 <= line_count <= 80:
            if line_count > 60:
                return "\n".join(block.splitlines()[:60])
            return block
    for block in cleaned_blocks:
        line_count = len(block.splitlines())
        if line_count >= 10:
            if line_count > 60:
                return "\n".join(block.splitlines()[:60])
            return block
    first_block = cleaned_blocks[0]
    lines = first_block.splitlines()
    if len(lines) > 60:
        return "\n".join(lines[:60])
    return first_block


def count_valid_files(tokenizer) -> Set[str]:
    """
    Scans the JSONL file and returns the set of snippet IDs that have >= 50 tokens.
    """
    valid_files = set()
    if not os.path.exists(CODE_SNIPPETS_JSONL):
        return valid_files
        
    with open(CODE_SNIPPETS_JSONL, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    item = json.loads(line)
                    content = item.get("content", "").strip()
                    tokens = tokenizer.encode(content, add_special_tokens=False)
                    if len(tokens) >= 50:
                        valid_files.add(item["id"])
                except Exception as e:
                    logger.error(f"Error parsing line during token count check: {e}")
            
    return valid_files


def fetch_category_members(cmcontinue: str = None) -> tuple:
    """
    Queries the Category:Python members from Rosetta Code API.
    """
    url = "https://rosettacode.org/w/api.php"
    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": "Category:Python",
        "cmlimit": "500",
        "format": "json"
    }
    if cmcontinue:
        params["cmcontinue"] = cmcontinue
        
    headers = {"User-Agent": USER_AGENT}
    response = requests.get(url, params=params, headers=headers, timeout=15)
    response.raise_for_status()
    data = response.json()
    
    members = data.get("query", {}).get("categorymembers", [])
    next_continue = data.get("continue", {}).get("cmcontinue", None)
    return members, next_continue


def main():
    logger.info("=== Starting Rosetta Code Supplementary Fetching to Reach 300 Code Snippets ===")
    
    # 1. Initialize tokenizer
    logger.info(f"Loading tokenizer '{MODEL_NAME}' to verify token counts...")
    tokenizer = load_tokenizer(MODEL_NAME)
    
    # 2. Count current valid files from JSONL
    valid_files = count_valid_files(tokenizer)
    current_valid_count = len(valid_files)
    logger.info(f"Current valid files count (>= 50 tokens): {current_valid_count} / {TARGET_VALID_COUNT}")
    
    # Load all existing IDs for check
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

    if current_valid_count >= TARGET_VALID_COUNT:
        logger.info("We have already reached the target of 300 valid code snippets! Exiting.")
        return
        
    # 3. Setup continue params for category pagination
    cmcontinue = None
    fetched_in_this_run = 0
    headers = {"User-Agent": USER_AGENT}
    
    while current_valid_count < TARGET_VALID_COUNT:
        logger.info("Fetching Category:Python members from API...")
        members, cmcontinue = fetch_category_members(cmcontinue)
        time.sleep(RATE_LIMIT_DELAY)
        
        if not members:
            logger.error("No category members returned. Rosetta Code might be fully parsed. Exiting.")
            break
            
        for member in members:
            if current_valid_count >= TARGET_VALID_COUNT:
                break
                
            if member.get("ns") != 0:
                continue
                
            title = member.get("title", "")
            sanitized = sanitize_filename(title)
            
            # Check if already exists in JSONL
            if sanitized in existing_ids:
                continue
                
            # Fetch this task
            encoded_title = urllib.parse.quote(title)
            task_url = f"https://rosettacode.org/w/api.php?action=parse&page={encoded_title}&format=json&prop=wikitext"
            
            try:
                logger.info(f"[FETCHING] Getting '{title}'...")
                resp = requests.get(task_url, headers=headers, timeout=15)
                time.sleep(RATE_LIMIT_DELAY)
                
                if resp.status_code != 200:
                    logger.error(f"[FAIL] HTTP {resp.status_code} for '{title}'")
                    continue
                    
                data = resp.json()
                if "error" in data:
                    continue
                    
                wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")
                if not wikitext:
                    continue
                    
                python_section = extract_python_section(wikitext)
                if not python_section.strip():
                    continue
                    
                raw_blocks = extract_code_blocks(python_section)
                if not raw_blocks:
                    continue
                    
                cleaned_blocks = [clean_code_block(b) for b in raw_blocks]
                cleaned_blocks = [b for b in cleaned_blocks if b]
                selected_code = select_best_block(cleaned_blocks)
                
                if not selected_code.strip():
                    continue
                    
                # Verify token count BEFORE saving
                tokens = tokenizer.encode(selected_code, add_special_tokens=False)
                token_len = len(tokens)
                
                if token_len >= 50:
                    # Append to JSONL
                    with open(CODE_SNIPPETS_JSONL, "a", encoding="utf-8") as out_f:
                        item = {
                            "id": sanitized,
                            "content": selected_code,
                            "source_category": "code_snippets"
                        }
                        out_f.write(json.dumps(item, ensure_ascii=False) + "\n")
                        
                    existing_ids.add(sanitized)
                    current_valid_count += 1
                    fetched_in_this_run += 1
                    line_count = len(selected_code.splitlines())
                    logger.info(f"[SUCCESS] Saved '{title}' ({line_count} lines, {token_len} tokens). Current valid total: {current_valid_count}/{TARGET_VALID_COUNT}")
                else:
                    logger.info(f"[SKIP] '{title}' code snippet is too short ({token_len} tokens, min 50 required)")
                    
            except Exception as e:
                logger.error(f"Error fetching/processing '{title}': {e}")
                time.sleep(RATE_LIMIT_DELAY)
                
        if not cmcontinue:
            logger.info("Reached the end of Category:Python members.")
            break
            
    logger.info("=" * 40)
    logger.info(" RECONCILIATION SUMMARY")
    logger.info("=" * 40)
    logger.info(f"Total Valid Code Snippets: {current_valid_count} / {TARGET_VALID_COUNT}")
    logger.info(f"Fetched in this run:       {fetched_in_this_run}")
    logger.info("=" * 40)


if __name__ == '__main__':
    main()
