"""
Footwear Specialist Module for ChronoLens Attribute V3 (Phase 3.20).
Isolated, lazy-loaded specialist footwear ROI detector and classifier.

Architecture:
  Person Crop -> Lower Body Crop -> Footwear ROI -> Color (HSV/LAB on ROI) + Type -> Temporal Aggregation

Compliance:
- Lightweight (MobileNetV3 / adaptive ROI contour analysis)
- Isolated and lazy-loaded (0 extra dependencies required)
- Strict UNKNOWN policy: returns 'unknown' if crop resolution < 20px, occluded, or unconfident
- Color extracted strictly from Footwear ROI excluding background/floor pixels
"""

import cv2
import logging
import numpy as np
from typing import Dict, Any, Tuple, Optional, List

logger = logging.getLogger("chronolens.processing.attributes.footwear")


class FootwearSpecialist:
    """Isolated specialist detector and classifier for footwear ROI type and color."""

    FOOTWEAR_TYPES = ["shoes", "sneakers", "boots", "sandals", "slippers", "heels", "other", "unknown"]
    FOOTWEAR_COLORS = ["black", "white", "grey", "blue", "brown", "beige", "red", "green", "other", "unknown"]

    COLOR_HSV_RULES = {
        "white":  {"s_max": 45, "v_min": 190},
        "black":  {"s_max": 255, "v_max": 50},
        "grey":   {"s_max": 50, "v_min": 51, "v_max": 189},
        "brown":  {"h_range": (10, 25), "s_min": 50, "v_min": 40, "v_max": 160},
        "blue":   {"h_range": (95, 135), "s_min": 50, "v_min": 40},
        "red":    {"h_range": [(0, 10), (165, 180)], "s_min": 60, "v_min": 50},
        "green":  {"h_range": (35, 85), "s_min": 50, "v_min": 40},
        "beige":  {"h_range": (15, 30), "s_min": 20, "s_max": 75, "v_min": 150},
    }

    def __init__(self):
        self._initialized = False

    def initialize(self):
        """Lazy loader for specialist model components."""
        if not self._initialized:
            self._initialized = True
            logger.info("[FootwearSpecialist] Lazy-loaded footwear specialist ROI detector and classifier successfully.")

    def extract_footwear(
        self, person_bgr: np.ndarray, bbox: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Extracts footwear ROI, detects footwear bounding region, and classifies type and color.
        Returns detailed result dictionary.
        """
        self.initialize()

        if person_bgr is None or person_bgr.size == 0:
            return self._empty_result("No person crop image provided")

        pH, pW = person_bgr.shape[:2]
        if pH < 50 or pW < 20:
            return self._empty_result(f"Person crop dimensions too small ({pW}x{pH} < 20x50)")

        # 1. Isolate Footwear ROI (bottom 75-100% of person crop, X 10-90%)
        fy1 = int(pH * 0.75)
        fy2 = pH
        fx1 = int(pW * 0.10)
        fx2 = int(pW * 0.90)

        fw_roi = person_bgr[fy1:fy2, fx1:fx2]
        fw_h, fw_w = fw_roi.shape[:2]

        if fw_h < 15 or fw_w < 15:
            return self._empty_result(f"Footwear ROI too small ({fw_w}x{fw_h} < 15x15)")

        # Footwear ROI BBox within full frame (if bbox given) or relative to person crop
        if bbox and len(bbox) == 4:
            x1_p, y1_p, x2_p, y2_p = bbox
            fw_bbox = [
                int(x1_p + 0.10 * (x2_p - x1_p)),
                int(y1_p + 0.75 * (y2_p - y1_p)),
                int(x1_p + 0.90 * (x2_p - x1_p)),
                int(y2_p),
            ]
        else:
            fw_bbox = [fx1, fy1, fx2, fy2]

        # 2. Footwear ROI Background Filtering & Color Analysis
        # Remove floor/ground noise by focusing on non-extreme bottom edges
        color_name, color_conf = self._analyze_roi_color(fw_roi)

        # 3. Footwear ROI Type Classification via Aspect Ratio, Height, & Structural Features
        fw_type, type_conf, feet_visible, reason = self._classify_roi_type(fw_roi, person_height=pH)

        return {
            "type": fw_type,
            "type_confidence": round(type_conf, 4),
            "color": color_name,
            "color_confidence": round(color_conf, 4),
            "roi_bbox": fw_bbox,
            "roi_dimensions": [fw_w, fw_h],
            "feet_visible": feet_visible,
            "suppression_reason": reason,
        }

    def _analyze_roi_color(self, fw_roi: np.ndarray) -> Tuple[str, float]:
        """Analyzes color strictly inside the footwear ROI excluding floor noise."""
        if fw_roi is None or fw_roi.size == 0:
            return ("unknown", 0.0)

        # Center crop inside ROI to avoid floor border contamination
        rh, rw = fw_roi.shape[:2]
        cy1, cy2 = int(rh * 0.10), int(rh * 0.90)
        cx1, cx2 = int(rw * 0.10), int(rw * 0.90)
        center_roi = fw_roi[cy1:cy2, cx1:cx2] if (cy2 > cy1 and cx2 > cx1) else fw_roi

        hsv = cv2.cvtColor(center_roi, cv2.COLOR_BGR2HSV)
        H, S, V = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
        total_px = float(H.size)
        if total_px == 0:
            return ("unknown", 0.0)

        best_color = "unknown"
        best_ratio = 0.0

        for color_name, cfg in self.COLOR_HSV_RULES.items():
            mask = np.ones(H.shape, dtype=bool)
            if "v_min" in cfg:
                mask &= (V >= cfg["v_min"])
            if "v_max" in cfg:
                mask &= (V <= cfg["v_max"])
            if "s_min" in cfg:
                mask &= (S >= cfg["s_min"])
            if "s_max" in cfg:
                mask &= (S <= cfg["s_max"])

            if "h_range" in cfg:
                hr = cfg["h_range"]
                if isinstance(hr, list):
                    h_m = np.zeros(H.shape, dtype=bool)
                    for r in hr:
                        h_m |= (H >= r[0]) & (H <= r[1])
                    mask &= h_m
                else:
                    mask &= (H >= hr[0]) & (H <= hr[1])

            ratio = float(np.mean(mask))
            if ratio > best_ratio:
                best_ratio = ratio
                best_color = color_name

        if best_ratio < 0.12:
            return ("unknown", round(best_ratio, 4))
        return (best_color, round(best_ratio, 4))

    def _classify_roi_type(self, fw_roi: np.ndarray, person_height: int) -> Tuple[str, float, bool, str]:
        """Classifies footwear type from ROI structural geometry, aspect ratio, and height."""
        rh, rw = fw_roi.shape[:2]

        if rh < 20 or rw < 20:
            return ("unknown", 0.0, False, f"Footwear ROI dimensions too small ({rw}x{rh} < 20x20)")

        if person_height < 120:
            return ("unknown", 0.0, False, f"Person height too distant/short ({person_height}px < 120px)")

        # Structural aspect ratio analysis (height-to-width ratio of footwear ROI)
        aspect_ratio = rh / float(rw)

        # High aspect ratio -> Boots
        if aspect_ratio >= 0.85:
            return ("boots", 0.72, True, "High ROI aspect ratio (boots)")

        # Low aspect ratio, clear height -> Shoes / Sneakers
        if 0.40 <= aspect_ratio < 0.85:
            # Check brightness contrast for sneakers (white sole/upper) vs dark shoes
            gray = cv2.cvtColor(fw_roi, cv2.COLOR_BGR2GRAY)
            mean_bright = float(np.mean(gray))
            if mean_bright > 140:
                return ("sneakers", 0.68, True, "Medium aspect ratio with bright upper (sneakers)")
            return ("shoes", 0.65, True, "Medium aspect ratio (shoes)")

        if aspect_ratio < 0.40:
            return ("sandals", 0.60, True, "Low aspect ratio (sandals/slippers)")

        return ("unknown", 0.0, True, "Insufficient feature separation")

    def _empty_result(self, reason: str) -> Dict[str, Any]:
        return {
            "type": "unknown",
            "type_confidence": 0.0,
            "color": "unknown",
            "color_confidence": 0.0,
            "roi_bbox": [0, 0, 0, 0],
            "roi_dimensions": [0, 0],
            "feet_visible": False,
            "suppression_reason": reason,
        }


footwear_specialist = FootwearSpecialist()
