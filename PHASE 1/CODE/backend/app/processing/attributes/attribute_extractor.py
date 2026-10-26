import logging
from typing import Dict, Any, Optional, Tuple, List
import cv2
import numpy as np
from PIL import Image

from app.services.semantic.openclip_engine import openclip_engine

logger = logging.getLogger("chronolens.processing.attributes")


COLOR_DEFINITIONS = {
    "black": {"h_min": 0, "h_max": 180, "s_min": 0, "s_max": 255, "v_min": 0, "v_max": 50},
    "white": {"h_min": 0, "h_max": 180, "s_min": 0, "s_max": 40, "v_min": 190, "v_max": 255},
    "grey":  {"h_min": 0, "h_max": 180, "s_min": 0, "s_max": 45, "v_min": 51, "v_max": 189},
    "red":   [
        {"h_min": 0, "h_max": 10, "s_min": 60, "s_max": 255, "v_min": 50, "v_max": 255},
        {"h_min": 165, "h_max": 180, "s_min": 60, "s_max": 255, "v_min": 50, "v_max": 255}
    ],
    "blue":  {"h_min": 95, "h_max": 135, "s_min": 50, "s_max": 255, "v_min": 40, "v_max": 255},
    "green": {"h_min": 35, "h_max": 85, "s_min": 50, "s_max": 255, "v_min": 40, "v_max": 255},
    "yellow":{"h_min": 14, "h_max": 36, "s_min": 45, "s_max": 255, "v_min": 90, "v_max": 255},
    "brown": {"h_min": 10, "h_max": 25, "s_min": 50, "s_max": 255, "v_min": 40, "v_max": 150}
}


_TEXT_EMB_CACHE: Dict[str, np.ndarray] = {}


def get_cached_text_embedding(text_prompt: str) -> np.ndarray:
    """Helper that caches text embeddings to eliminate redundant OpenCLIP text encoder calls."""
    if text_prompt not in _TEXT_EMB_CACHE:
        _TEXT_EMB_CACHE[text_prompt] = openclip_engine.generate_text_embedding(text_prompt)
    return _TEXT_EMB_CACHE[text_prompt]


class AttributeExtractor:
    """
    Phase 2.4 Hybrid Visual Attribute Extractor & Track-Level Aggregator.
    Combines primary OpenCV HSV color histogram analysis with OpenCLIP zero-shot semantic evidence.
    Includes region cropping for upper/lower clothing to avoid skin/background noise,
    accessory detection with thresholding, and multi-frame evidence aggregation across tracks.
    """

    @staticmethod
    def extract_opencv_dominant_color(img_bgr: np.ndarray, mask: Optional[np.ndarray] = None) -> Tuple[str, float]:
        """
        Analyzes HSV color distribution in an image region.
        Returns (dominant_color_name, primary_confidence).
        """
        if img_bgr is None or img_bgr.size == 0:
            return "unknown", 0.0

        hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
        total_pixels = hsv.shape[0] * hsv.shape[1]
        if total_pixels == 0:
            return "unknown", 0.0

        # Create skin mask to exclude skin pixels (Hue in [0..25], Sat in [20..150], Val > 60)
        lower_skin = np.array([0, 20, 60], dtype=np.uint8)
        upper_skin = np.array([25, 150, 255], dtype=np.uint8)
        skin_mask = cv2.inRange(hsv, lower_skin, upper_skin)
        non_skin_mask = cv2.bitwise_not(skin_mask)

        if mask is not None:
            combined_mask = cv2.bitwise_and(non_skin_mask, mask)
        else:
            combined_mask = non_skin_mask

        valid_pixels = cv2.countNonZero(combined_mask)
        if valid_pixels == 0:
            combined_mask = mask if mask is not None else np.ones(hsv.shape[:2], dtype=np.uint8) * 255
            valid_pixels = max(1, cv2.countNonZero(combined_mask))

        color_counts = {}
        for cname, defs in COLOR_DEFINITIONS.items():
            if isinstance(defs, list):
                m1 = cv2.inRange(hsv, np.array([defs[0]["h_min"], defs[0]["s_min"], defs[0]["v_min"]]), np.array([defs[0]["h_max"], defs[0]["s_max"], defs[0]["v_max"]]))
                m2 = cv2.inRange(hsv, np.array([defs[1]["h_min"], defs[1]["s_min"], defs[1]["v_min"]]), np.array([defs[1]["h_max"], defs[1]["s_max"], defs[1]["v_max"]]))
                c_mask = cv2.bitwise_or(m1, m2)
            else:
                c_mask = cv2.inRange(hsv, np.array([defs["h_min"], defs["s_min"], defs["v_min"]]), np.array([defs["h_max"], defs["s_max"], defs["v_max"]]))

            matched_mask = cv2.bitwise_and(c_mask, combined_mask)
            count = cv2.countNonZero(matched_mask)
            color_counts[cname] = count

        best_color = max(color_counts, key=color_counts.get)
        best_count = color_counts[best_color]
        confidence = round(float(best_count) / float(valid_pixels), 4)

        if confidence < 0.12:
            return "unknown", confidence

        return best_color, min(1.0, confidence)

    @classmethod
    def extract_person_attributes(
        cls,
        crop_bgr: np.ndarray,
        track_id: int,
        supporting_frame: int,
        existing_crop_url: Optional[str] = None,
        crop_emb: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        Extracts upper/lower clothing colors and accessories for a single person crop.
        Splits crop internally into upper (15-48% height) and lower (45-88% height) regions.
        """
        if crop_bgr is None or crop_bgr.size == 0 or crop_bgr.shape[0] < 20 or crop_bgr.shape[1] < 10:
            return {
                "trackId": track_id,
                "objectClass": "person",
                "upperClothingColor": "unknown",
                "upperClothingConfidence": 0.0,
                "lowerClothingColor": "unknown",
                "lowerClothingConfidence": 0.0,
                "hasBackpack": False,
                "backpackConfidence": 0.0,
                "hasHelmet": False,
                "hasHat": False,
                "hasGlasses": False,
                "supportingFrame": supporting_frame,
                "cropUrl": existing_crop_url
            }

        h, w = crop_bgr.shape[:2]

        # Upper Body Region (15% to 48% height, excluding head/neck)
        y1_up, y2_up = int(h * 0.15), int(h * 0.48)
        upper_crop = crop_bgr[y1_up:y2_up, :] if y2_up > y1_up else crop_bgr

        # Lower Body Region (45% to 88% height, excluding shoes/floor contamination)
        y1_low, y2_low = int(h * 0.45), int(h * 0.88)
        lower_crop = crop_bgr[y1_low:y2_low, :] if y2_low > y1_low else crop_bgr

        # Extract primary OpenCV HSV color
        cv_upper_color, cv_upper_conf = cls.extract_opencv_dominant_color(upper_crop)
        cv_lower_color, cv_lower_conf = cls.extract_opencv_dominant_color(lower_crop)

        # Supporting OpenCLIP Zero-Shot Semantic Evidence
        clip_upper_color = "unknown"
        clip_upper_conf = 0.0
        clip_lower_color = "unknown"
        clip_lower_conf = 0.0

        try:
            if crop_emb is None:
                pil_crop = Image.fromarray(cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB))
                crop_emb = openclip_engine.generate_image_embedding(pil_crop)

            color_candidates = ["black", "blue", "red", "white", "green", "yellow", "grey", "brown"]
            upper_prompts = [f"a photo of a person wearing {c} upper clothing" for c in color_candidates]
            prompt_embs = [get_cached_text_embedding(p) for p in upper_prompts]

            sims = [float(np.dot(crop_emb, p_emb)) for p_emb in prompt_embs]
            best_idx = int(np.argmax(sims))
            clip_upper_color = color_candidates[best_idx]
            clip_upper_conf = round(max(0.0, sims[best_idx]), 4)

            lower_prompts = [f"a photo of a person wearing {c} pants or trousers" for c in color_candidates]
            lower_prompt_embs = [get_cached_text_embedding(p) for p in lower_prompts]
            lower_sims = [float(np.dot(crop_emb, p_emb)) for p_emb in lower_prompt_embs]
            best_low_idx = int(np.argmax(lower_sims))
            clip_lower_color = color_candidates[best_low_idx]
            clip_lower_conf = round(max(0.0, lower_sims[best_low_idx]), 4)

        except Exception as e:
            logger.warning(f"[AttributeExtractor] OpenCLIP zero-shot evidence exception: {str(e)}")

        final_upper_color = cv_upper_color if cv_upper_conf >= 0.20 else clip_upper_color
        final_upper_conf = round(0.60 * cv_upper_conf + 0.40 * clip_upper_conf, 4)

        final_lower_color = cv_lower_color if cv_lower_conf >= 0.20 else clip_lower_color
        final_lower_conf = round(0.60 * cv_lower_conf + 0.40 * clip_lower_conf, 4)

        if final_upper_conf < 0.15:
            final_upper_color = "unknown"
        if final_lower_conf < 0.15:
            final_lower_color = "unknown"

        # Accessory Detection (Relative Zero-Shot CLIP Evidence)
        has_backpack, backpack_conf = cls._evaluate_accessory_cached(
            crop_emb,
            "a photo of a person carrying a backpack or shoulder bag",
            "a photo of a person without a backpack"
        )
        has_helmet, helmet_conf = cls._evaluate_accessory_cached(
            crop_emb,
            "a photo of a person wearing a protective helmet",
            "a photo of a person without a helmet"
        )
        has_hat, hat_conf = cls._evaluate_accessory_cached(
            crop_emb,
            "a photo of a person wearing a hat, cap, or headwear",
            "a photo of a person with bare head and no hat or cap"
        )
        has_glasses, glasses_conf = cls._evaluate_accessory_cached(
            crop_emb,
            "a photo of a person wearing glasses or sunglasses",
            "a photo of a person without glasses"
        )

        return {
            "trackId": track_id,
            "objectClass": "person",
            "upperClothingColor": final_upper_color,
            "upperClothingConfidence": final_upper_conf,
            "lowerClothingColor": final_lower_color,
            "lowerClothingConfidence": final_lower_conf,
            "hasBackpack": has_backpack,
            "backpackConfidence": backpack_conf,
            "hasHelmet": has_helmet,
            "helmetConfidence": helmet_conf,
            "hasHat": has_hat,
            "hatConfidence": hat_conf,
            "hasGlasses": has_glasses,
            "glassesConfidence": glasses_conf,
            "supportingFrame": supporting_frame,
            "cropUrl": existing_crop_url
        }

    @classmethod
    def aggregate_track_person_attributes(
        cls,
        crop_items: List[Tuple[np.ndarray, int, str]],
        track_id: int
    ) -> Dict[str, Any]:
        """
        Phase C: Multi-Frame Track-Level Attribute Aggregation.
        Aggregates visual clothing color and accessory evidence across multiple frame crops of a person track.
        Ignores unusable/low-quality crops and returns aggregated track-level attributes with supporting frames.
        """
        if not crop_items:
            return {
                "trackId": track_id,
                "objectClass": "person",
                "upperClothingColor": "unknown",
                "upperClothingConfidence": 0.0,
                "lowerClothingColor": "unknown",
                "lowerClothingConfidence": 0.0,
                "hasBackpack": False,
                "backpackConfidence": 0.0,
                "hasHelmet": False,
                "hasHat": False,
                "hasGlasses": False,
                "supportingFrame": 0,
                "supportingFrames": []
            }

        frame_results = []
        for crop_bgr, frame_num, crop_url in crop_items:
            if crop_bgr is not None and crop_bgr.shape[0] >= 25 and crop_bgr.shape[1] >= 12:
                res = cls.extract_person_attributes(crop_bgr, track_id, frame_num, crop_url)
                frame_results.append(res)

        if not frame_results:
            # Fallback if all crops were small
            res0 = cls.extract_person_attributes(crop_items[0][0], track_id, crop_items[0][1], crop_items[0][2])
            res0["supportingFrames"] = [crop_items[0][1]]
            return res0

        # Aggregate Lower Clothing Color across frames
        lower_counts: Dict[str, List[Tuple[float, int]]] = {}
        upper_counts: Dict[str, List[Tuple[float, int]]] = {}
        backpack_confs: List[Tuple[float, int]] = []
        glasses_confs: List[Tuple[float, int]] = []

        for fr in frame_results:
            fn = fr["supportingFrame"]

            lc = fr.get("lowerClothingColor", "unknown")
            lconf = fr.get("lowerClothingConfidence", 0.0)
            if lc != "unknown":
                lower_counts.setdefault(lc, []).append((lconf, fn))

            uc = fr.get("upperClothingColor", "unknown")
            uconf = fr.get("upperClothingConfidence", 0.0)
            if uc != "unknown":
                upper_counts.setdefault(uc, []).append((uconf, fn))

            if fr.get("hasBackpack"):
                backpack_confs.append((fr.get("backpackConfidence", 0.0), fn))
            if fr.get("hasGlasses"):
                glasses_confs.append((fr.get("glassesConfidence", 0.0), fn))

        # Select dominant lower color
        best_lower_color = "unknown"
        best_lower_conf = 0.0
        lower_supporting_frames = []

        if lower_counts:
            # Rank by (vote_count, sum_confidence)
            sorted_lower = sorted(
                lower_counts.items(),
                key=lambda item: (len(item[1]), sum(c[0] for c in item[1])),
                reverse=True
            )
            best_lower_color = sorted_lower[0][0]
            entries = sorted_lower[0][1]
            best_lower_conf = round(sum(c[0] for c in entries) / float(len(entries)), 4)
            lower_supporting_frames = sorted(list(set(c[1] for c in entries)))

        # Select dominant upper color
        best_upper_color = "unknown"
        best_upper_conf = 0.0
        upper_supporting_frames = []

        if upper_counts:
            sorted_upper = sorted(
                upper_counts.items(),
                key=lambda item: (len(item[1]), sum(c[0] for c in item[1])),
                reverse=True
            )
            best_upper_color = sorted_upper[0][0]
            entries = sorted_upper[0][1]
            best_upper_conf = round(sum(c[0] for c in entries) / float(len(entries)), 4)
            upper_supporting_frames = sorted(list(set(c[1] for c in entries)))

        # Aggregate accessories
        has_backpack = len(backpack_confs) >= max(1, len(frame_results) // 3)
        bp_conf = round(sum(c[0] for c in backpack_confs) / float(max(1, len(backpack_confs))), 4) if backpack_confs else 0.0

        has_glasses = len(glasses_confs) >= max(1, len(frame_results) // 3)
        gl_conf = round(sum(c[0] for c in glasses_confs) / float(max(1, len(glasses_confs))), 4) if glasses_confs else 0.0

        rep_frame = frame_results[0]["supportingFrame"]
        rep_crop_url = frame_results[0]["cropUrl"]

        return {
            "trackId": track_id,
            "objectClass": "person",
            "upperClothingColor": best_upper_color,
            "upperClothingConfidence": best_upper_conf,
            "lowerClothingColor": best_lower_color,
            "lowerClothingConfidence": best_lower_conf,
            "hasBackpack": has_backpack,
            "backpackConfidence": bp_conf,
            "hasHelmet": False,
            "helmetConfidence": 0.0,
            "hasHat": False,
            "hatConfidence": 0.0,
            "hasGlasses": has_glasses,
            "glassesConfidence": gl_conf,
            "supportingFrame": rep_frame,
            "supportingFrames": lower_supporting_frames or upper_supporting_frames or [rep_frame],
            "cropUrl": rep_crop_url
        }

    @classmethod
    def extract_vehicle_attributes(
        cls,
        crop_bgr: np.ndarray,
        object_class: str,
        track_id: int,
        supporting_frame: int,
        existing_crop_url: Optional[str] = None,
        crop_emb: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        Extracts vehicle color for car/bus/truck/motorcycle/bicycle crops.
        Reuses existing crop URL.
        """
        if crop_bgr is None or crop_bgr.size == 0:
            return {
                "trackId": track_id,
                "objectClass": object_class,
                "vehicleColor": "unknown",
                "vehicleColorConfidence": 0.0,
                "supportingFrame": supporting_frame,
                "cropUrl": existing_crop_url
            }

        cv_color, cv_conf = cls.extract_opencv_dominant_color(crop_bgr)
        clip_color = "unknown"
        clip_conf = 0.0

        try:
            if crop_emb is None:
                pil_crop = Image.fromarray(cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB))
                crop_emb = openclip_engine.generate_image_embedding(pil_crop)

            color_candidates = ["black", "blue", "red", "white", "silver", "yellow", "grey", "green"]
            prompts = [f"a photo of a {c} {object_class}" for c in color_candidates]
            prompt_embs = [get_cached_text_embedding(p) for p in prompts]

            sims = [float(np.dot(crop_emb, p_emb)) for p_emb in prompt_embs]
            best_idx = int(np.argmax(sims))
            clip_color = color_candidates[best_idx]
            clip_conf = round(max(0.0, sims[best_idx]), 4)
        except Exception as e:
            logger.warning(f"[AttributeExtractor] Vehicle OpenCLIP exception: {str(e)}")

        final_color = cv_color if cv_conf >= 0.25 else clip_color
        final_conf = round(0.60 * cv_conf + 0.40 * clip_conf, 4)

        if final_conf < 0.20:
            final_color = "unknown"

        return {
            "trackId": track_id,
            "objectClass": object_class,
            "vehicleColor": final_color,
            "vehicleColorConfidence": final_conf,
            "supportingFrame": supporting_frame,
            "cropUrl": existing_crop_url
        }

    @staticmethod
    def _evaluate_accessory_cached(crop_emb: Optional[np.ndarray], pos_prompt: str, neg_prompt: str) -> Tuple[bool, float]:
        """
        Evaluates accessory presence using cached text prompt embeddings.
        """
        if crop_emb is None:
            return False, 0.0
        try:
            pos_emb = get_cached_text_embedding(pos_prompt)
            neg_emb = get_cached_text_embedding(neg_prompt)

            sim_pos = float(np.dot(crop_emb, pos_emb))
            sim_neg = float(np.dot(crop_emb, neg_emb))
            conf = round(max(0.0, sim_pos), 4)

            has_acc = (sim_pos > sim_neg) or (sim_pos >= 0.20)
            return bool(has_acc), conf
        except Exception:
            return False, 0.0

    @staticmethod
    def _evaluate_accessory(crop_bgr: np.ndarray, pos_prompt: str, neg_prompt: str) -> Tuple[bool, float]:
        """
        Evaluates accessory presence using relative OpenCLIP zero-shot prompt evidence (positive vs negative contrast).
        Returns (has_accessory: bool, confidence: float).
        """
        try:
            pil_crop = Image.fromarray(cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB))
            crop_emb = openclip_engine.generate_image_embedding(pil_crop)
            pos_emb = openclip_engine.generate_text_embedding(pos_prompt)
            neg_emb = openclip_engine.generate_text_embedding(neg_prompt)

            sim_pos = float(np.dot(crop_emb, pos_emb))
            sim_neg = float(np.dot(crop_emb, neg_emb))
            conf = round(max(0.0, sim_pos), 4)

            # Relative comparison with small safety margin
            has_acc = (sim_pos > sim_neg) or (sim_pos >= 0.20)
            return bool(has_acc), conf
        except Exception:
            return False, 0.0

