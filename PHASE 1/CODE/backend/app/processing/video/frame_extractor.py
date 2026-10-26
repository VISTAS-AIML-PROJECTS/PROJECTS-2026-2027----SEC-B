import os
import logging
import subprocess
from pathlib import Path
from typing import List
import cv2
import imageio_ffmpeg
from app.core.config import settings
from app.models.schemas import FrameMetadata

logger = logging.getLogger("chronolens.processing.frame_extractor")


class FrameExtractor:
    @staticmethod
    def extract_frames_1fps(video_path: Path, video_id: str) -> List[FrameMetadata]:
        """
        Extracts frames at 1 frame per second into storage/frames/{videoId}/.
        Returns a list of FrameMetadata entries.
        """
        output_dir = settings.FRAMES_DIR / video_id
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"[FrameExtractor] Starting 1 FPS frame extraction for video_id={video_id}")
        
        frames_list: List[FrameMetadata] = []

        # Attempt FFmpeg extraction first
        ffmpeg_exe = None
        try:
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            ffmpeg_exe = "ffmpeg"

        cmd = [
            ffmpeg_exe,
            "-y",
            "-i", str(video_path),
            "-vf", "fps=1",
            "-q:v", "2",
            str(output_dir / "frame_%04d.jpg")
        ]

        ffmpeg_success = False
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            ffmpeg_success = True
            logger.info(f"[FrameExtractor] FFmpeg frame extraction completed successfully for {video_id}")
        except Exception as e:
            logger.warning(f"[FrameExtractor] FFmpeg CLI failed/missing ({str(e)}). Falling back to OpenCV extraction.")

        # Fallback to OpenCV frame extraction if FFmpeg CLI failed
        if not ffmpeg_success or len(list(output_dir.glob("frame_*.jpg"))) == 0:
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                raise RuntimeError(f"FFmpeg and OpenCV both failed to read video {video_path}")

            fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
            frame_interval = int(round(fps)) if fps > 0 else 25
            
            frame_idx = 0
            extracted_count = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_idx % frame_interval == 0:
                    extracted_count += 1
                    frame_filename = f"frame_{extracted_count:04d}.jpg"
                    frame_path = output_dir / frame_filename
                    cv2.imwrite(str(frame_path), frame)

                frame_idx += 1
            
            cap.release()
            logger.info(f"[FrameExtractor] OpenCV extracted {extracted_count} frames at 1 FPS.")

        # Gather extracted frame files and create metadata
        extracted_files = sorted(list(output_dir.glob("frame_*.jpg")))
        for idx, img_path in enumerate(extracted_files, start=1):
            timestamp = float(idx - 1)  # 1 FPS implies frame 1 = 0.0s, frame 2 = 1.0s...
            frames_list.append(
                FrameMetadata(
                    frameNumber=idx,
                    timestamp=timestamp,
                    imagePath=str(img_path),
                    videoId=video_id
                )
            )

        logger.info(f"[FrameExtractor] Total extracted frames: {len(frames_list)}")
        return frames_list
