import os
import time
import subprocess
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

import cv2
from app.core.config import settings
from app.database.mongo import mongo_db

logger = logging.getLogger("chronolens.services.clip_generator")

CLIP_BEFORE_SECONDS = 5.0
CLIP_AFTER_SECONDS = 5.0


class ClipGeneratorService:
    """
    Query-Result Video Clip Generation Service.
    Extracts playable H.264 MP4 video clips covering the relevant time around matched events.
    Uses FFmpeg with fast input seeking, lazy caching, and deterministic naming.
    """

    @classmethod
    def get_source_video_path(cls, video_id: str) -> Optional[Path]:
        if not video_id:
            return None

        # 1. Query MongoDB videos collection for stored path or filename
        if mongo_db.db is not None:
            try:
                v_doc = mongo_db.db.videos.find_one({"videoId": video_id}, {"_id": 0})
                if v_doc:
                    for field in ["storedFilePath", "sourcePath", "filePath"]:
                        p_val = v_doc.get(field)
                        if p_val and Path(p_val).exists():
                            return Path(p_val)
                    
                    for fn_field in ["storedFilename", "filename", "originalFileName"]:
                        fn = v_doc.get(fn_field)
                        if fn:
                            p_upload = settings.UPLOADS_DIR / fn
                            if p_upload.exists():
                                return p_upload
                            if Path(fn).exists():
                                return Path(fn)
            except Exception as e:
                logger.warning(f"[ClipGenerator] Mongo lookup failed for {video_id}: {e}")

        # 2. Check UPLOADS_DIR for matching video_id file
        if settings.UPLOADS_DIR.exists():
            for ext in [".mp4", ".avi", ".mov", ".mkv"]:
                p_exact = settings.UPLOADS_DIR / f"{video_id}{ext}"
                if p_exact.is_file():
                    return p_exact
            for p in settings.UPLOADS_DIR.glob(f"{video_id}*"):
                if p.is_file() and p.suffix.lower() in {".mp4", ".avi", ".mov", ".mkv"}:
                    return p
            short_id = video_id.split("-")[0] if "-" in video_id else video_id[:8]
            if len(short_id) >= 4:
                for p in settings.UPLOADS_DIR.glob(f"*{short_id}*"):
                    if p.is_file() and p.suffix.lower() in {".mp4", ".avi", ".mov", ".mkv"}:
                        return p

        # 3. Check VIDEOS_DIR / video_id
        if settings.VIDEOS_DIR.exists():
            v_sub = settings.VIDEOS_DIR / video_id
            if v_sub.exists():
                for p in v_sub.glob("*"):
                    if p.is_file() and p.suffix.lower() in {".mp4", ".avi", ".mov", ".mkv"}:
                        return p
            for p in settings.VIDEOS_DIR.glob(f"{video_id}*"):
                if p.is_file() and p.suffix.lower() in {".mp4", ".avi", ".mov", ".mkv"}:
                    return p

        # 4. Fallback: If single video file exists in UPLOADS_DIR, use it
        if settings.UPLOADS_DIR.exists():
            uploads_videos = [
                p for p in settings.UPLOADS_DIR.iterdir()
                if p.is_file() and p.suffix.lower() in {".mp4", ".avi", ".mov", ".mkv"}
            ]
            if len(uploads_videos) == 1:
                logger.info(f"[ClipGenerator] Using single uploaded video fallback: {uploads_videos[0]}")
                return uploads_videos[0]

        return None

    @classmethod
    def get_video_duration(cls, video_id: str, source_path: Path) -> float:
        if mongo_db.db is not None:
            try:
                v_doc = mongo_db.db.videos.find_one({"videoId": video_id}, {"_id": 0})
                if v_doc and v_doc.get("duration"):
                    return float(v_doc["duration"])
            except Exception:
                pass

        try:
            cap = cv2.VideoCapture(str(source_path))
            if cap.isOpened():
                fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
                frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0
                cap.release()
                if fps > 0 and frame_count > 0:
                    return float(frame_count / fps)
        except Exception as e:
            logger.warning(f"[ClipGenerator] Failed to get OpenCV duration for {source_path}: {str(e)}")

        return 0.0

    @classmethod
    def generate_result_clip(
        cls,
        video_id: str,
        match_timestamp: float,
        identifier_tag: str,
        start_override: Optional[float] = None,
        end_override: Optional[float] = None,
        precise_mode: bool = False
    ) -> Tuple[Optional[str], float, float, float]:
        """
        Generates or reuses a trimmed H.264 MP4 clip centered around match_timestamp,
        or bounded by start_override / end_override (e.g. for speech segments).

        If precise_mode is True (e.g. for SPEECH / Whisper clips):
          Prioritizes frame-accurate re-encoding (-c:v libx264 -preset ultrafast -crf 23 -c:a aac)
          on ONLY the short evidence segment so timestamps match exact audio.
          Falls back to fast stream copy (-c copy) if re-encoding fails.
        Otherwise (default):
          Uses fast stream copy (-c copy) for maximum speed.
        """
        source_path = cls.get_source_video_path(video_id)
        if not source_path or not source_path.exists():
            logger.warning(f"[ClipGenerator] Source video for '{video_id}' not found. Cannot extract clip.")
            return None, 0.0, 0.0, 0.0

        video_dur = cls.get_video_duration(video_id, source_path)

        if video_dur > 0.0:
            match_timestamp = min(max(0.0, match_timestamp), max(0.0, video_dur - 1.0))

        if start_override is not None and end_override is not None:
            start_time = max(0.0, float(start_override))
            end_time = float(end_override)
            if video_dur > 0.0:
                end_time = min(video_dur, end_time)
        else:
            start_time = max(0.0, match_timestamp - CLIP_BEFORE_SECONDS)
            end_time = match_timestamp + CLIP_AFTER_SECONDS
            if video_dur > 0.0:
                end_time = min(video_dur, end_time)
                if start_time >= video_dur:
                    start_time = max(0.0, video_dur - CLIP_BEFORE_SECONDS)

        if end_time <= start_time:
            end_time = min(video_dur, start_time + 1.0) if video_dur > 0.0 else start_time + 1.0

        duration = round(end_time - start_time, 2)
        start_time = round(start_time, 2)
        end_time = round(end_time, 2)

        # Deterministic filename incorporating videoId, mode, tag, and exact timestamps
        clean_tag = str(identifier_tag).replace(" ", "_").replace("/", "_")
        mode_prefix = "precise" if precise_mode else "fast"
        clip_filename = f"{video_id}_{mode_prefix}_{clean_tag}_{start_time}s_{end_time}s.mp4"
        
        clips_dir = settings.CLIPS_DIR
        clips_dir.mkdir(parents=True, exist_ok=True)

        clip_path = clips_dir / clip_filename
        clip_url = f"/static/storage/clips/{clip_filename}"

        # Lazy Caching Check: reuse existing clip if file is valid
        if clip_path.exists() and clip_path.stat().st_size > 100:
            logger.info(f"[ClipGenerator] Reusing cached ({mode_prefix}) clip: {clip_filename}")
            return clip_url, start_time, end_time, duration

        # Resolve FFmpeg executable
        try:
            import imageio_ffmpeg
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            ffmpeg_exe = "ffmpeg"

        cmd_copy = [
            ffmpeg_exe, "-y",
            "-ss", str(start_time),
            "-i", str(source_path),
            "-t", str(duration),
            "-c", "copy",
            "-avoid_negative_ts", "make_zero",
            str(clip_path)
        ]

        cmd_precise = [
            ffmpeg_exe, "-y",
            "-ss", str(start_time),
            "-i", str(source_path),
            "-t", str(duration),
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "23",
            "-c:a", "aac",
            "-avoid_negative_ts", "make_zero",
            "-movflags", "+faststart",
            str(clip_path)
        ]

        # ── HYBRID CLIP STRATEGY ─────────────────────────────────────────────
        if precise_mode:
            # 1. Try precise re-encoding first for speech evidence
            logger.info(f"[ClipGenerator] Extracting PRECISE speech clip '{clip_filename}' (start={start_time}s, end={end_time}s, dur={duration}s)...")
            try:
                res = subprocess.run(cmd_precise, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=12)
                if res.returncode == 0 and clip_path.exists() and clip_path.stat().st_size > 100:
                    logger.info(f"[ClipGenerator] Successfully generated precise speech clip: {clip_filename}")
                    return clip_url, start_time, end_time, duration
            except Exception as pe:
                logger.warning(f"[ClipGenerator] Precise extraction failed ({pe}), falling back to fast stream copy...")

            # 2. Fallback to fast copy if precise re-encoding fails
            try:
                res = subprocess.run(cmd_copy, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
                if res.returncode == 0 and clip_path.exists() and clip_path.stat().st_size > 100:
                    logger.info(f"[ClipGenerator] Precise fallback -> generated fast clip: {clip_filename}")
                    return clip_url, start_time, end_time, duration
            except Exception:
                pass
        else:
            # Fast visual/event clip: try stream copy first for maximum speed
            logger.info(f"[ClipGenerator] Extracting FAST clip '{clip_filename}' (start={start_time}s, end={end_time}s, dur={duration}s)...")
            try:
                res = subprocess.run(cmd_copy, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
                if res.returncode == 0 and clip_path.exists() and clip_path.stat().st_size > 100:
                    logger.info(f"[ClipGenerator] Successfully generated fast clip: {clip_filename}")
                    return clip_url, start_time, end_time, duration
            except Exception:
                pass

            # Fallback to re-encoding if stream copy fails
            try:
                res = subprocess.run(cmd_precise, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
                if res.returncode == 0 and clip_path.exists() and clip_path.stat().st_size > 100:
                    logger.info(f"[ClipGenerator] Fast fallback -> generated re-encoded clip: {clip_filename}")
                    return clip_url, start_time, end_time, duration
            except Exception as e:
                logger.error(f"[ClipGenerator] Exception during FFmpeg execution for {clip_filename}: {str(e)}")

        return None, start_time, end_time, duration

