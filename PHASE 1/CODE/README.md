# ChronoLens: AI Powered Video Intelligence Framework

> **Department of Artificial Intelligence and Data Science / Machine Learning**  
> **Batch 2026–2027 | Section B | Team 11**

---

## 📌 Project Overview

**ChronoLens** is an advanced AI-powered video intelligence and multi-modal semantic retrieval framework. It ingests video feeds, decomposes them into temporal frames and audio tracks, tracks objects across time using deep spatio-temporal tracking, extracts fine-grained visual attributes and OCR scene text, and allows users to perform natural-language queries (visual descriptions, clothing/color attributes, speech transcripts, and visible text) to retrieve precise video moments with sub-second accuracy.

---

## 🏗️ Architecture & Core Components

```
                   ┌────────────────────────────────────────┐
                   │        Video Input (.mp4, .avi)        │
                   └───────────────────┬────────────────────┘
                                       │
                     ┌─────────────────┴─────────────────┐
                     ▼                                   ▼
          ┌───────────────────────┐           ┌───────────────────────┐
          │    Video Processor    │           │    Audio Processor    │
          │  (Frame Extraction)   │           │   (Whisper Transcribe)│
          └──────────┬────────────┘           └──────────┬────────────┘
                     │                                   │
      ┌──────────────┴──────────────┐                    │
      ▼                             ▼                    │
┌───────────────┐           ┌───────────────┐            │
│  YOLO26m / v8 │           │   PaddleOCR   │            │
│Object Detector│           │   Scene Text  │            │
└───────┬───────┘           └───────┬───────┘            │
        │                           │                    │
        ▼                           │                    │
┌───────────────┐                   │                    │
│   ByteTrack   │                   │                    │
│Object Tracking│                   │                    │
└───────┬───────┘                   │                    │
        │                           │                    │
        ▼                           ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│  Multi-Modal Feature Extraction & Unified Storage           │
│  - OpenCLIP / SigLIP2 Visual & Keyframe Embeddings          │
│  - Fine-Grained Attribute & Footwear Specialist (Color/Type)│
│  - In-Memory FAISS Vector Index & MongoDB Document Store    │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│               Query Router & Retrieval Engine               │
│  - Natural Language Intent Parsing & Relational Analysis    │
│  - Hybrid Semantic + Attribute + OCR + Speech Fusion        │
│  - Candidate Re-Ranking & Temporal Grouping                 │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│       FastAPI Backend API  ◄──►  React 18 + Vite UI         │
│     (Interactive Search Dashboard & Visual Inspector)       │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

### Backend
- **Language:** Python 3.10+ / 3.11+
- **Framework:** FastAPI with Uvicorn (ASGI)
- **Validation & Settings:** Pydantic v2 & Pydantic-Settings
- **Computer Vision & Detection:** Ultralytics YOLO26m / YOLOv8, OpenCV
- **Multi-Object Tracking:** ByteTrack Spatio-Temporal Association
- **Embedding & Semantic Search:** OpenCLIP, SigLIP2, FAISS vector indexing
- **Scene Text Recognition:** PaddleOCR
- **Audio Processing:** OpenAI Whisper
- **Database:** MongoDB (Motor async driver) with transparent local JSON fallback

### Frontend
- **Framework:** React 18
- **Build Tool:** Vite
- **Styling:** Custom Modern Vanilla CSS (Dark theme with `#4F46E5` primary accent)
- **HTTP Client:** Axios
- **Icons:** Lucide React

---

## 📂 Directory Structure

```
PHASE 1/CODE/
├── backend/
│   ├── app/
│   │   ├── api/                     # REST API endpoints & dependency injection
│   │   │   ├── v1/
│   │   │   │   ├── endpoints/       # Upload, search, status, debug, summary, health
│   │   │   │   └── router.py        # Central API router aggregator
│   │   │   └── dependencies.py
│   │   ├── core/
│   │   │   └── config.py            # System configuration & environment management
│   │   ├── database/
│   │   │   └── mongo.py             # MongoDB async connection & data access layer
│   │   ├── models/
│   │   │   ├── schemas.py           # Pydantic data schemas & response models
│   │   │   └── attribute_v3_schema.py
│   │   ├── processing/              # Media processing pipelines
│   │   │   ├── attributes/          # Clothing, color, and footwear extractors
│   │   │   ├── audio/               # Whisper audio transcriber
│   │   │   ├── debug/               # Bounding box & tracking visual annotator
│   │   │   ├── detection/           # YOLO object detector
│   │   │   ├── ocr/                 # PaddleOCR scene text service
│   │   │   ├── text/                # OCR text processing
│   │   │   ├── tracking/            # ByteTrack object tracker
│   │   │   ├── video/               # Video decoding & frame extraction
│   │   │   ├── coordinator.py       # Full pipeline coordinator
│   │   │   ├── embedding_generator.py # OpenCLIP visual embedding engine
│   │   │   └── metadata.py          # Video metadata extractor
│   │   ├── search/                  # Multi-modal query & retrieval engine
│   │   │   ├── attribute_filter.py
│   │   │   ├── attribute_reranker.py
│   │   │   ├── attribute_retrieval_engine.py
│   │   │   ├── query_embedder.py
│   │   │   ├── query_router.py
│   │   │   ├── ranking_engine.py
│   │   │   ├── representative_selector.py
│   │   │   ├── result_filter.py
│   │   │   ├── search_analytics.py
│   │   │   ├── search_models.py
│   │   │   ├── semantic_search_service.py
│   │   │   └── track_grouping.py
│   │   ├── services/                # Business services
│   │   │   ├── semantic/            # FAISS index manager & OpenCLIP engine
│   │   │   ├── clip_generator.py    # Target video clip generation
│   │   │   ├── debug_service.py     # Diagnostic & visualization inspection
│   │   │   ├── queue_service.py     # Async background task queue
│   │   │   ├── reset_service.py     # Database & cache reset utility
│   │   │   └── upload_service.py    # Chunked video upload handler
│   │   ├── uploads/
│   │   │   └── .gitkeep             # Local upload storage directory
│   │   ├── utils/
│   │   │   └── file_utils.py        # File helpers & format validators
│   │   └── main.py                  # FastAPI application entrypoint
│   ├── .env.example                 # Environment configuration template
│   ├── README.md                    # Backend documentation
│   ├── requirements.txt             # Python dependencies
│   ├── test_api.py                  # API integration test
│   ├── test_pipeline.py             # End-to-end processing pipeline test
│   ├── test_search.py               # Semantic search test
│   ├── test_hybrid_ranking.py       # Hybrid retrieval ranking test
│   └── verify_live_search.py        # Live search verification script
│
├── frontend/
│   ├── public/                      # Static assets
│   ├── src/
│   │   ├── components/
│   │   │   ├── DebugDashboard.jsx   # Visual inspection & track debugging interface
│   │   │   ├── ExampleQueries.jsx   # One-click pre-configured benchmark queries
│   │   │   ├── SemanticSearch.jsx   # Multi-modal search input & results viewer
│   │   │   └── VideoUploader.jsx    # Drag-and-drop video upload component
│   │   ├── App.jsx                  # Main application container
│   │   ├── index.css                # Custom modern dark design system
│   │   └── main.jsx                 # React root renderer
│   ├── index.html                   # HTML template
│   ├── package.json                 # Node.js dependencies
│   ├── vite.config.js               # Vite bundler configuration
│   └── README.md                    # Frontend documentation
│
├── .gitignore                       # Repository exclusion rules
└── README.md                        # Master project guide
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python:** 3.10 or 3.11 recommended
- **Node.js:** 18+ and npm
- **FFmpeg:** Installed and available in system PATH (required for audio/video decoding)
- **Git**

---

### 2. Backend Setup

1. Open a terminal and navigate to the `backend` directory:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:
   ```bash
   # Windows (PowerShell)
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create local environment configuration:
   ```bash
   # Windows
   copy .env.example .env

   # Linux / macOS
   cp .env.example .env
   ```

5. Launch the FastAPI backend server:
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```
   The backend will be available at:
   - **Interactive Swagger Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   - **Alternative ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
   - **Health Check:** [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

---

### 3. Frontend Setup

1. Open a new terminal and navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```

2. Install npm dependencies:
   ```bash
   npm install
   ```

3. Start the Vite development server:
   ```bash
   npm run dev
   ```

4. Open your browser and navigate to:
   - **ChronoLens Web Application:** [http://localhost:5173](http://localhost:5173)

---

## 🔍 Key Capabilities & Usage

1. **Video Ingestion:** Upload an `.mp4`, `.mov`, or `.avi` video through the drag-and-drop web portal.
2. **Automated Analysis:** ChronoLens extracts frames, tracks people and objects, transcribes spoken words, and reads on-screen text in the background.
3. **Multi-Modal Semantic Search:** Search using diverse queries:
   - *Natural Visual:* `"person in blue jacket walking"`, `"black backpack on table"`
   - *Attribute Filtering:* `"man wearing yellow pants and dark shoes"`
   - *Scene Text / OCR:* `"EXIT"`, `"CAUTION"`, visible signs or license plates
   - *Spoken Audio:* Speech quotes or dialog mentioned in the video
4. **Interactive Timeline:** Click any result to play the exact sub-clip where the entity or event occurs.
5. **Debug Dashboard:** Inspect bounding boxes, tracker IDs, confidence curves, and model metadata.

---

## 🧪 Running Automated Tests

To verify backend pipeline functionality, run:

```bash
cd backend
python test_pipeline.py
python test_api.py
python test_search.py
```

---

## 👥 Team 11 Members

- **Project:** ChronoLens - AI Powered Video Intelligence Framework
- **Academic Year:** 2026–2027
- **Section:** Section B
