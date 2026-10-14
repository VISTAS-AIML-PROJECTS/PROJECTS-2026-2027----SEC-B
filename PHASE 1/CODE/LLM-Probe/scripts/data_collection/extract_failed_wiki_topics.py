import re
import os

LOG_FILE = r"C:\Users\Jai\.gemini\antigravity-ide\brain\01e11fd1-59e6-4238-a512-f43287c58b81\.system_generated\tasks\task-458.log"
OUTPUT_FILE = "data/memorization/raw/wiki_failed_topics.txt"

def main():
    if not os.path.exists(LOG_FILE):
        print(f"Log file not found: {LOG_FILE}")
        return
        
    failed_topics = []
    
    # Example line: 2026-07-25 18:50:45,977 - ERROR - [18/500] [FAIL] 404 Not Found for topic 'Model poisoning'. Check if spelling matches Wikipedia.
    fail_pattern = re.compile(r"\[FAIL\].*topic '([^']+)'")
    
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            match = fail_pattern.search(line)
            if match:
                failed_topics.append(match.group(1))
                
    print(f"Extracted {len(failed_topics)} failed topics from log.")
    
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for topic in failed_topics:
            f.write(topic + "\n")
            
    print(f"Saved failed topics list to: {OUTPUT_FILE}")

if __name__ == '__main__':
    main()
