"""
LLM Probe - Command-Line Interface (CLI) Entry Point.
Live token-by-token inference for memorization and hallucination detection.

Usage:
  # Launch Interactive REPL session:
  python cli.py

  # Single prompt memorization check:
  python cli.py --task memorization --prompt "Alice was beginning to get very tired..."

  # Single prompt hallucination check:
  python cli.py --task hallucination --prompt "Can you catch a cold from being cold?"
"""

import sys

from demo.inference import main

if __name__ == "__main__":
    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    main()
