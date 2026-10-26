import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import cv2
import numpy as np

from app.core.config import settings

logger = logging.getLogger("chronolens.processing.ocr")


class OcrAnnotator:
    """
    Dedicated OCR Evidence Annotator.
    Highlights recognized text bounding boxes and labels cleanly on evidence frames.
    Saves evidence image to storage/debug/{videoId}/ocr/ or returns annotated BGR image.
    """

    @classmethod
    def annotate_frame(
        cls,
        image_input: Any,
        video_id: str,
        frame_number: int,
        detections: List[Dict[str, Any]],
        output_dir: Optional[Path] = None,
        target_text: Optional[str] = None,
        target_bbox: Optional[List[float]] = None
    ) -> Optional[str]:
        """
        Draws bounding box(es) and text label(s) for OCR detections.
        Strongly highlights target matched text in Gold/Cyan while muting secondary detections.
        Returns the static URL or file path of the saved annotated frame.
        """
        try:
            if isinstance(image_input, (str, Path)):
                img = cv2.imread(str(image_input))
            elif isinstance(image_input, np.ndarray):
                img = image_input.copy()
            else:
                return None

            if img is None:
                return None

            h, w = img.shape[:2]
            q_target = target_text.lower().strip() if target_text else ""

            # Draw secondary (unmatched) detections first in muted gray
            for det in detections:
                bbox = det.get("bbox", [])
                text = str(det.get("text", "")).strip()
                conf = float(det.get("confidence", 0.0))
                
                is_match = False
                if q_target and (q_target in text.lower() or q_target in det.get("normalizedText", "").lower()):
                    is_match = True

                if len(bbox) == 4 and not is_match:
                    x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
                    x1, y1 = max(0, min(w - 1, x1)), max(0, min(h - 1, y1))
                    x2, y2 = max(x1 + 1, min(w, x2)), max(y1 + 1, min(h, y2))
                    cv2.rectangle(img, (x1, y1), (x2, y2), (100, 100, 100), 1)

            # Draw target matched detections in Gold/Cyan
            for det in detections:
                bbox = det.get("bbox", [])
                text = str(det.get("text", "")).strip()
                conf = float(det.get("confidence", 0.0))
                
                is_match = False
                if q_target and (q_target in text.lower() or q_target in det.get("normalizedText", "").lower()):
                    is_match = True
                elif not q_target:
                    is_match = True

                if len(bbox) == 4 and is_match:
                    x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
                    x1, y1 = max(0, min(w - 1, x1)), max(0, min(h - 1, y1))
                    x2, y2 = max(x1 + 1, min(w, x2)), max(y1 + 1, min(h, y2))

                    box_color = (255, 215, 0)  # Gold/Cyan BGR
                    cv2.rectangle(img, (x1, y1), (x2, y2), box_color, 3)

                    label_str = f"OCR Match: {text} ({round(conf * 100)}%)"
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    font_scale = 0.55
                    thickness = 2
                    (text_w, text_h), baseline = cv2.getTextSize(label_str, font, font_scale, thickness)

                    label_y1 = max(0, y1 - text_h - 8)
                    label_y2 = y1
                    cv2.rectangle(img, (x1, label_y1), (x1 + text_w + 6, label_y2), box_color, cv2.FILLED)
                    cv2.putText(
                        img,
                        label_str,
                        (x1 + 3, label_y2 - 4),
                        font,
                        font_scale,
                        (0, 0, 0),
                        thickness,
                        cv2.LINE_AA
                    )

            # Draw composite phrase bounding box if provided (Tier 3 reconstructed phrase)
            if target_bbox and len(target_bbox) == 4:
                x1, y1, x2, y2 = int(target_bbox[0]), int(target_bbox[1]), int(target_bbox[2]), int(target_bbox[3])
                x1, y1 = max(0, min(w - 1, x1)), max(0, min(h - 1, y1))
                x2, y2 = max(x1 + 1, min(w, x2)), max(y1 + 1, min(h, y2))
                box_color = (0, 255, 255)  # Vibrant Yellow BGR
                cv2.rectangle(img, (x1, y1), (x2, y2), box_color, 3)

            # Determine save path
            out_dir = output_dir or (settings.STORAGE_DIR / "debug" / video_id / "ocr")
            out_dir.mkdir(parents=True, exist_ok=True)

            out_filename = f"ocr_frame_{frame_number:04d}.jpg"
            out_filepath = out_dir / out_filename
            cv2.imwrite(str(out_filepath), img)

            # Return static URL for web client
            static_url = f"/static/storage/debug/{video_id}/ocr/{out_filename}"
            return static_url

        except Exception as err:
            logger.warning(f"[OcrAnnotator] Error annotating frame {frame_number} for {video_id}: {err}")
            return None
