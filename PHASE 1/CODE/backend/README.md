# ChronoLens - Backend

FastAPI backend service for the **ChronoLens** AI Powered Video Intelligence Framework (Phase 0 Foundation & Upload Pipeline).

---

## Technical Overview

- **Language:** Python 3.11+
- **Framework:** FastAPI & Uvicorn
- **Validation:** Pydantic v2
- **Storage:** Local streaming filesystem storage (`app/uploads/`)

---

## Folder Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── dependencies.py          # Shared endpoint dependencies
│   │   └── v1/
│   │       ├── router.py            # API Router aggregator
│   │       └── endpoints/
│   │           ├── root.py          # GET /
│   │           ├── health.py        # GET /health
│   │           └── upload.py        # POST /upload
│   ├── core/
│   │   └── config.py                # Pydantic environment & system configuration
│   ├── services/
│   │   └── upload_service.py        # Chunked streaming video save & validation logic
│   ├── models/
│   │   └── schemas.py               # Request & response Pydantic models
│   ├── utils/
│   │   └── file_utils.py            # UUID generation, format validation, size conversion
│   ├── uploads/
│   │   └── .gitkeep                 # Local upload storage directory
│   └── main.py                      # FastAPI entry point, CORS setup & startup events
│
├── .env.example                     # Environment variables template
├── requirements.txt                 # Python package dependencies
└── README.md                        # Backend documentation
```

---

## Backend Setup & Local Execution

### 1. Create & Activate Virtual Environment

```bash
# Navigate to backend folder
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# Linux / macOS:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run FastAPI Server

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The backend server will start on `http://127.0.0.1:8000`.

---

## API Endpoints Documentation

### 1. Root Endpoint
- **URL:** `GET /`
- **Description:** Returns basic project information and state.
- **Response Format (`200 OK`):**
```json
{
  "project": "ChronoLens",
  "status": "running",
  "version": "0.1"
}
```

---

### 2. Health Check
- **URL:** `GET /health`
- **Description:** System health check endpoint.
- **Response Format (`200 OK`):**
```json
{
  "status": "healthy"
}
```

---

### 3. Upload Video
- **URL:** `POST /upload`
- **Content-Type:** `multipart/form-data`
- **Supported Video Formats:** `.mp4`, `.avi`, `.mov`, `.mkv`
- **Maximum File Size:** `2 GB` (2,147,483,648 bytes)
- **Response Format (`201 Created`):**
```json
{
  "video_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "filename": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d.mp4",
  "original_name": "sample_clip.mp4",
  "size": "42.50 MB",
  "status": "uploaded"
}
```

#### Error Responses
- **`400 Bad Request`** (Invalid file type / extension):
```json
{
  "detail": "Unsupported file type. Only video files (.avi, .mkv, .mov, .mp4) are allowed."
}
```
- **`413 Payload Too Large`** (Exceeds 2GB):
```json
{
  "detail": "Large file. Maximum allowed upload size is 2GB."
}
```

---

## Interactive API Docs (Swagger UI & ReDoc)

Once the backend server is running, interactive documentation is available at:
- **Swagger UI:** `http://127.0.0.1:8000/docs`
- **ReDoc:** `http://127.0.0.1:8000/redoc`
