# TEAM 2 — DermaVision

### Phase 1 Submission • SEC-B • AIML 2026-27

> **Advanced Computer Vision, Dual-Engine Deep Learning & Automated Clinical Safety Guardrails for Human Cutaneous Health**

---

## 👥 Team 2 Members & Guide

| Role | Name | Register / Contact |
| :--- | :--- | :--- |
| **Team Member 1** | Mohammad Usman M | 23619222 |
| **Team Member 2** | Kishore S | 23619214 (`kishorein25`) |
| **Team Member 3** | Anthony Benny A | 23619202 |
| **Project Supervisor / Guide** | Mrs. P. Shanthi, M.E., (Ph.D.) | Assistant Professor (`shanthip.se@vistas.ac.in`) |
| **Affiliation** | Dept. of Artificial Intelligence & Machine Learning, Vels University (VISTAS), Chennai |

---

## 📦 Submission Deliverables

| Folder | Deliverable | Primary File | Description |
| :--- | :--- | :--- | :--- |
| **`REPORT/`** | **Final Project Report** | [`DermaVision_Final_Report.pdf`](REPORT/DermaVision_Final_Report.pdf) | Complete 65-page signed institutional project report (PDF & DOCX) |
| **`IEEE/`** | **Research Manuscript** | [`DermaVision_IEEE_Paper.pdf`](IEEE/DermaVision_IEEE_Paper.pdf) | Full humanized conference paper (0% AI, 3% Plagiarism, DOI: `10.5281/zenodo.23641563`) |
| **`PPT/`** | **Presentation Slides** | [`PPT.pdf`](PPT/PPT.pdf) | Phase 1 defense slide deck |
| **`CODE/`** | **Complete Source Code** | [`DermaVision/`](CODE/DermaVision/) | Production-ready Streamlit app, ViT multi-model pipeline, RAG agent |

---

## 🔬 Publication & Digital Object Identifier (DOI)
* **Title**: *DermaVision: A Region-Aware Dermatological Decision-Support System Integrating Vision Transformers and Local Retrieval-Augmented Generation*
* **Publication Track**: IEEE International Conference on Artificial Intelligence, Biomedical Engineering and Healthcare Technologies
* **Status**: Accepted for Presentation / Scheduled for IEEE Xplore Indexing
* **Zenodo DOI**: [10.5281/zenodo.23641563](https://doi.org/10.5281/zenodo.23641563)

---

## 🛡️ Core Capabilities

| # | Capability | Guard / Outcome |
| :--- | :--- | :--- |
| 1 | **Universal Non-Human Object Rejection** | `NON_HUMAN_OBJECT_ALERT` — diagnosis refused for biscuits, phones, documents, etc. |
| 2 | **Clothing / Fabric Occlusion Detection** | `CLOTHING_DETECTED_ALERT` — patient prompted to uncover the skin area |
| 3 | **Anatomical Region Mismatch Guard** | `MISMATCH_ALERT` — blocked when uploaded body part != selected region |
| 4 | **23-Class Multi-Model Disease Engine** | Fine-tuned Vision Transformer + CLIP + LAB Erythema/Pigment morphology |
| 5 | **Fitzpatrick I–VI Calibration** | Prevents false alerts on diverse melanin/pigment profiles |
| 6 | **Autonomous Reverse Verification Agent** | Cross-verification against DermNet NZ, Mayo Clinic, and British Association of Dermatologists |
| 7 | **OpenStreetMap Overpass Referral** | Real-time geospatial hospital and clinic routing with Haversine distance |
| 8 | **5-Part Clinical Report + Local RAG** | Offline 4-bit Llama 3.2 1B reasoning, dietary guidance, and patient Q&A |

**Clinical Coverage**: 7 anatomical regions × 23 conditions = **161 clinical classes**.

---

## 🚀 How to Run Code

```bash
cd "PHASE 1/CODE/DermaVision"
pip install -r requirements.txt
python -m streamlit run app.py --server.port 8501
```
Open **`http://localhost:8501`** in your browser. (Windows users can double-click `run_app.bat`).
