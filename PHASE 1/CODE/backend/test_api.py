import asyncio
import os
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)


def test_root_endpoint():
    print("--> Testing GET /")
    res = client.get("/")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    data = res.json()
    assert data["project"] == "ChronoLens"
    assert data["status"] == "running"
    assert data["version"] == "0.1"
    print(" [PASSED] GET /:", data)


def test_health_endpoint():
    print("--> Testing GET /health")
    res = client.get("/health")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    data = res.json()
    assert data["status"] == "healthy"
    print(" [PASSED] GET /health:", data)


def test_upload_valid_video():
    print("--> Testing POST /upload (valid .mp4 file)")
    dummy_video_content = b"\x00\x00\x00\x18ftypisom\x00\x00\x02\x00isomiso2avc1mp41"
    files = {"file": ("test_sample.mp4", dummy_video_content, "video/mp4")}
    
    res = client.post("/upload", files=files)
    assert res.status_code == 201, f"Expected 201 Created, got {res.status_code}: {res.text}"
    data = res.json()
    assert "video_id" in data
    assert data["original_name"] == "test_sample.mp4"
    assert data["status"] == "uploaded"
    
    saved_file = settings.UPLOADS_DIR / data["filename"]
    assert saved_file.exists(), f"Uploaded file {saved_file} does not exist on disk"
    print(" [PASSED] POST /upload (valid video):", data)
    
    # Cleanup test upload file
    if saved_file.exists():
        saved_file.unlink()


def test_upload_invalid_file_type():
    print("--> Testing POST /upload (invalid .txt file format)")
    files = {"file": ("document.txt", b"Hello world text file", "text/plain")}
    res = client.post("/upload", files=files)
    assert res.status_code == 400, f"Expected 400 Bad Request, got {res.status_code}"
    data = res.json()
    assert "Unsupported file type" in data["detail"]
    print(" [PASSED] POST /upload (invalid format rejection):", data)


if __name__ == "__main__":
    print("\n================ RUNNING API VERIFICATION TESTS ================\n")
    test_root_endpoint()
    test_health_endpoint()
    test_upload_valid_video()
    test_upload_invalid_file_type()
    print("\n================ ALL BACKEND API TESTS PASSED ================\n")
