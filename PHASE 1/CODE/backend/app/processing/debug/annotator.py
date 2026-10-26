import os
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Any
import cv2
import imageio_ffmpeg
from app.core.config import settings

logger = logging.getLogger("chronolens.processing.debug.annotator")

# High-contrast vibrant neon color palette for distinct track visualization (BGR format)
TRACK_PALETTE = [
    (0, 255, 100),    # Neon Lime Green
    (255, 0, 220),    # Hot Neon Pink
    (240, 240, 0),    # Electric Cyan
    (0, 180, 255),    # Bright Amber Orange
    (255, 50, 120),   # Bright Electric Violet
    (0, 255, 255),    # Neon Yellow
    (50, 120, 255),   # Bright Flame Orange
    (255, 160, 0),    # Electric Azure Blue
]


class AnnotatedVideoGenerator:
    @staticmethod
    def generate_annotated_video(
        video_id: str,
        frames: List[Dict[str, Any]],
        detections: List[Dict[str, Any]],
        fps: float = 1.0,
        force_regenerate: bool = True
    ) -> tuple[Path, Path]:
        """
        Generates high-visibility, resolution-scaled annotated frame images with bold bounding boxes
        and encodes a Web-compatible 25 FPS H.264 MP4 video playable natively in all browsers.
        Returns (annotated_video_path, annotated_frames_dir).
        """
        debug_video_dir = settings.DEBUG_DIR / video_id
        annotated_frames_dir = debug_video_dir / "frames"
        annotated_video_path = debug_video_dir / "annotated_video.mp4"

        annotated_frames_dir.mkdir(parents=True, exist_ok=True)

        if not force_regenerate and annotated_video_path.exists() and annotated_video_path.stat().st_size > 5000 and len(list(annotated_frames_dir.glob("*.jpg"))) > 0:
            logger.info(f"[Annotator] Using cached annotated video for video_id={video_id}")
            return annotated_video_path, annotated_frames_dir

        logger.info(f"[Annotator] Generating BOLD annotated frames and Web H.264 video for video_id={video_id} across {len(frames)} frames")

        # Group detections by frame number
        detections_by_frame = {}
        for det in detections:
            frame_num = det.get("frameNumber")
            if frame_num not in detections_by_frame:
                detections_by_frame[frame_num] = []
            detections_by_frame[frame_num].append(det)

        # Sort frames by frameNumber
        sorted_frames = sorted(frames, key=lambda f: f.get("frameNumber", 0))

        for frame in sorted_frames:
            frame_num = frame.get("frameNumber")
            img_path = Path(frame.get("imagePath", ""))
            
            if not img_path.exists():
                alt_path = settings.BASE_DIR / img_path
                if alt_path.exists():
                    img_path = alt_path
                else:
                    continue

            img = cv2.imread(str(img_path))
            if img is None:
                continue

            h, w = img.shape[:2]
            max_dim = max(w, h)

            # Proportional thickness scaling for UHD / 4K frames (e.g. 14px thick on 4096px height)
            line_thickness = max(10, int(max_dim / 260))
            outer_thickness = line_thickness + 6
            font_scale = max(1.1, max_dim / 1000)
            font_thickness = max(3, int(line_thickness / 3))

            # Draw detections for this frame
            frame_dets = detections_by_frame.get(frame_num, [])
            for det in frame_dets:
                box = det.get("boundingBox", [0, 0, 0, 0])
                obj_cls = det.get("objectClass", "object")
                conf = float(det.get("confidence", 0.0))
                raw_track_id = det.get("trackId", "N/A")

                try:
                    t_id_num = int(raw_track_id)
                    color = TRACK_PALETTE[(t_id_num - 1) % len(TRACK_PALETTE)]
                except (ValueError, TypeError):
                    color = (0, 255, 100)

                x1, y1, x2, y2 = [int(round(v)) for v in box]

                # Clamp box coordinates strictly to image dimensions
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w, x2), min(h, y2)

                if x2 <= x1 or y2 <= y1:
                    continue

                # 1. Outer Black Contrast Outline for high visibility over bright/dark backgrounds
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 0), outer_thickness)

                # 2. Main Vivid Bounding Box Rectangle
                cv2.rectangle(img, (x1, y1), (x2, y2), color, line_thickness)

                # 3. Corner Accent Brackets for bold AI target highlighting
                corner_len = min(int((x2 - x1) * 0.2), int((y2 - y1) * 0.2), 60)
                if corner_len > 10:
                    c_thick = line_thickness + 2
                    # Top-Left
                    cv2.line(img, (x1, y1), (x1 + corner_len, y1), (255, 255, 255), c_thick)
                    cv2.line(img, (x1, y1), (x1, y1 + corner_len), (255, 255, 255), c_thick)
                    # Top-Right
                    cv2.line(img, (x2, y1), (x2 - corner_len, y1), (255, 255, 255), c_thick)
                    cv2.line(img, (x2, y1), (x2, y1 + corner_len), (255, 255, 255), c_thick)
                    # Bottom-Left
                    cv2.line(img, (x1, y2), (x1 + corner_len, y2), (255, 255, 255), c_thick)
                    cv2.line(img, (x1, y2), (x1, y2 - corner_len), (255, 255, 255), c_thick)
                    # Bottom-Right
                    cv2.line(img, (x2, y2), (x2 - corner_len, y2), (255, 255, 255), c_thick)
                    cv2.line(img, (x2, y2), (x2, y2 - corner_len), (255, 255, 255), c_thick)

                # 4. Text Label Header formatting
                label = f"{obj_cls.upper()} | ID: #{raw_track_id} | {conf:.2f}"
                (text_w, text_h), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_thickness)
                
                pad = int(line_thickness * 1.2)
                lbl_y1 = max(0, y1 - text_h - (pad * 2))
                lbl_y2 = max(text_h + (pad * 2), y1)

                # Label Box Solid Background with Contrast Outline
                cv2.rectangle(img, (x1, lbl_y1), (x1 + text_w + (pad * 2), lbl_y2), (0, 0, 0), -1)
                cv2.rectangle(img, (x1, lbl_y1), (x1 + text_w + (pad * 2), lbl_y2), color, max(2, int(line_thickness / 2)))

                # White Text Overlay
                cv2.putText(
                    img,
                    label,
                    (x1 + pad, lbl_y2 - pad),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    font_scale,
                    (255, 255, 255),
                    font_thickness,
                    lineType=cv2.LINE_AA
                )

            # Save annotated frame image
            annotated_frame_name = f"frame_{frame_num:04d}.jpg"
            annotated_frame_file = annotated_frames_dir / annotated_frame_name
            cv2.imwrite(str(annotated_frame_file), img)

        # Assemble Web-compatible 25 FPS H.264 MP4 video using FFmpeg
        ffmpeg_exe = None
        try:
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            ffmpeg_exe = "ffmpeg"

        # -r 25 and -g 25 keyframes ensure instant HTML5 video player buffering and playback
        cmd = [
            ffmpeg_exe,
            "-y",
            "-framerate", str(max(1.0, float(fps))),
            "-i", str(annotated_frames_dir / "frame_%04d.jpg"),
            "-vf", "scale=-2:'min(1080,ih)'",
            "-r", "25",
            "-g", "25",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "ultrafast",
            "-crf", "22",
            "-movflags", "+faststart",
            str(annotated_video_path)
        ]

        try:
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            logger.info(f"[Annotator] Bold H.264 25 FPS Web video compiled successfully at {annotated_video_path}")
        except Exception as e:
            logger.warning(f"[Annotator] FFmpeg web encoding failed ({str(e)}). Falling back to basic H.264.")
            cmd_fallback = [
                ffmpeg_exe,
                "-y",
                "-framerate", str(max(1.0, float(fps))),
                "-i", str(annotated_frames_dir / "frame_%04d.jpg"),
                "-r", "25",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                str(annotated_video_path)
            ]
            subprocess.run(cmd_fallback, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        return annotated_video_path, annotated_frames_dir
