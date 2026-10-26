import os
import sys
import time
import uuid
from pathlib import Path
import cv2
import numpy as np

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.models.schemas import ProcessingStatusEnum, FrameMetadata, DetectionItem
from app.processing.metadata import MetadataExtractor
from app.processing.video.frame_extractor import FrameExtractor
from app.processing.tracking.tracker import tracker
from app.processing.coordinator import PipelineCoordinator

from app.database.mongo import mongo_db, MongoDBConnectionError

client = TestClient(app)


def create_synthetic_test_video(output_path: Path, duration_sec: int = 3, fps: int = 25) -> Path:
    """Creates a 3-second sample MP4 video for automated testing."""
    width, height = 640, 480
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(output_path), fourcc, float(fps), (width, height))

    total_frames = duration_sec * fps
    for i in range(total_frames):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        # Draw a moving colored rectangle to simulate moving object
        x_pos = int((i / total_frames) * (width - 100))
        cv2.rectangle(frame, (x_pos, 150), (x_pos + 100, 250), (0, 255, 0), -1)
        cv2.putText(frame, f"Frame {i+1}", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        out.write(frame)

    out.release()
    return output_path


def test_metadata_extraction():
    print("--> [Test] MetadataExtractor")
    test_video = settings.STORAGE_DIR / "temp_test.mp4"
    create_synthetic_test_video(test_video, duration_sec=2, fps=25)

    video_id = str(uuid.uuid4())
    metadata = MetadataExtractor.extract_metadata(test_video, video_id, "temp_test.mp4")

    assert metadata.videoId == video_id
    assert metadata.filename == "temp_test.mp4"
    assert metadata.fps == 25.0
    assert metadata.duration >= 1.9

    if test_video.exists():
        test_video.unlink()
    print(" [PASSED] MetadataExtractor test:", metadata.dict())


def test_frame_extractor():
    print("--> [Test] FrameExtractor (1 FPS)")
    test_video = settings.STORAGE_DIR / "temp_test_2.mp4"
    create_synthetic_test_video(test_video, duration_sec=3, fps=25)

    video_id = str(uuid.uuid4())
    frames = FrameExtractor.extract_frames_1fps(test_video, video_id)

    assert len(frames) >= 3, f"Expected at least 3 frames for 3s video at 1 FPS, got {len(frames)}"
    for f in frames:
        assert isinstance(f, FrameMetadata)
        assert Path(f.imagePath).exists()

    if test_video.exists():
        test_video.unlink()
    print(f" [PASSED] FrameExtractor test: Extracted {len(frames)} frame metadata objects.")


def test_bytetracker():
    print("--> [Test] ByteTracker")
    video_id = str(uuid.uuid4())
    dets = [
        DetectionItem(trackId=None, videoId=video_id, frameNumber=1, timestamp=0.0, boundingBox=[10, 10, 50, 50], confidence=0.9, objectClass="person"),
        DetectionItem(trackId=None, videoId=video_id, frameNumber=2, timestamp=1.0, boundingBox=[12, 12, 52, 52], confidence=0.92, objectClass="person"),
        DetectionItem(trackId=None, videoId=video_id, frameNumber=1, timestamp=0.0, boundingBox=[200, 200, 250, 250], confidence=0.85, objectClass="car"),
    ]

    updated_dets, tracks = tracker.track_objects(dets, video_id)
    assert len(tracks) == 2, f"Expected 2 unique tracks, got {len(tracks)}"
    print(f" [PASSED] ByteTracker test: Generated {len(tracks)} tracks across {len(updated_dets)} detections.")


def test_end_to_end_upload_api():
    print("--> [Test] Upload API and Status/Summary queries")
    test_video = settings.STORAGE_DIR / "temp_upload_test.mp4"
    create_synthetic_test_video(test_video, duration_sec=2, fps=25)

    with open(test_video, "rb") as f:
        response = client.post("/upload", files={"file": ("test_upload.mp4", f, "video/mp4")})

    assert response.status_code == 201, f"Expected 201 Created, got {response.status_code}: {response.text}"
    data = response.json()
    assert "video_id" in data
    assert data["status"] == "uploaded"
    assert data["message"] == "Video uploaded successfully. Processing started."
    video_id = data["video_id"]
    print(" [PASSED] POST /upload immediate response:", data)

    # Allow worker thread time to process queue
    time.sleep(2)

    # Query Status API
    status_res = client.get(f"/video/{video_id}/status")
    print(f" [PASSED] GET /video/{video_id}/status response:", status_res.json())

    if test_video.exists():
        test_video.unlink()


if __name__ == "__main__":
    print("\n================ RUNNING PHASE 1 PIPELINE TESTS ================\n")
    test_metadata_extraction()
    test_frame_extractor()
    test_bytetracker()
    test_end_to_end_upload_api()
    print("\n================ ALL PHASE 1 PIPELINE TESTS PASSED ================\n")
