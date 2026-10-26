import os
import logging
from pathlib import Path
from typing import List, Optional, Tuple
import cv2
import numpy as np
from app.core.config import settings

logger = logging.getLogger("chronolens.processing.debug.crop_generator")


class ObjectCropGenerator:
    @staticmethod
    def get_or_create_crop(
        video_id: str,
        track_id: int,
        frame_number: int,
        bbox: List[float],
        image_path: str = "",
        padding_pct: float = 0.10
    ) -> Tuple[str, Optional[np.ndarray]]:
        """
        Lazily crops detected object from frame image using stored bounding box [x1, y1, x2, y2].
        Adds padding_pct (10% default) bounded by frame dimensions.
        Returns (crop_url, crop_img_bgr_array).
        """
        crop_dir = settings.DEBUG_DIR / video_id / "tracks" / str(track_id)
        crop_dir.mkdir(parents=True, exist_ok=True)

        crop_filename = f"frame_{frame_number:04d}.jpg"
        crop_file_path = crop_dir / crop_filename
        crop_url = f"/static/storage/debug/{video_id}/tracks/{track_id}/{crop_filename}"

        # Lazy caching check: reuse existing crop if valid non-empty file exists
        if crop_file_path.exists() and crop_file_path.stat().st_size > 100:
            crop_img = cv2.imread(str(crop_file_path))
            if crop_img is not None and crop_img.size > 0:
                return crop_url, crop_img

        # Check source image existence
        if not image_path:
            image_path = str(settings.DEBUG_DIR / video_id / "frames" / f"frame_{frame_number:04d}.jpg")

        src_path = Path(image_path)
        if not src_path.exists():
            debug_frame = settings.DEBUG_DIR / video_id / "frames" / f"frame_{frame_number:04d}.jpg"
            frames_dir_path = settings.FRAMES_DIR / video_id / f"frame_{frame_number:04d}.jpg"
            if debug_frame.exists():
                src_path = debug_frame
            elif frames_dir_path.exists():
                src_path = frames_dir_path
            else:
                alt_path = settings.BASE_DIR / image_path
                if alt_path.exists():
                    src_path = alt_path
                else:
                    logger.warning(f"[CropGenerator] Original frame not found for crop: {image_path}")
                    return crop_url, None

        img = cv2.imread(str(src_path))
        if img is None:
            logger.warning(f"[CropGenerator] Failed to read image for crop: {src_path}")
            return crop_url, None

        h, w = img.shape[:2]
        if len(bbox) < 4:
            bbox = [0, 0, w, h]

        v1, v2, v3, v4 = [float(v) for v in bbox[:4]]

        # Handle normalized [0, 1] bounding box coordinates automatically
        if max(v3, v4) <= 1.5:
            v1, v2, v3, v4 = v1 * w, v2 * h, v3 * w, v4 * h

        # Detect [x, y, w, h] COCO format vs [x1, y1, x2, y2] VOC format:
        # If v3 <= v1 or (v3 < w and v4 < h and v3 > 0 and v4 > 0 and (v3 + v1 > w or v3 < (v1 / 2))):
        # If v3 < v1, it is explicitly [x, y, w, h].
        # If v3 > v1 and v3 < v1 + 5: it might be narrow box, but if v3 is width, x2 = v1 + v3.
        if v3 <= v1:
            x1, y1, x2, y2 = v1, v2, v1 + v3, v2 + v4
        else:
            x1, y1, x2, y2 = v1, v2, v3, v4

        box_w = max(1.0, x2 - x1)
        box_h = max(1.0, y2 - y1)

        pad_w = box_w * padding_pct
        pad_h = box_h * padding_pct

        px1 = max(0, int(x1 - pad_w))
        py1 = max(0, int(y1 - pad_h))
        px2 = min(w, int(x2 + pad_w))
        py2 = min(h, int(y2 + pad_h))

        # Ensure valid crop slice dimensions
        if px2 <= px1 or py2 <= py1:
            px1, py1, px2, py2 = max(0, int(x1)), max(0, int(y1)), min(w, int(x2)), min(h, int(y2))

        if px2 <= px1 or py2 <= py1:
            px1, py1, px2, py2 = 0, 0, w, h

        crop = img[py1:py2, px1:px2]
        if crop is None or crop.size == 0:
            crop = img

        # Preserve aspect ratio while scaling longer side to max 512px for compact storage
        crop_h, crop_w = crop.shape[:2]
        max_dim = 512
        if max(crop_h, crop_w) > max_dim:
            scale = max_dim / float(max(crop_h, crop_w))
            new_w = max(1, int(round(crop_w * scale)))
            new_h = max(1, int(round(crop_h * scale)))
            crop = cv2.resize(crop, (new_w, new_h), interpolation=cv2.INTER_AREA)

        cv2.imwrite(str(crop_file_path), crop)
        logger.debug(f"[CropGenerator] Saved object crop for video {video_id} track {track_id} frame {frame_number}")

        return crop_url, crop
