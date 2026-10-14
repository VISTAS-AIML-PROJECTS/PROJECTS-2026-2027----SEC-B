# LLM Probe — Final Year Project Report

**Author**: Jai-080  
**Model Under Study**: microsoft/Phi-3-mini-4k-instruct  
**Date**: September 2026

---

## 1. Overview

LLM Probe is a research system that detects two distinct failure modes in large language models (LLMs) — **memorization** and **hallucination** — by examining the model's internal transformer activations rather than relying on external databases or fact-checking APIs. Two linear probes (classifiers trained on hidden states) are deployed simultaneously during autoregressive generation, producing a per-token risk score rendered live in the terminal.

The project is structured as an end-to-end pipeline: raw data collection → labelled dataset construction → activation extraction → layer selection → probe training → evaluation → live CLI inference.

---

## 2. Repository Structure

```
LLM Probe/
├── src/
│   └── llm_probe/           # Core Python library (installable package)
│       ├── config.py
│       ├── verify_setup.py
│       ├── models/loader.py
│       └── core/
│           ├── activations.py
│           ├── layer_selection.py
│           └── probe.py
├── scripts/
│   ├── data_collection/     # Wikipedia, Gutenberg, GitHub scrapers
│   ├── probe_1_memorization/
│   │   ├── build_prefix_activations_memorization.py
│   │   └── train_memorization_probe_prefix_k5.py
│   └── probe_2_hallucination/
│       ├── build_prefix_activations_hallucination.py
│       └── train_hallucination_probe_prefix_k5.py
├── demo/
│   ├── inference.py         # Autoregressive dual-probe inference
│   └── render.py            # ANSI terminal renderer
├── data/
│   ├── memorization/        # Raw sources + labelled parquet
│   └── hallucination/       # TruthfulQA-derived parquet + review CSVs
├── results/
│   ├── memorization/        # probe.joblib, layer_rankings.png, reports
│   └── hallucination/       # probe.joblib, layer_rankings.png, reports
├── cli.py                   # Entry point (REPL and single-prompt modes)
├── requirements.txt
└── pyproject.toml
```

---

## 3. Model & Infrastructure

| Item | Value |
|---|---|
| Base model | Phi-3-mini-4k-instruct (3.8B parameters) |
| Quantization | 4-bit NF4 (bitsandbytes) |
| VRAM footprint | ~6 GB |
| Transformer layers | 32 (+ embedding layer = 33 total) |
| Hidden dimension | 3,072 per layer |
| Device | CUDA (CPU fallback) |

Phi-3 is loaded once at inference time from the Hugging Face Hub; no large weights are stored in the repository. Only the lightweight probe files (~290 KB each) are committed.

---

## 4. Probe 1 — Memorization Detection

### 4.1 Goal

Identify when the model reproduces verbatim fragments of its training data.

### 4.2 Dataset Construction

**Sources**:
- Wikipedia lead paragraphs (scraped via `fetch_wiki_leads.py`)
- Project Gutenberg book openings (`fetch_book_openings.py`)
- GitHub code snippets (`fetch_code_snippets.py`)

**Labelling**: Phi-3 is prompted with the first portion of a known text. Its generated continuation is scored with ROUGE-L against the true continuation:
- ROUGE-L > 0.70 → **memorized** (label 1)
- ROUGE-L < 0.50 AND fewer than 10 prefix-token matches → **novel** (label 0)
- ROUGE-L < 0.50 AND 10 or more prefix-token matches → borderline (treated as manual review)
- Borderline [0.50, 0.70] → manual review (`review_borderline.py`)

**Final dataset**: **1,727 examples** (73 memorized / 4.2%, 1,654 novel), stored as `data/memorization/labeled/dataset.parquet` (670 KB). The strong class imbalance (4.2% positive) means accuracy is a misleading metric; F1 and balanced class weights are essential.

### 4.3 Activation Extraction

For each prompt–continuation pair:
1. Tokenize prompt (with BOS) and continuation (without BOS), concatenate.
2. Run a single forward pass with `output_hidden_states=True`.
3. Slice out the continuation portion from all 33 layers.
4. Compute `mean_pooled` (mean across continuation tokens) and `last_token` representations per layer.

Activations are cached to `data/memorization/labeled/activations_checkpoint.pkl` (gitignored) with checkpoint-resumable extraction to handle interruptions.

### 4.4 Layer Selection

Each layer is ranked by **mean absolute Cohen's d** — the average effect size across all 3,072 hidden dimensions between the memorized and novel classes. The top layers by separability are:

| Rank | Layer | Mean Cohen's d (train only) |
|---|---|---|
| 1 | 32 (last transformer) | 0.6144 |
| 2 | 1 (first transformer) | 0.3960 |
| 3 | 0 (embedding layer) | 0.3665 |

Layer selection performed on the training split only (C1 correction). The top 3 layers are selected; their `mean_pooled` representations are concatenated into a **9,216-dimensional feature vector** per example.

### 4.5 Probe Training

Classifier: **Logistic Regression** (balanced class weights, sklearn default solver).  
Features are normalised with `StandardScaler` before fitting.

An MLP variant (hidden layers [128, 64]) was also trained for comparison.

### 4.6 Results

#### Corrected Baseline In-Domain (80/20 stratified split, 1,381 train / 346 test)

| Metric | Logistic Regression | MLP |
|---|---|---|
| Accuracy | 0.9595 | — |
| Precision | 0.5294 | — |
| Recall | 0.6000 | — |
| F1 Score | **0.5625** | **Not recorded** |

> **Note on baseline MLP**: The MLP was trained during the corrected-baseline run for validation only and its F1 was printed to stdout but not saved to a file. The value is therefore not reproducible from stored artefacts; it must not be inferred from the Prefix K=5 MLP result (0.6207), which comes from a different training procedure.

**Confusion matrix (Logistic Regression)**:

```
             Predicted
          Novel  Memorized
Novel      323       8
Memorized    6       9
```

The sharp drop from pre-correction estimates (F1 ≈ 0.985) is the expected effect of removing test-set leakage from layer selection. The class imbalance is severe — only 15 memorized examples in the 346-example test set (4.3%). The probe still detects 9 of 15 memorized examples (Recall = 0.60) at Precision = 0.53, which is a meaningful signal (a naive classifier predicting all-novel would achieve Recall = 0).

#### Corrected Baseline Out-of-Domain Generalisation (trained on Wikipedia/Books, tested on 223 unseen code snippets)

| Metric | Linear Probe | MLP |
|---|---|---|
| F1 Score | 0.0000 | 0.0351 |
| Recall | 0.0000 | 0.0189 |
| Precision | 0.0000 | 0.2500 |

The OOD probe made zero correct positive predictions (Linear) and one correct positive prediction (MLP) out of 53 memorized code examples. The generalization failure reflects two compounding factors: (1) the non-code training set contains only 20 memorized examples out of 1,504 (1.3%), providing insufficient positive signal to learn a generalizable memorization boundary; (2) the domain shift from natural language to code is substantial — both in text distribution and memorization rate (1.3% non-code vs 23.8% code). The C2 correction exposed this limitation, which was masked by the previous OOD leakage.

#### Prefix K=5 Memorization Results

Probe trained with the expanded prefix methodology (see §4.8); tested at k=5 (full-continuation mean_pooled, directly comparable to the baseline). Selected layers: [32, 1, 22].

| Metric | Logistic Regression | MLP |
|---|---|---|
| In-Domain F1 (k=5) | **0.5882** | **0.6207** |
| OOD Code F1 (k=5) | 0.0357 | — |

The prefix K=5 LR F1 (0.5882) modestly outperforms the corrected-baseline LR F1 (0.5625), consistent with the expanded training set providing marginally better coverage of the memorization signal.

#### Teacher-Forcing Verification

Forcing the true continuation tokens (known-memorized text) through the model at decoding time consistently yields high memorization scores; forcing novel control continuations yields low scores. This confirms the probe reads a genuine memorization signal rather than surface heuristics.

### 4.7 Live Demo Results

| Prompt | Risk Level | Max Token Score | Avg Token Score |
|---|---|---|---|
| Alice in Wonderland (known text) | **HIGH** | 0.9888 | 0.3229 |
| Call me Ishmael / Moby Dick | **LOW** | 0.0696 | 0.0038 |
| Invented sci-fi scenario | **LOW** | 0.1292 | 0.0149 |
| Factual Q&A (capital of France) | **LOW** | 0.2508 | 0.0246 |

The probe correctly flags the Alice in Wonderland continuation (exact novel text) while leaving factual, novel, and open-domain outputs unmarked.

*Note: demo scores above were produced with the corrected-baseline probe (`results/memorization/probe.joblib`, layers [32, 1, 0]). The demo CLI now defaults to the Prefix K=5 probe (`results/memorization/probe_prefix_k5.joblib`, layers [32, 1, 22]).*

### 4.8 Prefix Training (K=5) — Expanded Methodology

To increase effective training set size without additional data collection, each training example is re-used at K=5 different prefix lengths of its continuation. For a continuation of N tokens, prefix representations are extracted at positions t_k = max(1, min(round(N × k/5), N)) for k = 1, 2, 3, 4, 5.

**Key implementation properties:**
- A single forward pass with causal masking yields all K hidden states simultaneously: the activation at position p is identical to what a forward pass on only the first p tokens would produce.
- All K prefix vectors from one example remain in the same train/test split to prevent leakage.
- The training matrix is `np.stack(parts, axis=1).reshape(N_train × K, hidden_dim)` with labels propagated via `np.repeat(y_train, K)`.
- **Evaluation is always at k=5** (the full-continuation mean_pooled representation), making it directly comparable to the corrected baseline.

The Prefix K=5 probe therefore uses a 5× expanded training set but is evaluated identically to the baseline probe. This is a data-augmentation approach, not a change to the inference representation.

---

## 5. Probe 2 — Hallucination Detection

### 5.1 Goal

Identify when the model generates factually incorrect or unsupported claims.

### 5.2 Dataset Construction

**Source**: [TruthfulQA](https://github.com/sylinrl/TruthfulQA) benchmark — a curated set of questions known to elicit hallucinations in LLMs, with multiple reference answers provided.

**Labelling**: Phi-3 is prompted with each TruthfulQA question and generates a free-form answer. The answer is scored by ROUGE-L recall against the set of reference answers:
- Recall ≥ 0.5 → **grounded** (label 0)
- Recall < 0.5 → **hallucinated** (label 1)

**Post-processing**:
- Boilerplate stripping (model preamble like "Sure, here is…" removed)
- Entity Guard: ambiguous single-entity answers reviewed separately
- Multiple manual review cycles using exported CSV batches (`needs_manual_review.csv`, `reconsidered.csv`, `newly_resolved.csv`)

**Final dataset**: **796 examples** (436 hallucinated / 360 grounded), stored as `data/hallucination/labeled/dataset.parquet` (243 KB), covering categories: Misconceptions, Law, Medicine, Conspiracies, and others.

### 5.3 Activation Extraction & Layer Selection

Same pipeline as Probe 1. Top layers ranked by Cohen's d for the hallucination task:

| Rank | Layer |
|---|---|
| 1 | 32 (last transformer) |
| 2 | 15 |
| 3 | 17 |

Feature vector: layers [32, 15, 17] concatenated → **9,216 dimensions**.

### 5.4 Probe Training

Same Logistic Regression + MLP setup as Probe 1.

### 5.5 Results

#### Corrected Baseline In-Domain (80/20 stratified split, 636 train / 160 test)

| Metric | Logistic Regression | MLP |
|---|---|---|
| Accuracy | 0.6687 | — |
| Precision | 0.7160 | — |
| Recall | 0.6591 | — |
| F1 Score | **0.6864** | **0.7241** |

**Confusion matrix (Logistic Regression)**:

```
                 Predicted
              Grounded  Hallucinated
Actual Grounded    49        23
Actual Hallucinated 30        58
```

> **Note on stability**: The hallucination probe numbers are numerically identical to the pre-correction run. This is expected: (1) the dataset is near-balanced (436/360), so the same `random_state=42` split produces the same 636/160 partition and the same class distribution in train; (2) Cohen's d values are uniformly small (d ≤ 0.107) and close together across many layers — the top-3 ranking [32, 15, 17] is stable whether computed on 636 train examples or all 796. The correction is still methodologically necessary; this result confirms the hallucination signal is weak enough that the previous leakage happened not to change the layer order.

#### Corrected Baseline Held-Out Category Generalisation (each category excluded from its own layer selection)

| Category (held out) | F1 | Accuracy | Precision | Recall |
|---|---|---|---|---|
| Misconceptions | 0.3947 | 0.5400 | 0.5000 | 0.3261 |
| Law | 0.6133 | 0.5246 | 0.6765 | 0.5610 |

Generalisation varies significantly by category. The Misconceptions category is the most challenging — likely because misconceptions are semantically plausible, making the activation signal noisier.

#### Prefix K=5 Hallucination Results

Probe trained with the expanded prefix methodology (see §4.8); tested at k=5 (full-continuation mean_pooled, directly comparable to the corrected baseline). Selected layers: [32, 17, 16].

| Metric | Logistic Regression | MLP |
|---|---|---|
| In-Domain F1 (k=5) | **0.7314** | **0.7345** |

| Category (held out) | F1 |
|---|---|
| Misconceptions | 0.4634 |
| Law | 0.6000 |

The Prefix K=5 probe shows modest improvements over the corrected baseline in-domain (LR: +0.0450, MLP: +0.0104) and on the Misconceptions OOD category (+0.0687), with a slight decrease on Law (−0.0133). The improvements are consistent with a larger effective training set providing better coverage of the hallucination signal.

### 5.6 Comparison: Corrected Baseline vs Prefix K=5

**Corrected Baseline**

| Dimension | Memorization Probe | Hallucination Probe |
|---|---|---|
| In-domain F1 (LR) | 0.5625 | **0.6864** |
| In-domain F1 (MLP) | Not recorded | **0.7241** |
| OOD F1 | 0.0000–0.0351 | 0.39–0.61 |
| Selected layers | [32, 1, 0] | [32, 15, 17] |
| Max Cohen's d | 0.6144 (layer 32, train only) | 0.1071 (layer 32, train only) |

**Prefix K=5**

| Dimension | Memorization Probe | Hallucination Probe |
|---|---|---|
| In-domain F1 (LR, k=5) | 0.5882 | **0.7314** |
| In-domain F1 (MLP, k=5) | **0.6207** | **0.7345** |
| OOD F1 (k=5) | 0.0357 | 0.46–0.60 |
| Selected layers | [32, 1, 22] | [32, 17, 16] |

The memorization probe's dramatically lower corrected in-domain F1 (0.56 vs prior 0.99) is a direct consequence of the severe class imbalance (4.2% positive rate): the leaked layer selection had previously optimised for test-set separability, inflating the apparent signal. The hallucination probe's results are unchanged, confirming its pre-correction numbers were already valid. Prefix K=5 training yields modest but consistent improvements across both probes and both tasks.

---

## 6. Live Inference System

### 6.1 Architecture

The CLI (`cli.py` / `demo/inference.py`) loads Phi-3 once and both probes once, then runs:

1. Encode the user's prompt.
2. **Autoregressive loop** (up to `max_tokens`):
   - Append the latest generated token to the context.
   - Run a single forward pass → extract hidden states from selected layers for both probes.
   - **Memorization probe**: concatenate layer activations → scale → predict P(memorized).
   - **Hallucination probe**: same, simultaneously.
   - Predict next token (greedy, argmax over logits).
3. Output each token annotated with both scores.

### 6.2 Terminal Rendering

`demo/render.py` produces a structured five-section output after each generation:

1. **Generated Answer** — the full response, decoded correctly by the tokenizer (no inline annotations).
2. **Probe Summary** — overall risk level (HIGH/MEDIUM/LOW), average score, and max score per active probe.
3. **Generation Info** — token counts (prompt / generated / total) and EOS vs token-limit status.
4. **Detailed Token Analysis** — per-token table with token index, sanitised token string, and colour-coded scores for each active probe.
5. **ASCII Risk Charts** — Unicode block bar charts showing how probe risk evolves across the generated token sequence.

ANSI colour thresholds apply throughout:

| Score | Colour | Meaning |
|---|---|---|
| ≥ 0.6 | Red | High risk |
| 0.3 – 0.6 | Yellow | Medium risk |
| < 0.3 | Green | Low risk |

### 6.3 CLI Usage

```bash
# Interactive REPL (loads model once, allows multiple queries)
python cli.py

# Single prompt
python cli.py --prompt "Alice was beginning to get very tired..." --max_tokens 50

# Single-probe mode
python cli.py --task memorization --prompt "..."
python cli.py --task hallucination --prompt "..."
```

---

## 7. Technical Implementation Notes

### Activation Extraction Detail (`llm_probe/core/activations.py`)

The extraction is careful to:
- Concatenate prompt and continuation with exact token boundary preservation (no re-tokenization artefacts).
- Extract only the **continuation** portion from each layer (not the prompt tokens).
- Return both `last_token` and `mean_pooled` representations so the training pipeline can select the better one.

### Checkpoint-Resumable Extraction

Activation extraction for >1,000 examples can take hours on GPU. `build_memorization_dataset.py` and `build_hallucination_dataset.py` implement a checkpoint pattern: partial results are saved to `.pkl` periodically; if the script is interrupted, it resumes from the last checkpoint instead of restarting.

### Layer Selection (`llm_probe/core/layer_selection.py`)

Cohen's d is computed per hidden dimension, then **averaged across all dimensions** for a scalar per-layer score. This gives a robust ranking that accounts for multi-dimensional class separation rather than just variance.

---

## 8. Key Findings

1. **Memorization is detectable with a meaningful but modest signal**: Corrected-baseline in-domain F1 = 0.5625 (LR) on a severely imbalanced test set (4.2% positive rate). The probe correctly identifies 9 of 15 memorized examples at Precision 0.53. The prior reported F1 ≈ 0.985 was an artefact of test-set leakage in layer selection; the true activation separability (max Cohen's d = 0.61 on training data) is real but much more modest. Prefix K=5 training raises LR F1 to 0.5882 and MLP F1 to 0.6207.

2. **Memorization does not generalise to the code domain under the corrected OOD protocol**: With only 20 memorized examples in the non-code training split (1.3% positive rate), the probe learned no reliable boundary transferable to code_snippets (23.8% positive rate). F1 ≈ 0 on 223 code test examples. A code-specific probe or a larger balanced memorization dataset would be needed for code generalisation.

3. **Hallucination detection is a harder problem, confirmed**: Corrected-baseline F1 = 0.6864 (LR) / 0.7241 (MLP) in-domain; Prefix K=5 raises this to 0.7314 (LR) / 0.7345 (MLP). Max Cohen's d = 0.107, versus 0.614 for memorization — factual incorrectness produces an activation signature roughly 6× weaker than verbatim memorization. OOD generalisation for the corrected baseline is 0.39–0.61 by category; Prefix K=5 reaches 0.46–0.60.

4. **Top-layer activations dominate both tasks**: Layer 32 (the final transformer block) is the strongest predictor for both probes. Higher-level semantic representations, formed late in the network, carry the most task-relevant information.

5. **MLP provides marginal gains over Logistic Regression**: Hallucination baseline: +0.04 F1 (0.69 → 0.72). Prefix K=5: memorization +0.03 F1 (0.59 → 0.62), hallucination +0.003 F1 (0.73 → 0.73). The activation signal is not fully linearly separable, but the gap is moderate.

6. **Dual-probe inference is practical**: Both probes run on a single forward pass with negligible overhead — the bottleneck is the base model's autoregressive generation, not the probe scoring.

---

## 9. Limitations & Future Work

### Methodology Limitations (corrected or documented)

| ID | Limitation | Status |
|---|---|---|
| C1 | Layer selection used all data (including test set), inflating reported OOD/in-domain separation estimates | **Fixed & rerun complete** — corrected numbers in sections 4.6 and 5.5 |
| C2 | OOD evaluation layer selection used the held-out category data | **Fixed & rerun complete** — corrected numbers in sections 4.6 and 5.5 |
| H1 | Per-token inference scores computed on growing prefix (1–t tokens), while probes trained on full continuations — early-step scores are out-of-distribution | **Partially addressed** by Prefix K=5 training (probes see diverse prefix lengths during training), though the train/inference distribution still differs due to label propagation across prefixes. Sequence-level F1 unaffected. |
| M1 | Memorization class imbalance: 73 memorized / 1,727 total (4.2%) — accuracy is a misleading metric | Balanced class weights used throughout; F1 reported |
| M2 | 9 low-similarity-floor hallucination examples (1.1%) were labelled by floor rule, not ROUGE-L | Not material; documented for completeness |

### Known Limitations & Future Work

| Limitation | Potential Fix |
|---|---|
| Hallucination probe trained on TruthfulQA only | Extend dataset to open-domain QA (e.g., SQuAD, Natural Questions) |
| ROUGE-L labelling is an imperfect proxy for hallucination | Incorporate LLM-as-judge labelling or human annotation at scale |
| Probes are Phi-3-specific | Test transferability to other models (Llama, Mistral) |
| Greedy decoding in inference | Support beam search and top-p sampling |
| No confidence calibration | Apply temperature scaling to probe outputs |
| Hallucination generalisation varies by domain | Train category-specific probes or use domain adaptation |
| Prefix K=5 label propagation assumption | Each prefix representation is labelled with the full-continuation label; short prefixes may not yet exhibit the final classification signal, introducing noise | Use dynamic labelling or learn label confidence per prefix length |
| Memorization class imbalance limits prefix benefit | Only ~73 memorized examples in 1,727 total; 5× expansion reuses the same rare positives | Collect additional memorized examples; consider oversampling positives |
| Prefix K=5 MLP not evaluated OOD | MLP probe for memorization Prefix K=5 OOD not recorded | Run OOD evaluation on Prefix K=5 MLP probe |
| Demo train/inference representation mismatch persists | Even with Prefix K=5, the demo scores each token on a partial continuation; sequence-level probe F1 is the valid performance metric | Reported clearly; per-token scores are indicative only |

---

## 10. Artefacts

| Artefact | Path | Size |
|---|---|---|
| Memorization probe (corrected baseline) | `results/memorization/probe.joblib` | 290 KB |
| Memorization probe (Prefix K=5) | `results/memorization/probe_prefix_k5.joblib` | 290 KB |
| Hallucination probe (corrected baseline) | `results/hallucination/probe.joblib` | 290 KB |
| Hallucination probe (Prefix K=5) | `results/hallucination/probe_prefix_k5.joblib` | 290 KB |
| Memorization dataset | `data/memorization/labeled/dataset.parquet` | 670 KB |
| Hallucination dataset | `data/hallucination/labeled/dataset.parquet` | 243 KB |
| Memorization layer rankings | `results/memorization/layer_rankings.png` | 35 KB |
| Hallucination layer rankings | `results/hallucination/layer_rankings.png` | 36 KB |
| Demo test results | `results/memorization/demo_test_results.md` | — |
| Hallucination training report | `results/hallucination/probe_training_report.md` | — |

The Prefix K=5 probe files are the current demo defaults (see `demo/inference.py` lines 31–32). The corrected-baseline probes remain available for comparison.

Activation checkpoint files (several GB) are gitignored and must be regenerated locally by running the respective `build_*_dataset.py` scripts.

---

## 11. Dependencies

| Package | Role |
|---|---|
| `torch` 2.5.1 | Model execution |
| `transformers` 5.14.1 | Phi-3 loading and inference |
| `bitsandbytes` | 4-bit NF4 quantization |
| `scikit-learn` | Logistic Regression, MLP, StandardScaler, metrics |
| `datasets` | TruthfulQA dataset loading |
| `rouge-score` | ROUGE-L labelling |
| `pandas`, `numpy` | Data manipulation |
| `matplotlib`, `seaborn` | Layer ranking plots |
| `joblib` | Probe serialisation |
