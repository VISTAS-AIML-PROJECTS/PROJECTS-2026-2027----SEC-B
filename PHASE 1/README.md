# TEAM 2 — DermaVision

### Phase 1 Submission · SEC-B · AIML 2026-27

> **Advanced Computer Vision, Dual-Engine Deep Learning & Automated Clinical Safety Guardrails for Human Cutaneous Health**

---

## 👥 Team 2

| | |
| :--- | :--- |
| **Team Number** | Team 2 |
| **Section** | SEC-B |
| **Git Branch** | `TEAM-2` |
| **Project Name** | **DermaVision** — 7-Region Clinical AI Dermatology Screening Platform |
| **Git Author** | `kishorein25` (`ks6700822@gmail.com`) |
| **Team Members** | _kishorein25, <add remaining Team 2 member names here>_ |

---

## 📦 Submission Contents

| Folder | Deliverable | File |
| :--- | :--- | :--- |
| `CODE/` | Full working source code | [`DermaVision/`](CODE/DermaVision/) |
| `IEEE/` | Conference-format research paper | `DermaVision_IEEE_Paper.pdf` |
| `IEEE/` | Final project report | `DermaVision_Final_Report.docx` |
| `PPT/` | Presentation slides | `PPT.pdf` |

Full source: **`PHASE 1/CODE/DermaVision/`** · Detailed project documentation: [`CODE/DermaVision/README.md`](CODE/DermaVision/README.md)

---

## 🎯 Problem Statement

Self-screening for skin conditions needs a dermatologist, but clinics are inaccessible, late, and costly for most patients. Generic AI image classifiers worsen this: they happily diagnose a **biscuit packet** as a skin disease, misclassify **clothing** as a rash, and never notice that a **hand photo** was submitted to a **face** diagnosis slot.

DermaVision is an AI-assisted clinical screening and decision-support prototype that makes those failures impossible by default.

---

## 🛡️ Core Capabilities

| # | Capability | Guard / Outcome |
| :--- | :--- | :--- |
| 1 | **Universal Non-Human Object Rejection** | `NON_HUMAN_OBJECT_ALERT` → diagnosis refused (biscuits, packaging, phones, documents, animals) |
| 2 | **Clothing / Fabric Occlusion Detection** | `CLOTHING_DETECTED_ALERT` → patient asked to uncover the area |
| 3 | **Anatomical Region Mismatch Guard** | `MISMATCH_ALERT` → blocked when uploaded region ≠ selected region |
| 4 | **23-Class Multi-Model Disease Engine** | Fine-tuned Medical ViT + CLIP ViT-B/32 + LAB erythema / pigment / Canny-edge morphology |
| 5 | **Fitzpatrick I–VI Skin-Tone Calibration** | Prevents false vitiligo / keloid alerts on normal dark skin |
| 6 | **23-Disease Reverse Google Images Verification Agent** | Clickable live image-search proof + differential rule-out audit log vs. DermNet NZ / Mayo Clinic / BAD |
| 7 | **Google Maps Specialist Referral** | Nearby dermatology clinics, ratings, distance & turn-by-turn navigation |
| 8 | **5-Part Clinical Report + RAG Chatbot** | Local Llama 3.2 (offline) definition, spread, diet, treatment & patient Q&A |

**Coverage:** 7 anatomical regions (Face, Scalp, Hand & Arm, Leg & Thigh, Foot, Back, Whole Body/Torso) × 23 conditions = **161 clinical classes**.

---

## ⚙️ How to Run

```bash
pip install -r requirements.txt          # from CODE/DermaVision/
python -m streamlit run app.py --server.port 8501
```
Open **http://localhost:8501** · Windows users can double-click `run_app.bat`.

Optional offline LLM for reports & chat: `ollama run llama3.2:1b`

---

## 🧪 Validation

`python test_user_images.py` runs the 12-case clinical benchmark (inanimate objects, packaging, clothing, region mismatches, tattoos, normal skin, acne lesions). See [`CODE/DermaVision/tests/README.md`](CODE/DermaVision/tests/README.md).

---

## 📄 Documentation

| Document | Purpose |
| :--- | :--- |
| [`JUDGES_EXECUTIVE_SUMMARY.md`](CODE/DermaVision/docs/JUDGES_EXECUTIVE_SUMMARY.md) | Executive summary for hackathon judges |
| [`ARCHITECTURE.md`](CODE/DermaVision/docs/ARCHITECTURE.md) | End-to-end system architecture & diagrams |
| [`CLINICAL_VALIDATION.md`](CODE/DermaVision/docs/CLINICAL_VALIDATION.md) | 7-region coverage, 23 conditions & safety metrics |
| [`FREE_MAP_INTEGRATION.md`](CODE/DermaVision/docs/FREE_MAP_INTEGRATION.md) | Zero-cost map API architecture |

---

## 🔒 Medical Disclaimer

DermaVision is an AI-assisted clinical screening and decision-support prototype intended for preliminary triage and educational purposes. **It does not replace professional medical advice, clinical biopsy, or direct physical examination by a licensed dermatologist.**
