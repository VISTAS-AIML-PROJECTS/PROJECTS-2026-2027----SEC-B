"""
CLI Rendering Utilities for LLM Probe Live Inference.
Provides ANSI color-coded token display and dual-probe execution summaries.
"""

# ANSI Color Codes
CYAN = "\033[96m"
BOLD_CYAN = "\033[1;96m"
RED = "\033[91m"
BOLD_RED = "\033[1;91m"
YELLOW = "\033[93m"
BOLD_YELLOW = "\033[1;93m"
GREEN = "\033[92m"
BOLD_GREEN = "\033[1;92m"
GRAY = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"


def get_risk_level_str(max_score):
    """Returns ANSI formatted risk level string based on max score."""
    if max_score >= 0.6:
        return f"{BOLD_RED}HIGH{RESET}"
    elif max_score >= 0.3:
        return f"{BOLD_YELLOW}MEDIUM{RESET}"
    else:
        return f"{BOLD_GREEN}LOW{RESET}"


def format_colored_score(tag, score):
    """Formats a single score with ANSI color coding."""
    if score >= 0.6:
        return f"{BOLD_RED}{tag}:{score:.2f}{RESET}"
    elif score >= 0.3:
        return f"{BOLD_YELLOW}{tag}:{score:.2f}{RESET}"
    else:
        return f"{GREEN}{tag}:{score:.2f}{RESET}"


def render_ascii_graph(scores, label, width=50):
    """
    Renders a Unicode block bar chart of scores over token positions.

    Three data rows aligned to risk thresholds (0.30, 0.60, 0.90) plus a
    zero baseline. For sequences longer than `width` tokens, scores are
    averaged into buckets so the chart never exceeds `width` columns.
    No external dependencies; uses Unicode block elements only.

    Args:
        scores: list of float scores in [0, 1]
        label:  chart title string
        width:  maximum number of display columns (default 50)
    """
    if not scores:
        return

    n = len(scores)
    blocks = " ▁▂▃▄▅▆▇█"

    # Compress long sequences into at most `width` display columns
    if n > width:
        bucket_size = n / width
        display = []
        for i in range(width):
            start = int(i * bucket_size)
            end = min(int((i + 1) * bucket_size), n)
            if end <= start:
                end = start + 1
            bucket = scores[start:end]
            display.append(sum(bucket) / len(bucket))
        n_display = width
    else:
        display = list(scores)
        n_display = n

    print(f"\n{BOLD}{label}{RESET}")

    # Three data rows, each covering a risk-threshold-aligned band
    row_bands = [
        (0.90, 1.00),
        (0.60, 0.90),
        (0.30, 0.60),
    ]
    for row_low, row_high in row_bands:
        chars = []
        for s in display:
            if s < row_low:
                chars.append(" ")
            elif s >= row_high:
                chars.append("█")
            else:
                frac = (s - row_low) / (row_high - row_low)
                idx = max(1, min(8, round(frac * 8)))
                chars.append(blocks[idx])
        print(f"  {row_low:.2f} ┤{''.join(chars)}")

    # Baseline (x-axis)
    print(f"  0.00 ┼{'─' * n_display}")

    # Token-range footer (aligned with data rows; prefix is 8 chars wide)
    end_label = str(n)
    start_label = "1"
    pad = max(0, n_display - len(start_label) - len(end_label))
    print(f"        {start_label}{' ' * pad}{end_label}")


def render_terminal(results, task="both", token_counts=None):
    """
    Renders the LLM Probe demo output in five sections:
      1. Clean generated answer (no inline risk annotations)
      2. Overall probe summary (risk level, avg/max per probe)
      3. Generation information (token counts, EOS vs limit status)
      4. Detailed per-token analysis table
      5. Risk-over-generation ASCII bar charts

    Args:
        results:      list of dicts with 'token', 'mem_score' and/or 'halluc_score'
        task:         'both', 'memorization', or 'hallucination'
        token_counts: dict with 'prompt_tokens', 'generated_tokens',
                      'total_tokens', 'max_tokens'
    """
    if not results:
        print(f"{YELLOW}No tokens generated.{RESET}")
        return

    has_mem = (
        any("mem_score" in item or "score" in item for item in results)
        and task != "hallucination"
    )
    has_halluc = (
        any("halluc_score" in item for item in results)
        and task != "memorization"
    )

    # Collect scores once; used by summary, table, and graphs
    mem_scores = []
    halluc_scores = []
    for item in results:
        if has_mem:
            s = item.get("mem_score", item.get("score"))
            if s is not None:
                mem_scores.append(float(s))
        if has_halluc:
            s = item.get("halluc_score")
            if s is not None:
                halluc_scores.append(float(s))

    width = 62

    # ── Section 1: Clean Generated Answer ──────────────────────────────
    print(f"\n{BOLD_CYAN}=== Generated Answer ==={RESET}\n")
    generated_text = (token_counts or {}).get("generated_text")
    if generated_text is not None:
        print(generated_text)
    else:
        for item in results:
            print(item.get("token", ""), end="")
    print("\n")

    # ── Section 2 & 3: Probe Summary + Generation Info ─────────────────
    print(f"{CYAN}{'=' * width}{RESET}")
    print(f"{BOLD_CYAN}{'PROBE SUMMARY':^{width}}{RESET}")
    print(f"{CYAN}{'=' * width}{RESET}")

    # Generation / token info
    gen_cnt = len(results)
    if token_counts:
        gen_cnt = token_counts.get("generated_tokens", len(results))
        max_limit = token_counts.get("max_tokens")
        prompt_cnt = token_counts.get("prompt_tokens")
        if max_limit and gen_cnt >= max_limit:
            status_str = f"Token Limit Reached ({max_limit})"
        else:
            status_str = "EOS Reached"
        print(f"  {BOLD}Generated{RESET}  : {BOLD_CYAN}{gen_cnt} tokens{RESET}  [{status_str}]")
        if prompt_cnt is not None:
            print(f"  {BOLD}Prompt{RESET}     : {prompt_cnt} tokens")
    else:
        print(f"  {BOLD}Generated{RESET}  : {BOLD_CYAN}{gen_cnt} tokens{RESET}")

    # Memorization probe stats
    if has_mem and mem_scores:
        mem_max = max(mem_scores)
        mem_avg = sum(mem_scores) / len(mem_scores)
        print(f"{GRAY}{'-' * width}{RESET}")
        print(f"  {BOLD}MEMORIZATION{RESET}")
        print(f"    Risk Level : {get_risk_level_str(mem_max)}")
        print(f"    Avg Score  : {mem_avg:.4f}")
        print(f"    Max Score  : {mem_max:.4f}")

    # Hallucination probe stats
    if has_halluc and halluc_scores:
        halluc_max = max(halluc_scores)
        halluc_avg = sum(halluc_scores) / len(halluc_scores)
        print(f"{GRAY}{'-' * width}{RESET}")
        print(f"  {BOLD}HALLUCINATION{RESET}")
        print(f"    Risk Level : {get_risk_level_str(halluc_max)}")
        print(f"    Avg Score  : {halluc_avg:.4f}")
        print(f"    Max Score  : {halluc_max:.4f}")

    print(f"{CYAN}{'=' * width}{RESET}")

    # ── Section 4: Detailed Token Analysis ────────────────────────────
    print(f"\n{BOLD}{'─' * width}{RESET}")
    print(f"{BOLD}  Detailed Token Analysis{RESET}")
    print(f"{BOLD}{'─' * width}{RESET}")

    tok_width = 20  # visible display width for the token column

    # Header row
    if has_mem and has_halluc:
        print(f"{GRAY}  {'#':>4}  {'Token':<{tok_width}}  {'Mem':>6}  {'Hall':>6}{RESET}")
        print(f"{GRAY}  {'─'*4}  {'─'*tok_width}  {'─'*6}  {'─'*6}{RESET}")
    elif has_mem:
        print(f"{GRAY}  {'#':>4}  {'Token':<{tok_width}}  {'Mem':>6}{RESET}")
        print(f"{GRAY}  {'─'*4}  {'─'*tok_width}  {'─'*6}{RESET}")
    else:
        print(f"{GRAY}  {'#':>4}  {'Token':<{tok_width}}  {'Hall':>6}{RESET}")
        print(f"{GRAY}  {'─'*4}  {'─'*tok_width}  {'─'*6}{RESET}")

    for i, item in enumerate(results, 1):
        raw_token = item.get("token", "")

        # Sanitize token for table display only; never alters the answer output
        display_tok = (
            raw_token
            .replace("\n", "\\n")
            .replace("\r", "\\r")
            .replace("\t", "\\t")
        )
        display_tok = "".join(c if c.isprintable() else "?" for c in display_tok)
        if len(display_tok) > tok_width:
            display_tok = display_tok[:tok_width - 1] + "…"

        idx_str = f"{i:>4}"
        tok_str = f"{display_tok:<{tok_width}}"

        if has_mem and has_halluc:
            mem_s = float(item.get("mem_score", item.get("score", 0.0)))
            hall_s = float(item.get("halluc_score", 0.0))
            print(f"  {idx_str}  {tok_str}  {format_colored_score('M', mem_s)}  {format_colored_score('H', hall_s)}")
        elif has_mem:
            mem_s = float(item.get("mem_score", item.get("score", 0.0)))
            print(f"  {idx_str}  {tok_str}  {format_colored_score('M', mem_s)}")
        else:
            hall_s = float(item.get("halluc_score", 0.0))
            print(f"  {idx_str}  {tok_str}  {format_colored_score('H', hall_s)}")

    print(f"{GRAY}{'─' * width}{RESET}")

    # ── Section 5: Risk-over-generation graphs ─────────────────────────
    if has_mem and mem_scores:
        render_ascii_graph(mem_scores, "Memorization Risk Over Generation")
    if has_halluc and halluc_scores:
        render_ascii_graph(halluc_scores, "Hallucination Risk Over Generation")
