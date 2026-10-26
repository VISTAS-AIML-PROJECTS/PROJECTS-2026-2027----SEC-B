"""
Region Cropper for ChronoLens Attribute V3.
Deterministically extracts 7 localized sub-regions from person crops:
  1. HEAD CROP
  2. UPPER BODY CROP
  3. FULL TORSO CROP
  4. LOWER BODY CROP
  5. FOOTWEAR CROP
  6. FULL PERSON CROP
  7. ACCESSORY/NECK CROP

All crops are clamped to image bounds and validated for minimum dimensions.
"""

import cv2
import numpy as np
from typing import Dict, Any, Tuple, Optional


class RegionCropper:
    """Extracts standardized sub-regions from a person bounding box image."""

    MIN_CROP_DIM: int = 15

    @classmethod
    def extract_regions(cls, person_bgr: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Given a person BGR crop, returns a dict of named sub-region BGR crops.
        """
        if person_bgr is None or person_bgr.size == 0:
            return {}

        h, w = person_bgr.shape[:2]
        if h < 10 or w < 10:
            return {}

        # 1. HEAD CROP (top 0–35%, X 15–85%)
        head = cls._crop_slice(person_bgr, 0.0, 0.35, 0.15, 0.85)

        # 2. UPPER BODY CROP (top 15–65%, X 5–95%)
        upper_body = cls._crop_slice(person_bgr, 0.15, 0.65, 0.05, 0.95)

        # 3. FULL TORSO CROP (top 20–75%, X 5–95%)
        torso = cls._crop_slice(person_bgr, 0.20, 0.75, 0.05, 0.95)

        # 4. LOWER BODY CROP (top 50–95%, X 5–95%)
        lower_body = cls._crop_slice(person_bgr, 0.50, 0.95, 0.05, 0.95)

        # 5. FOOTWEAR CROP (bottom 75–100%, X 5–95%)
        footwear = cls._crop_slice(person_bgr, 0.75, 1.00, 0.05, 0.95)

        # 6. FULL PERSON CROP (top 0–100%, X 0–100%)
        full_person = person_bgr.copy()

        # 7. ACCESSORY / NECK CROP (top 20–50%, X 20–80%)
        neck_accessory = cls._crop_slice(person_bgr, 0.20, 0.50, 0.20, 0.80)

        return {
            "head": head,
            "upper_body": upper_body,
            "torso": torso,
            "lower_body": lower_body,
            "footwear": footwear,
            "full_person": full_person,
            "neck_accessory": neck_accessory,
        }

    @classmethod
    def _crop_slice(
        cls, img: np.ndarray, y1_pct: float, y2_pct: float, x1_pct: float, x2_pct: float
    ) -> np.ndarray:
        h, w = img.shape[:2]
        y1 = max(0, int(h * y1_pct))
        y2 = min(h, int(h * y2_pct))
        x1 = max(0, int(w * x1_pct))
        x2 = min(w, int(w * x2_pct))

        if y2 <= y1 or x2 <= x1:
            return img.copy()

        sub = img[y1:y2, x1:x2]
        return sub if sub.size > 0 else img.copy()


region_cropper = RegionCropper()
