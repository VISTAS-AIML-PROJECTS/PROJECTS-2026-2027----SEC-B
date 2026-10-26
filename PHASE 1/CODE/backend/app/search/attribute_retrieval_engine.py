"""
Dedicated Human Attribute & Clothing Color Retrieval Engine for ChronoLens Phase 3.19.
Integrates HSV/LAB color evidence, PP-Human PAR predictions, OpenCLIP localized crops,
and deterministic track-level aggregation with mathematically normalized [0, 1] scoring.
"""

import cv2
import logging
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from PIL import Image

from app.core.config import settings
from app.services.semantic.openclip_engine import openclip_engine

logger = logging.getLogger("chronolens.search.attribute_engine")

# Color taxonomy definition
COLOR_TAXONOMY = {
    "white": {"h_range": None, "s_max": 65, "v_min": 140},
    "black": {"h_range": None, "s_max": 75, "v_max": 95},
    "grey": {"h_range": None, "s_max": 65, "v_range": (65, 175)},
    "gray": {"h_range": None, "s_max": 65, "v_range": (65, 175)},
    "blue": {"h_range": (90, 135), "s_min": 50, "v_min": 50},
    "red": {"h_range": [(0, 15), (165, 180)], "s_min": 60, "v_min": 50},
    "yellow": {"h_range": (15, 35), "s_min": 60, "v_min": 60},
    "green": {"h_range": (35, 85), "s_min": 50, "v_min": 50},
    "purple": {"h_range": (135, 160), "s_min": 50, "v_min": 50},
    "orange": {"h_range": (10, 25), "s_min": 100, "v_min": 100},
    "pink": {"h_range": (145, 170), "s_min": 30, "v_min": 100},
    "brown": {"h_range": (10, 30), "s_min": 50, "v_range": (30, 120)},
    "beige": {"h_range": (15, 35), "s_max": 80, "v_range": (140, 220)}
}

PAR_LABELS = [
    "Hat", "Glasses", "ShortSleeve", "LongSleeve", "UpperStride", "UpperLogo",
    "UpperPlaid", "UpperSplice", "LowerStripe", "LowerPattern", "LongCoat",
    "Trousers", "Shorts", "Skirt&Dress", "boots", "HandBag", "ShoulderBag",
    "Backpack", "HoldObjectsInFront", "AgeOver60", "Age18-60", "AgeLess18",
    "Female", "Front", "Side", "Back"
]


class PPHumanPARPredictor:
    """Predictor wrapper for PP-Human PPLCNet_x1_0_person_attribute model."""

    def __init__(self):
        self.predictor = None
        self.mean = np.array([0.485, 0.456, 0.406], dtype=np.float32).reshape(1, 3, 1, 1)
        self.std = np.array([0.229, 0.224, 0.225], dtype=np.float32).reshape(1, 3, 1, 1)
        self._init_model()

    def _init_model(self):
        try:
            import paddle.inference as inference
            model_dir = settings.BASE_DIR / "storage" / "models" / "pp_human_attr" / "PPLCNet_x1_0_person_attribute_945_infer"
            if not model_dir.exists():
                model_dir = settings.BASE_DIR / "backend" / "storage" / "models" / "pp_human_attr" / "PPLCNet_x1_0_person_attribute_945_infer"

            if model_dir.exists():
                model_file = str(model_dir / "inference.pdmodel")
                params_file = str(model_dir / "inference.pdiparams")
                config = inference.Config(model_file, params_file)
                config.disable_gpu()
                config.disable_mkldnn()
                config.enable_memory_optim()
                self.predictor = inference.create_predictor(config)
                input_names = self.predictor.get_input_names()
                self.input_handle = self.predictor.get_input_handle(input_names[0])
                output_names = self.predictor.get_output_names()
                self.output_handle = self.predictor.get_output_handle(output_names[0])
                logger.info("[PPHumanPARPredictor] Initialized PP-Human PAR model successfully.")
        except Exception as e:
            logger.warning(f"[PPHumanPARPredictor] Failed to load PP-Human PAR model: {e}")
            self.predictor = None

    def predict_crop_bgr(self, crop_bgr: np.ndarray) -> Dict[str, float]:
        if self.predictor is None or crop_bgr is None or crop_bgr.size == 0:
            return {}

        try:
            img_rgb = Image.fromarray(cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB))
            img_resized = img_rgb.resize((192, 256), Image.BICUBIC)
            img_np = np.array(img_resized, dtype=np.float32) / 255.0
            img_np = img_np.transpose(2, 0, 1)
            img_np = np.expand_dims(img_np, axis=0)
            img_normalized = (img_np - self.mean) / self.std

            inp_tensor = img_normalized.astype(np.float32)
            self.input_handle.reshape(inp_tensor.shape)
            self.input_handle.copy_from_cpu(inp_tensor)
            self.predictor.run()
            out_raw = self.output_handle.copy_to_cpu()

            probs = 1.0 / (1.0 + np.exp(-out_raw[0]))
            return {label: float(probs[idx]) for idx, label in enumerate(PAR_LABELS)}
        except Exception as e:
            logger.warning(f"[PPHumanPARPredictor] Inference error: {e}")
            return {}


par_predictor = PPHumanPARPredictor()


class AttributeRetrievalEngine:
    """Phase 3.19 Dedicated Attribute Engine."""

    def __init__(self):
        openclip_engine.initialize()
        self.text_cache = {}
        self.par_cache = {}
        self.eval_cache = {}

    def get_par_prediction_cached(self, path_str: str, crop_bgr: np.ndarray) -> Dict[str, float]:
        if path_str not in self.par_cache:
            self.par_cache[path_str] = par_predictor.predict_crop_bgr(crop_bgr)
        return self.par_cache[path_str]

    def get_text_feat(self, text_prompt: str) -> np.ndarray:
        if text_prompt not in self.text_cache:
            self.text_cache[text_prompt] = openclip_engine.generate_text_embedding(text_prompt)
        return self.text_cache[text_prompt]

    @staticmethod
    def analyze_upper_body_color(crop_bgr: np.ndarray, target_color: str) -> float:
        h, w, _ = crop_bgr.shape
        if h < 20 or w < 20:
            return 0.0

        upper_body = crop_bgr[int(h * 0.15):int(h * 0.65), int(w * 0.10):int(w * 0.90)]
        if upper_body.size == 0:
            return 0.0

        hsv = cv2.cvtColor(upper_body, cv2.COLOR_BGR2HSV)
        cfg = COLOR_TAXONOMY.get(target_color.lower())
        if not cfg:
            return 0.0

        H = hsv[:, :, 0]
        S = hsv[:, :, 1]
        V = hsv[:, :, 2]

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

        color_ratio = float(np.mean(mask))
        return round(color_ratio, 4)

    @staticmethod
    def extract_head_crop(crop_bgr: np.ndarray) -> np.ndarray:
        h, w, _ = crop_bgr.shape
        head = crop_bgr[0:int(h * 0.35), int(w * 0.15):int(w * 0.85)]
        return head if head.size > 0 else crop_bgr

    @staticmethod
    def extract_upper_body_crop(crop_bgr: np.ndarray) -> np.ndarray:
        h, w, _ = crop_bgr.shape
        upper = crop_bgr[int(h * 0.10):int(h * 0.65), int(w * 0.05):int(w * 0.95)]
        return upper if upper.size > 0 else crop_bgr

    def compute_crop_similarity_batch(self, crops_bgr: List[np.ndarray], text_prompt: str) -> List[float]:
        if not crops_bgr:
            return []
        try:
            img_embs = openclip_engine.generate_image_embeddings_batch(crops_bgr)
            txt_emb = self.get_text_feat(text_prompt)
            sims = np.dot(img_embs, txt_emb)
            norm_sims = np.clip((sims - 0.10) / 0.25, 0.0, 1.0)
            return [round(float(s), 4) for s in norm_sims]
        except Exception:
            return [0.0] * len(crops_bgr)

    def evaluate_person_track(
        self,
        track_id: int,
        crop_paths: List[Path],
        route_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        sampled_paths = crop_paths[:5]
        if not sampled_paths:
            return self._empty_result(track_id)

        imgs_bgr = [cv2.imread(str(p)) for p in sampled_paths]
        imgs_bgr = [im for im in imgs_bgr if im is not None]
        if not imgs_bgr:
            return self._empty_result(track_id)

        route = route_info.get("route")
        raw_query = route_info.get("raw_query", "")

        # Read sub-feature flags
        enable_color_v2 = getattr(settings, "ENABLE_CLOTHING_COLOR_V2", False)
        enable_glasses_par = getattr(settings, "ENABLE_GLASSES_PAR", False)
        enable_hat_par = getattr(settings, "ENABLE_HAT_PAR", False)
        enable_bag_par = getattr(settings, "ENABLE_BAG_PAR", False)

        frame_scores = []

        # ── HUMAN_ATTRIBUTE: hair — PAR checkpoint does NOT support hair length.
        # Return a controlled low-evidence result rather than incorrect garbage.
        if route == "HUMAN_ATTRIBUTE" and route_info.get("is_hair", False):
            logger.debug(f"[AttributeEngine] Hair attribute unsupported by PAR checkpoint for track {track_id} — returning low-evidence.")
            return {
                "track_id": track_id,
                "mean_score": 0.0,
                "median_score": 0.0,
                "max_score": 0.0,
                "pos_frame_ratio": 0.0,
                "valid_frame_count": len(imgs_bgr),
                "raw_track_score": 0.0,
                "final_track_score": 0.0,
                "single_frame_warning": len(imgs_bgr) == 1,
                "frame_scores": [],
                "unsupported_attribute": True,
                "route": route,
            }

        if route == "CLOTHING_COLOR" and enable_color_v2:
            target_color = route_info["color"]
            color_hist_scores = [self.analyze_upper_body_color(im, target_color) for im in imgs_bgr]
            ub_crops = [self.extract_upper_body_crop(im) for im in imgs_bgr]
            semantic_scores = self.compute_crop_similarity_batch(ub_crops, f"person wearing {target_color} shirt")
            frame_scores = [round(0.70 * c + 0.30 * s, 4) for c, s in zip(color_hist_scores, semantic_scores)]

        elif route == "HUMAN_ATTRIBUTE":
            attr_name = route_info.get("attribute", "")
            head_crops = [self.extract_head_crop(im) for im in imgs_bgr]
            openclip_scores = self.compute_crop_similarity_batch(head_crops, f"person with {attr_name}")

            par_scores = []
            if "glasses" in attr_name and enable_glasses_par:
                for p, im in zip(sampled_paths, imgs_bgr):
                    par_dict = self.get_par_prediction_cached(str(p), im)
                    par_scores.append(par_dict.get("Glasses", 0.0))
            elif "hat" in attr_name and enable_hat_par:
                for p, im in zip(sampled_paths, imgs_bgr):
                    par_dict = self.get_par_prediction_cached(str(p), im)
                    par_scores.append(par_dict.get("Hat", 0.0))

            if par_scores:
                frame_scores = [round(0.50 * o + 0.50 * p, 4) for o, p in zip(openclip_scores, par_scores)]
            else:
                frame_scores = openclip_scores

        elif route == "CLOTHING_COLOR":
            # Sub-flag OFF: fall back to generic OpenCLIP full-crop similarity
            color_prompt = f"person wearing {route_info.get('color', 'colored')} shirt"
            frame_scores = self.compute_crop_similarity_batch(imgs_bgr, color_prompt)

        elif route == "BAG_RELATION":
            bag_type = route_info.get("bag_type", "bag")
            bag_color = route_info.get("bag_color", "")
            bag_prompt = f"person carrying a {bag_color + ' ' if bag_color else ''}{bag_type}".strip()
            ub_crops = [self.extract_upper_body_crop(im) for im in imgs_bgr]
            openclip_scores = self.compute_crop_similarity_batch(ub_crops, bag_prompt)

            par_scores = []
            if enable_bag_par:
                for p, im in zip(sampled_paths, imgs_bgr):
                    par_dict = self.get_par_prediction_cached(str(p), im)
                    bp_p = par_dict.get("Backpack", 0.0)
                    hb_p = par_dict.get("HandBag", 0.0)
                    sb_p = par_dict.get("ShoulderBag", 0.0)
                    par_scores.append(max(bp_p, hb_p, sb_p))

            if par_scores:
                frame_scores = [round(0.50 * o + 0.50 * p, 4) for o, p in zip(openclip_scores, par_scores)]
            else:
                frame_scores = openclip_scores
        else:
            frame_scores = self.compute_crop_similarity_batch(imgs_bgr, raw_query)

        if not frame_scores:
            return self._empty_result(track_id)

        mean_sc = round(float(np.mean(frame_scores)), 4)
        med_sc = round(float(np.median(frame_scores)), 4)
        max_sc = round(float(np.max(frame_scores)), 4)

        thresh = 0.25 if route == "CLOTHING_COLOR" else 0.40
        pos_ratio = round(float(np.mean([1.0 if s >= thresh else 0.0 for s in frame_scores])), 4)

        # Unnormalized raw score sum
        raw_track_score = round(0.50 * mean_sc + 0.30 * med_sc + 0.20 * max_sc + 0.10 * pos_ratio, 4)

        # PHASE 3.18 & 3.19 FIX: Mathematically normalized [0.0, 1.0] score by dividing by 1.10
        final_track_score = round(float(raw_track_score / 1.10), 4)

        # Safety assertion — TrackScore MUST always be in [0, 1]
        assert 0.0 <= final_track_score <= 1.0, (
            f"[AttributeEngine] TrackScore out of bounds for track {track_id}: "
            f"{final_track_score} (raw={raw_track_score})"
        )

        valid_count = len(frame_scores)
        single_frame_warn = (valid_count == 1)

        return {
            "track_id": track_id,
            "mean_score": mean_sc,
            "median_score": med_sc,
            "max_score": max_sc,
            "pos_frame_ratio": pos_ratio,
            "valid_frame_count": valid_count,
            "raw_track_score": raw_track_score,
            "final_track_score": final_track_score,
            "single_frame_warning": single_frame_warn,
            "frame_scores": frame_scores
        }

    def evaluate_person_tracks_batch(
        self,
        track_items: List[Dict[str, Any]],
        route_info: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Evaluates a batch of candidate person tracks in a single vectorized OpenCLIP pass.
        track_items is a list of dicts: {"track_id": int, "crop_paths": List[Path]}
        """
        if not track_items:
            return []

        route = route_info.get("route")
        raw_query = route_info.get("raw_query", "")

        # 1. Determine text prompt based on route
        if route == "CLOTHING_COLOR":
            color = route_info.get("color", "colored")
            text_prompt = f"person wearing {color} shirt"
        elif route == "HUMAN_ATTRIBUTE":
            attr = route_info.get("attribute", "")
            text_prompt = f"person with {attr}"
        elif route == "BAG_RELATION":
            bag_type = route_info.get("bag_type", "bag")
            bag_color = route_info.get("bag_color", "")
            text_prompt = f"person carrying a {bag_color + ' ' if bag_color else ''}{bag_type}".strip()
        else:
            text_prompt = raw_query

        # 2. Collect crops across all candidate tracks & record track mapping
        all_crops_bgr = []
        track_crop_slices = []  # list of (track_id, start_idx, end_idx, valid_paths)

        # Multithreaded parallel JPEG reading
        from concurrent.futures import ThreadPoolExecutor

        all_paths_to_load = []
        for item in track_items:
            all_paths_to_load.extend([str(p) for p in item.get("crop_paths", [])[:5]])

        def _read_img(path_str: str):
            try:
                im = cv2.imread(path_str)
                return path_str, im
            except Exception:
                return path_str, None

        img_dict = {}
        if all_paths_to_load:
            with ThreadPoolExecutor(max_workers=8) as executor:
                results = executor.map(_read_img, all_paths_to_load)
                for path_str, im in results:
                    img_dict[path_str] = im

        curr_idx = 0
        for item in track_items:
            tid = item["track_id"]
            crop_paths = item.get("crop_paths", [])[:5]
            if not crop_paths:
                track_crop_slices.append((tid, 0, 0, []))
                continue

            imgs_bgr = [img_dict.get(str(p)) for p in crop_paths]
            valid_pairs = [(p, im) for p, im in zip(crop_paths, imgs_bgr) if im is not None]

            if not valid_pairs:
                track_crop_slices.append((tid, 0, 0, []))
                continue

            # Extract sub-crops if needed for specific routes & collect cache items
            processed_crops = []
            for p, im in valid_pairs:
                if route == "HUMAN_ATTRIBUTE":
                    crop_sub = self.extract_head_crop(im)
                    sub_type = "head"
                elif route in ("CLOTHING_COLOR", "BAG_RELATION"):
                    crop_sub = self.extract_upper_body_crop(im)
                    sub_type = "upper_body"
                else:
                    crop_sub = im
                    sub_type = "full"
                
                processed_crops.append({
                    "crop_path": p,
                    "crop_sub": crop_sub,
                    "sub_type": sub_type
                })

            n_valid = len(processed_crops)
            all_crops_bgr.extend(processed_crops)
            track_crop_slices.append((tid, curr_idx, curr_idx + n_valid, [p for p, _ in valid_pairs]))
            curr_idx += n_valid

        if not all_crops_bgr:
            return [self._empty_result(item["track_id"]) for item in track_items]

        # 3. Cached Vectorized OpenCLIP batch inference for all crops in micro-batches (32 on CUDA, 16 on CPU)
        try:
            img_embs, hits, misses = openclip_engine.generate_crop_embeddings_with_cache(all_crops_bgr, batch_size=32)
            logger.info(f"[AttributeEngine] Crop embedding retrieval complete. Hits: {hits}, Misses: {misses}, Total: {len(all_crops_bgr)}")
            txt_emb = self.get_text_feat(text_prompt)
            raw_sims = np.dot(img_embs, txt_emb)

            # Calibrated normalized similarity scaling for sub-crops
            norm_sims = np.clip((raw_sims - 0.12) / 0.20, 0.0, 1.0)
            all_frame_scores = [round(float(s), 4) for s in norm_sims]
        except Exception as batch_err:
            logger.warning(f"[AttributeEngine] Vectorized batch inference fallback: {batch_err}")
            all_frame_scores = [0.0] * len(all_crops_bgr)

        # 4. Map frame scores back to individual track results
        thresh = 0.20 if route == "CLOTHING_COLOR" else 0.22

        results = []
        for tid, s_idx, e_idx, valid_paths in track_crop_slices:
            if s_idx == e_idx:
                results.append(self._empty_result(tid))
                continue

            f_scores = all_frame_scores[s_idx:e_idx]
            if not f_scores:
                results.append(self._empty_result(tid))
                continue

            mean_sc = round(float(np.mean(f_scores)), 4)
            med_sc = round(float(np.median(f_scores)), 4)
            max_sc = round(float(np.max(f_scores)), 4)
            pos_ratio = round(float(np.mean([1.0 if s >= thresh else 0.0 for s in f_scores])), 4)

            raw_track_score = round(0.50 * mean_sc + 0.30 * med_sc + 0.20 * max_sc + 0.10 * pos_ratio, 4)
            final_track_score = round(float(raw_track_score / 1.10), 4)
            final_track_score = min(1.0, max(0.0, final_track_score))

            valid_count = len(f_scores)
            results.append({
                "track_id": tid,
                "mean_score": mean_sc,
                "median_score": med_sc,
                "max_score": max_sc,
                "pos_frame_ratio": pos_ratio,
                "valid_frame_count": valid_count,
                "raw_track_score": raw_track_score,
                "final_track_score": final_track_score,
                "single_frame_warning": (valid_count == 1),
                "frame_scores": f_scores
            })

        return results

    def _empty_result(self, track_id: int) -> Dict[str, Any]:
        return {
            "track_id": track_id,
            "mean_score": 0.0,
            "median_score": 0.0,
            "max_score": 0.0,
            "pos_frame_ratio": 0.0,
            "valid_frame_count": 0,
            "raw_track_score": 0.0,
            "final_track_score": 0.0,
            "single_frame_warning": False,
            "frame_scores": []
        }


attribute_retrieval_engine = AttributeRetrievalEngine()

