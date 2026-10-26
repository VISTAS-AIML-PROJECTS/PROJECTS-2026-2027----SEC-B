import os
import logging
from pathlib import Path
from datetime import datetime, timezone
import cv2
from app.models.schemas import VideoMetadata, ProcessingStatusEnum
from app.utils.file_utils import format_file_size

logger = logging.getLogger("chronolens.processing.metadata")


class MetadataExtractor:
    @staticmethod
    def extract_metadata(video_path: Path, video_id: str, original_filename: str) -> VideoMetadata:
        """
        Extracts duration, FPS, resolution, codec, file size, and upload time from a video file.
        Returns a pure VideoMetadata object.
        """
        logger.info(f"[MetadataExtractor] Extracting metadata for video_id={video_id} at {video_path}")
        
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found at {video_path}")

        file_size_bytes = video_path.stat().st_size
        formatted_size = format_file_size(file_size_bytes)

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            logger.error(f"[MetadataExtractor] OpenCV failed to open video {video_path}")
            raise ValueError(f"Corrupted Video or Unsupported Codec: {original_filename}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0
        duration = float(frame_count / fps) if fps > 0 else 0.0
        
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        resolution = f"{width}x{height}" if width and height else "1920x1080"
        
        fourcc_int = int(cap.get(cv2.CAP_PROP_FOURCC) or 0)
        codec = "".join([chr((fourcc_int >> 8 * i) & 0xFF) for i in range(4)]).strip() or "h264"
        cap.release()

        uploaded_time_str = datetime.now(timezone.utc).isoformat()

        metadata = VideoMetadata(
            videoId=video_id,
            filename=original_filename,
            duration=round(duration, 2),
            fps=round(float(fps), 2),
            resolution=resolution,
            codec=codec.lower(),
            size=formatted_size,
            uploadedAt=uploaded_time_str,
            status=ProcessingStatusEnum.METADATA_EXTRACTION
        )
        
        logger.info(f"[MetadataExtractor] Metadata extracted: {metadata.dict()}")
        return metadata
