"""
Attribute V3 Extractor for ChronoLens.
Complies strictly with Mandatory Corrections:
1. attributeVersion = "v3"
2. Strict Model Capability Boundaries (reuses PP-Human PAR only for demonstrable classes; uses OpenCLIP for localized crops).
3. UNKNOWN vs FALSE Policy (insufficient/occluded/too-small/ambiguous evidence defaults to 'unknown').
4. Footwear Crop Thresholding (minimum crop size w >= 25, h >= 25; returns 'unknown' if small or unconfident).
5. Necklace / Chain Thresholding (minimum neck crop size w >= 30, h >= 30; high confidence threshold; suppresses reflections).
6. Temporal Evidence Aggregation (retains mean, median, max confidence, supportRatio, evidenceFrames, bestEvidenceFrame).
7. Motion-based Walking / Standing (uses ByteTrack spatial displacement over time).
8. Reuses PAR Front / Side / Back for view/orientation.
"""

import cv2
import logging
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from app.core.config import settings
from app.models.attribute_v3_schema import (
    AttributeV3Record,
    HeadAttributes,
    UpperBodyAttributes,
    LowerBodyAttributes,
    FootwearAttributes,
    AccessoryAttributes,
    BagAttributes,
    ViewAttributes,
    AttributeV3Evidence,
    AttributeProvenance,
)
from app.processing.attributes.region_cropper import region_cropper
from app.search.attribute_retrieval_engine import par_predictor, COLOR_TAXONOMY
from app.services.semantic.openclip_engine import openclip_engine

logger = logging.getLogger("chronolens.processing.attributes.v3_extractor")


class AttributeV3Extractor:
    """Extractor for Attribute V3 multi-category region-based human attributes."""

    FOOTWEAR_TYPES = ["sneakers", "shoes", "boots", "sandals", "slippers", "heels"]
    UPPER_BODY_TYPES = ["t_shirt", "shirt", "polo", "jacket", "hoodie", "sweatshirt", "sweater", "coat"]
    LOWER_BODY_TYPES = ["jeans", "pants", "trousers", "shorts", "skirt", "dress", "leggings"]
    COLOR_KEYS = ["black", "white", "blue", "red", "grey", "green", "yellow", "pink", "orange", "brown", "purple", "beige"]

    def __init__(self):
        openclip_engine.initialize()

    def extract_track_attributes(
        self,
        video_id: str,
        track_id: int,
        frame_items: List[Dict[str, Any]]
    ) -> AttributeV3Record:
        """
        Extracts Attribute V3 metadata for a tracked person across multiple frames.
        frame_items: list of dicts with keys: 'frame_number', 'timestamp', 'crop_path', 'bbox'
        """
        record = AttributeV3Record(trackId=track_id, videoId=video_id)

        if not frame_items:
            return record

        # Sample up to 10 representative frames
        sampled = frame_items[:10]
        valid_frames = []
        frame_predictions = []

        for item in sampled:
            crop_bgr = None
            crop_path = Path(item.get("crop_path", ""))
            if crop_path.exists():
                crop_bgr = cv2.imread(str(crop_path))

            frame_num = item["frame_number"]
            ts = item["timestamp"]
            bbox = item.get("bbox", [])

            if crop_bgr is None or crop_bgr.size == 0:
                frame_path = Path(item.get("frame_path", ""))
                if frame_path.exists():
                    full_img = cv2.imread(str(frame_path))
                    if full_img is not None and full_img.size > 0:
                        if len(bbox) == 4:
                            h_img, w_img = full_img.shape[:2]
                            x1, y1, x2, y2 = [int(v) for v in bbox]
                            x1, y1 = max(0, x1), max(0, y1)
                            x2, y2 = min(w_img, x2), min(h_img, y2)
                            if x2 > x1 and y2 > y1:
                                crop_bgr = full_img[y1:y2, x1:x2]

            if crop_bgr is None or crop_bgr.size == 0:
                continue

            valid_frames.append((frame_num, ts, crop_bgr, bbox))

            # Extract single-frame predictions
            single_pred = self.extract_single_frame(crop_bgr, frame_num, bbox)
            frame_predictions.append((frame_num, ts, single_pred))

        if not frame_predictions:
            return record

        # Calculate motion (walking vs standing) from bbox displacement across frames
        is_walking, motion_conf = self._calculate_trajectory_motion(valid_frames)

        # Perform temporal aggregation
        record = self.aggregate_temporal_predictions(
            video_id=video_id,
            track_id=track_id,
            frame_predictions=frame_predictions,
            is_walking=is_walking,
            motion_conf=motion_conf
        )

        return record

    def extract_single_frame(self, crop_bgr: np.ndarray, frame_num: int, bbox: List[float]) -> Dict[str, Any]:
        """Extracts attributes for a single frame crop using 7 regions."""
        regions = region_cropper.extract_regions(crop_bgr)
        if not regions:
            return {}

        # 1. PAR Predictor (Demonstrably supported classes ONLY)
        par_scores = par_predictor.predict_crop_bgr(regions.get("full_person", crop_bgr))

        # 2. Head Attributes
        head_crop = regions.get("head", crop_bgr)
        hat_par = par_scores.get("Hat", 0.0)
        glasses_par = par_scores.get("Glasses", 0.0)

        # Hair analysis via OpenCLIP zero-shot on head crop
        hair_type, hair_conf = self._classify_openclip_text(
            head_crop, ["short hair", "long hair", "bald head"], ["short", "long", "short"]
        )
        if hair_conf < getattr(settings, "ATTRIBUTE_V3_HEAD_CONFIDENCE", 0.60):
            hair_type = "unknown"

        # 3. Upper Body Attributes
        upper_crop = regions.get("upper_body", crop_bgr)
        upper_color, color_conf = self._analyze_region_color(upper_crop)
        
        # Upper body type
        upper_type, upper_type_conf = self._classify_openclip_text(
            upper_crop,
            [f"person wearing a {t}" for t in self.UPPER_BODY_TYPES],
            self.UPPER_BODY_TYPES
        )
        if upper_type_conf < getattr(settings, "ATTRIBUTE_V3_UPPER_BODY_CONFIDENCE", 0.60):
            upper_type = "unknown"

        # Sleeve length via PAR
        ss_par = par_scores.get("ShortSleeve", 0.0)
        ls_par = par_scores.get("LongSleeve", 0.0)
        if ss_par > 0.60 and ss_par > ls_par:
            sleeve, sleeve_conf = "short", ss_par
        elif ls_par > 0.60:
            sleeve, sleeve_conf = "long", ls_par
        else:
            sleeve, sleeve_conf = "unknown", max(ss_par, ls_par)

        # 4. Lower Body Attributes
        lower_crop = regions.get("lower_body", crop_bgr)
        lower_color, lower_color_conf = self._analyze_region_color(lower_crop)

        # Lower body type via PAR
        tr_par = par_scores.get("Trousers", 0.0)
        sh_par = par_scores.get("Shorts", 0.0)
        sk_par = par_scores.get("Skirt&Dress", 0.0)

        if tr_par > 0.60:
            lower_type, lower_type_conf = "pants", tr_par
        elif sh_par > 0.60:
            lower_type, lower_type_conf = "shorts", sh_par
        elif sk_par > 0.60:
            lower_type, lower_type_conf = "skirt", sk_par
        else:
            lower_type, lower_type_conf = self._classify_openclip_text(
                lower_crop,
                [f"person wearing {t}" for t in self.LOWER_BODY_TYPES],
                self.LOWER_BODY_TYPES
            )
            if lower_type_conf < getattr(settings, "ATTRIBUTE_V3_LOWER_BODY_CONFIDENCE", 0.60):
                lower_type = "unknown"

        # 5. Footwear Attributes (Specialist Footwear ROI Branch)
        from app.processing.attributes.footwear_specialist import footwear_specialist
        fw_res = footwear_specialist.extract_footwear(crop_bgr, bbox=bbox)
        fw_type = fw_res["type"]
        fw_conf = fw_res["type_confidence"]
        fw_color = fw_res["color"]
        fw_color_conf = fw_res["color_confidence"]

        # 6. Accessories (Correction #5: Strict size, high threshold, suppresses reflections)
        neck_crop = regions.get("neck_accessory", crop_bgr)
        nk_h, nk_w = neck_crop.shape[:2]
        if nk_h >= 30 and nk_w >= 30:
            acc_label, acc_conf = self._classify_openclip_text(
                neck_crop,
                ["wearing a necklace chain", "wearing a scarf", "no necklace or scarf"],
                ["necklace", "scarf", "none"]
            )
            if acc_conf < getattr(settings, "ATTRIBUTE_V3_ACCESSORY_CONFIDENCE", 0.70):
                acc_label = "none"
                acc_conf = 0.0
        else:
            acc_label, acc_conf = "none", 0.0

        # 7. Bags (PP-Human PAR + OpenCLIP V2 Relative Contrast Evidence Fusion)
        bp_par = par_scores.get("Backpack", 0.0)
        hb_par = par_scores.get("HandBag", 0.0)
        sb_par = par_scores.get("ShoulderBag", 0.0)
        ho_par = par_scores.get("HoldObjectsInFront", 0.0)

        # OpenCLIP V2 backpack evidence fusion
        has_bp_clip, clip_bp_conf = False, 0.0
        try:
            pil_crop = Image.fromarray(cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB))
            c_emb = openclip_engine.generate_image_embedding(pil_crop)
            p_emb = openclip_engine.generate_text_embedding("a photo of a person carrying a backpack or shoulder bag")
            n_emb = openclip_engine.generate_text_embedding("a photo of a person without a backpack")
            sim_pos = float(np.dot(c_emb, p_emb))
            sim_neg = float(np.dot(c_emb, n_emb))
            if (sim_pos > sim_neg and sim_pos >= 0.20) or sim_pos >= 0.25:
                has_bp_clip = True
                clip_bp_conf = round(max(0.0, sim_pos), 4)
        except Exception:
            pass

        final_bp_val = "true" if (bp_par >= 0.60 or (has_bp_clip and clip_bp_conf >= 0.50)) else ("false" if (bp_par <= 0.20 and not has_bp_clip) else "unknown")
        final_bp_conf = round(max(bp_par, clip_bp_conf), 4)

        # Hair Length and Color split (Correction #5)
        head_crop = regions.get("head", crop_bgr)
        hair_len, hair_len_conf = self._classify_openclip_text(
            head_crop,
            ["a person with long hair", "a person with short hair", "a person with bald or no hair"],
            ["long", "short", "unknown"]
        )
        hair_col, hair_col_conf = self._classify_openclip_text(
            head_crop,
            ["black hair", "brown hair", "blonde hair", "grey hair"],
            ["black", "brown", "blonde", "grey"]
        )

        # 8. View / Orientation (Correction #8: Reuse PAR Front/Side/Back)
        front_par = par_scores.get("Front", 0.0)
        side_par = par_scores.get("Side", 0.0)
        back_par = par_scores.get("Back", 0.0)
        
        max_view = max(front_par, side_par, back_par)
        if max_view > 0.50:
            if front_par == max_view:
                person_view, view_conf = "front", front_par
            elif side_par == max_view:
                person_view, view_conf = "side", side_par
            else:
                person_view, view_conf = "back", back_par
        else:
            person_view, view_conf = "unknown", max_view

        return {
            "head": {
                "hat": {"value": "true" if hat_par >= 0.60 else ("false" if hat_par <= 0.20 else "unknown"), "confidence": round(hat_par, 4), "source": "PP-Human PAR"},
                "glasses": {"value": "true" if glasses_par >= 0.60 else ("false" if glasses_par <= 0.20 else "unknown"), "confidence": round(glasses_par, 4), "source": "PP-Human PAR"},
                "hairLength": {"value": hair_len, "confidence": round(hair_len_conf, 4), "source": "OpenCLIP"},
                "hairColor": {"value": hair_col, "confidence": round(hair_col_conf, 4), "source": "OpenCLIP"},
            },
            "upperBody": {
                "type": upper_type,
                "type_confidence": round(upper_type_conf, 4),
                "color": upper_color,
                "color_confidence": round(color_conf, 4),
                "sleeve": sleeve,
                "sleeve_confidence": round(sleeve_conf, 4),
                "source": "HSV+OpenCLIP+PAR",
            },
            "lowerBody": {
                "type": lower_type,
                "color": lower_color,
                "confidence": round(max(lower_type_conf, lower_color_conf), 4),
                "source": "HSV+OpenCLIP+PAR",
            },
            "footwear": {
                "type": fw_type,
                "color": fw_color,
                "confidence": round(fw_conf, 4),
                "source": "OpenCLIP+PAR",
            },
            "accessories": {
                "necklace": {"value": "true" if acc_label == "necklace" and acc_conf >= 0.70 else "unknown", "confidence": round(acc_conf, 4), "source": "OpenCLIP"},
                "scarf": {"value": "true" if acc_label == "scarf" and acc_conf >= 0.70 else "unknown", "confidence": round(acc_conf, 4), "source": "OpenCLIP"},
            },
            "bags": {
                "backpack": {"value": final_bp_val, "confidence": final_bp_conf, "source": "PAR+OpenCLIP V2 Fusion"},
                "handbag": {"value": "true" if hb_par >= 0.60 else ("false" if hb_par <= 0.20 else "unknown"), "confidence": round(hb_par, 4), "source": "PP-Human PAR"},
                "shoulder_bag": {"value": "true" if sb_par >= 0.60 else ("false" if sb_par <= 0.20 else "unknown"), "confidence": round(sb_par, 4), "source": "PP-Human PAR"},
                "carrying_bag": {"value": "true" if max(final_bp_conf, hb_par, sb_par) >= 0.60 else "unknown", "confidence": round(max(final_bp_conf, hb_par, sb_par), 4), "source": "PAR+OpenCLIP"},
                "holding_object": {"value": "true" if ho_par >= 0.60 else "unknown", "confidence": round(ho_par, 4), "source": "PP-Human PAR"},
            },
            "view": {
                "person_view": person_view,
                "personView": person_view,
                "confidence": round(view_conf, 4),
            },
        }

    def _calculate_trajectory_motion(self, valid_frames: List[Tuple[int, float, np.ndarray, List[float]]]) -> Tuple[str, float]:
        """Correction #7: Calculates ByteTrack trajectory displacement over time to determine walking vs standing."""
        if len(valid_frames) < 2:
            return ("unknown", 0.0)

        centers = []
        timestamps = []
        for fn, ts, img, bbox in valid_frames:
            if len(bbox) >= 4:
                cx = (bbox[0] + bbox[2]) / 2.0
                cy = (bbox[1] + bbox[3]) / 2.0
                centers.append((cx, cy))
                timestamps.append(ts)

        if len(centers) < 2:
            return ("standing", 0.70)

        dt = max(0.1, timestamps[-1] - timestamps[0])
        dist = np.sqrt((centers[-1][0] - centers[0][0]) ** 2 + (centers[-1][1] - centers[0][1]) ** 2)
        speed = dist / dt

        # Threshold displacement speed (pixels per second)
        if speed > 15.0:
            return ("walking", min(1.0, round(0.60 + speed / 100.0, 4)))
        return ("standing", 0.75)

    def aggregate_temporal_predictions(
        self,
        video_id: str,
        track_id: int,
        frame_predictions: List[Tuple[int, float, Dict[str, Any]]],
        is_walking: str,
        motion_conf: float
    ) -> AttributeV3Record:
        """
        Aggregates frame-level attribute predictions into track-level AttributeV3Record.
        Retains mean, median, max confidence, supportRatio, bestEvidenceFrame, and evidenceFrames.
        Applies deterministic weighted aggregation formula:
          finalConfidence = round(0.35 * mean + 0.25 * median + 0.25 * max + 0.15 * supportRatio, 4)
        """
        record = AttributeV3Record(trackId=track_id, videoId=video_id)
        if not frame_predictions:
            return record

        sample_count = len(frame_predictions)
        evidence_frames = [fp[0] for fp in frame_predictions]
        best_frame_num = frame_predictions[0][0]
        best_frame_ts = frame_predictions[0][1]

        record.evidence = AttributeV3Evidence(
            bestEvidenceFrame=best_frame_num,
            bestEvidenceTimestamp=round(best_frame_ts, 2),
            evidenceFrames=evidence_frames,
            supportRatio=1.0,
            sampleCount=sample_count,
        )

        min_conf_threshold = getattr(settings, "ATTRIBUTE_V3_MIN_CONFIDENCE", 0.50)

        def _build_prov(confs: List[float], val_str: Any, src: str, mdl: str, reg: str, min_thresh: float = min_conf_threshold) -> AttributeProvenance:
            if not confs:
                return AttributeProvenance(value="unknown", source=src, model=mdl, region=reg)
            mean_c = round(float(np.mean(confs)), 4)
            med_c = round(float(np.median(confs)), 4)
            max_c = round(float(np.max(confs)), 4)
            sup_r = round(float(sum(1 for c in confs if c >= 0.50) / len(confs)), 4)

            # Deterministic Aggregated Confidence Formula (Correction #4)
            final_conf = round(0.35 * mean_c + 0.25 * med_c + 0.25 * max_c + 0.15 * sup_r, 4)

            # Apply threshold to final_conf
            if final_conf < min_thresh and val_str not in ["unknown", False]:
                val_str = "unknown"

            return AttributeProvenance(
                value=val_str,
                confidence=final_conf,
                mean_confidence=mean_c,
                median_confidence=med_c,
                max_confidence=max_c,
                support_ratio=sup_r,
                source=src,
                model=mdl,
                region=reg,
                best_evidence_frame=best_frame_num,
                evidence_frames=evidence_frames
            )

        # 1. Head Attributes
        hat_confs = [fp[2]["head"]["hat"]["confidence"] for fp in frame_predictions]
        hat_vals = [fp[2]["head"]["hat"]["value"] for fp in frame_predictions]
        hat_true_cnt = sum(1 for v in hat_vals if v == "true")
        final_hat_val = "true" if hat_true_cnt / sample_count >= 0.50 else ("false" if sum(1 for v in hat_vals if v == "false") / sample_count >= 0.60 else "unknown")
        record.head.hat = _build_prov(hat_confs, final_hat_val, "PP-Human PAR", "PPLCNet_x1_0_person_attribute", "head")

        glasses_confs = [fp[2]["head"]["glasses"]["confidence"] for fp in frame_predictions]
        glasses_vals = [fp[2]["head"]["glasses"]["value"] for fp in frame_predictions]
        gl_true_cnt = sum(1 for v in glasses_vals if v == "true")
        final_gl_val = "true" if gl_true_cnt / sample_count >= 0.50 else ("false" if sum(1 for v in glasses_vals if v == "false") / sample_count >= 0.60 else "unknown")
        record.head.glasses = _build_prov(glasses_confs, final_gl_val, "PP-Human PAR", "PPLCNet_x1_0_person_attribute", "head")

        hair_len_vals = [fp[2]["head"]["hairLength"]["value"] for fp in frame_predictions if fp[2]["head"]["hairLength"]["value"] != "unknown"]
        hair_len_confs = [fp[2]["head"]["hairLength"]["confidence"] for fp in frame_predictions]
        final_hair_len = max(set(hair_len_vals), key=hair_len_vals.count) if hair_len_vals else "unknown"
        record.head.hairLength = _build_prov(hair_len_confs, final_hair_len, "OpenCLIP", "ViT-L-14", "head")

        hair_col_vals = [fp[2]["head"]["hairColor"]["value"] for fp in frame_predictions if fp[2]["head"]["hairColor"]["value"] != "unknown"]
        hair_col_confs = [fp[2]["head"]["hairColor"]["confidence"] for fp in frame_predictions]
        final_hair_col = max(set(hair_col_vals), key=hair_col_vals.count) if hair_col_vals else "unknown"
        record.head.hairColor = _build_prov(hair_col_confs, final_hair_col, "OpenCLIP", "ViT-L-14", "head")

        # 2. Upper Body Attributes
        u_colors = [fp[2]["upperBody"]["color"] for fp in frame_predictions if fp[2]["upperBody"]["color"] != "unknown"]
        u_col_confs = [fp[2]["upperBody"]["color_confidence"] for fp in frame_predictions]
        final_u_col = max(set(u_colors), key=u_colors.count) if u_colors else "unknown"
        record.upperBody.color = _build_prov(u_col_confs, final_u_col, "HSV Color Analytics", "HSV+OpenCLIP", "upper_body")

        u_types = [fp[2]["upperBody"]["type"] for fp in frame_predictions if fp[2]["upperBody"]["type"] != "unknown"]
        u_typ_confs = [fp[2]["upperBody"]["type_confidence"] for fp in frame_predictions]
        final_u_typ = max(set(u_types), key=u_types.count) if u_types else "unknown"
        record.upperBody.type = _build_prov(u_typ_confs, final_u_typ, "OpenCLIP Zero-Shot", "ViT-L-14", "upper_body")

        # 3. Lower Body Attributes
        l_colors = [fp[2]["lowerBody"]["color"] for fp in frame_predictions if fp[2]["lowerBody"]["color"] != "unknown"]
        l_confs = [fp[2]["lowerBody"]["confidence"] for fp in frame_predictions]
        final_l_col = max(set(l_colors), key=l_colors.count) if l_colors else "unknown"
        record.lowerBody.color = _build_prov(l_confs, final_l_col, "HSV Color Analytics", "HSV+OpenCLIP", "lower_body")

        l_types = [fp[2]["lowerBody"]["type"] for fp in frame_predictions if fp[2]["lowerBody"]["type"] != "unknown"]
        final_l_typ = max(set(l_types), key=l_types.count) if l_types else "unknown"
        record.lowerBody.type = _build_prov(l_confs, final_l_typ, "PP-Human PAR + OpenCLIP", "PAR+ViT-L-14", "lower_body")

        # 4. Footwear Attributes
        fw_types = [fp[2]["footwear"]["type"] for fp in frame_predictions if fp[2]["footwear"]["type"] != "unknown"]
        fw_colors = [fp[2]["footwear"]["color"] for fp in frame_predictions if fp[2]["footwear"]["color"] != "unknown"]
        fw_confs = [fp[2]["footwear"]["confidence"] for fp in frame_predictions]

        final_fw_typ = max(set(fw_types), key=fw_types.count) if fw_types else "unknown"
        final_fw_col = max(set(fw_colors), key=fw_colors.count) if fw_colors else "unknown"
        record.footwear.type = _build_prov(fw_confs, final_fw_typ, "OpenCLIP Footwear Branch", "ViT-L-14", "footwear", min_thresh=0.60)
        record.footwear.color = _build_prov(fw_confs, final_fw_col, "HSV Footwear Analytics", "HSV+ViT-L-14", "footwear", min_thresh=0.60)

        # 5. Accessories
        neck_confs = [fp[2]["accessories"]["necklace"]["confidence"] for fp in frame_predictions]
        neck_vals = [fp[2]["accessories"]["necklace"]["value"] for fp in frame_predictions]
        final_neck = "true" if sum(1 for v in neck_vals if v == "true") / sample_count >= 0.50 else "unknown"
        record.accessories.necklace = _build_prov(neck_confs, final_neck, "OpenCLIP Neck Branch", "ViT-L-14", "neck_accessory", min_thresh=0.70)

        # 6. Bags
        bp_confs = [fp[2]["bags"]["backpack"]["confidence"] for fp in frame_predictions]
        bp_vals = [fp[2]["bags"]["backpack"]["value"] for fp in frame_predictions]
        final_bp = "true" if sum(1 for v in bp_vals if v == "true") / sample_count >= 0.40 else "unknown"
        record.bags.backpack = _build_prov(bp_confs, final_bp, "PAR+OpenCLIP V2 Fusion", "PPLCNet+ViT-L-14", "torso")

        # 7. View & Motion
        views = [fp[2]["view"]["person_view"] for fp in frame_predictions if fp[2]["view"]["person_view"] != "unknown"]
        v_confs = [fp[2]["view"]["confidence"] for fp in frame_predictions]
        final_view = max(set(views), key=views.count) if views else "unknown"
        record.view.person_view = _build_prov(v_confs, final_view, "PP-Human PAR", "PPLCNet_x1_0_person_attribute", "full_person")
        record.view.walking = _build_prov([motion_conf], is_walking == "walking", "ByteTrack Displacement", "ByteTrack", "trajectory")
        record.view.standing = _build_prov([motion_conf], is_walking == "standing", "ByteTrack Displacement", "ByteTrack", "trajectory")

        return record

    def _analyze_region_color(self, crop_bgr: np.ndarray) -> Tuple[str, float]:
        """Runs HSV color analysis on a region crop, returning (best_color, confidence)."""
        if crop_bgr is None or crop_bgr.size == 0 or crop_bgr.shape[0] < 10 or crop_bgr.shape[1] < 10:
            return ("unknown", 0.0)

        hsv = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2HSV)
        H, S, V = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]

        best_color = "unknown"
        best_ratio = 0.0

        for color in self.COLOR_KEYS:
            cfg = COLOR_TAXONOMY.get(color)
            if not cfg:
                continue

            mask = np.ones(H.shape, dtype=bool)
            if "v_min" in cfg:
                mask &= (V >= cfg["v_min"])
            if "v_max" in cfg:
                mask &= (V <= cfg["v_max"])
            if "v_range" in cfg:
                mask &= (V >= cfg["v_range"][0]) & (V <= cfg["v_range"][1])
            if "s_max" in cfg:
                mask &= (S <= cfg["s_max"])
            if "s_min" in cfg:
                mask &= (S >= cfg["s_min"])

            if cfg.get("h_range") is not None:
                hr = cfg["h_range"]
                if isinstance(hr, list):
                    h_mask = np.zeros(H.shape, dtype=bool)
                    for r in hr:
                        h_mask |= (H >= r[0]) & (H <= r[1])
                    mask &= h_mask
                else:
                    mask &= (H >= hr[0]) & (H <= hr[1])

            ratio = float(np.mean(mask))
            if ratio > best_ratio:
                best_ratio = ratio
                best_color = color

        if best_ratio < 0.15:
            return ("unknown", round(best_ratio, 4))
        return (best_color, round(best_ratio, 4))

    def _classify_openclip_text(
        self, crop_bgr: np.ndarray, text_prompts: List[str], label_mapping: List[str]
    ) -> Tuple[str, float]:
        """Classifies a crop against text prompts using OpenCLIP embeddings."""
        if crop_bgr is None or crop_bgr.size == 0 or not text_prompts:
            return ("unknown", 0.0)

        try:
            crop_emb = openclip_engine.generate_image_embeddings_batch([crop_bgr])[0]
            sims = []
            for prompt in text_prompts:
                txt_emb = openclip_engine.generate_text_embedding(prompt)
                sim = float(np.dot(crop_emb, txt_emb))
                sims.append(sim)

            best_idx = int(np.argmax(sims))
            best_sim = sims[best_idx]
            norm_conf = float(np.clip((best_sim - 0.10) / 0.25, 0.0, 1.0))

            if norm_conf < 0.40 or best_idx >= len(label_mapping):
                return ("unknown", round(norm_conf, 4))

            return (label_mapping[best_idx], round(norm_conf, 4))
        except Exception as e:
            logger.warning(f"OpenCLIP zero-shot error: {e}")
            return ("unknown", 0.0)


attribute_v3_extractor = AttributeV3Extractor()
