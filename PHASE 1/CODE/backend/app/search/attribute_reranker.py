import os
import math
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import cv2
import numpy as np
from PIL import Image

import torch
import torch.nn.functional as F

from app.core.config import settings

logger = logging.getLogger("chronolens.search.attribute_reranker")


class AttributeReranker:
    """
    Phase 2.4 SigLIP2 Fine-Grained Attribute Verifier/Reranker.
    Computes model-derived siglipScore for attribute candidates (q14-q17)
    using ViT-B-16-SigLIP2-256 without modifying the locked Phase 2.3 ranking formula.
    """

    _instance = None
    _model = None
    _preprocess = None
    _tokenizer = None
    _device = None
    _model_name = "ViT-B-16-SigLIP2-256"
    _pretrained_tag = "webli"
    _score_cache: Dict[Tuple[str, int, int, str], Tuple[float, float]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AttributeReranker, cls).__new__(cls)
            cls._score_cache = {}
        return cls._instance

    @classmethod
    def _initialize_model(cls) -> float:
        """
        Lazy singleton loading of SigLIP2 model on CUDA/CPU.
        Returns model loading latency in milliseconds.
        """
        if cls._model is not None:
            return 0.0

        t0 = time.time()
        cls._device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"[AttributeReranker] Loading SigLIP2 ({cls._model_name}, pretrained={cls._pretrained_tag}) on {cls._device}...")

        try:
            import open_clip
            model, _, preprocess = open_clip.create_model_and_transforms(
                cls._model_name,
                pretrained=cls._pretrained_tag,
                device=cls._device
            )
            tokenizer = open_clip.get_tokenizer(cls._model_name)

            model.eval()
            cls._model = model
            cls._preprocess = preprocess
            cls._tokenizer = tokenizer

            load_ms = round((time.time() - t0) * 1000.0, 2)
            vram_mb = round(torch.cuda.memory_allocated() / (1024 ** 2), 2) if torch.cuda.is_available() else 0.0
            logger.info(f"[AttributeReranker] Loaded SigLIP2 in {load_ms}ms (VRAM: {vram_mb} MB).")
            return load_ms
        except Exception as err:
            logger.warning(f"[AttributeReranker] SigLIP2 model initialization skipped / unavailable: {str(err)}")
            cls._model = None
            return round((time.time() - t0) * 1000.0, 2)

    @classmethod
    def format_query_text(cls, query: str) -> str:
        """
        Formats natural language query into standardized deterministic text input for SigLIP2.
        """
        q_lower = query.strip().lower()
        if "blue shirt" in q_lower or "blue top" in q_lower:
            return "a person wearing a blue shirt"
        elif "grey shirt" in q_lower or "gray shirt" in q_lower:
            return "a person wearing a grey shirt"
        elif "backpack" in q_lower or "bag" in q_lower:
            return "a person carrying a backpack"
        elif "glasses" in q_lower or "sunglasses" in q_lower:
            return "a person wearing glasses"
        else:
            return f"a {q_lower}"

    @classmethod
    def extract_attribute_crop(
        cls,
        video_id: str,
        track_id: int,
        frame_number: int,
        crop_url: str = "",
        query_text: str = ""
    ) -> Optional[Image.Image]:
        """
        Extracts attribute-specific crop from existing track crop file or original frame.
        - Shirt queries (q14, q15): Upper-torso crop (top 55% of bbox).
        - Glasses query (q17): Head/face region crop (top 35% of bbox).
        - Backpack query (q16): Full-body crop.
        """
        q_lower = query_text.lower()

        # 1. Try track crop file on disk
        crop_file = settings.DEBUG_DIR / video_id / "tracks" / str(track_id) / f"frame_{frame_number:04d}.jpg"
        if not crop_file.exists():
            crop_file = settings.STORAGE_DIR / "debug" / video_id / "tracks" / str(track_id) / f"frame_{frame_number:04d}.jpg"

        img_bgr = None
        if crop_file.exists() and crop_file.stat().st_size > 100:
            img_bgr = cv2.imread(str(crop_file))

        # 2. Fallback to original frame image
        if img_bgr is None:
            frame_path = settings.FRAMES_DIR / video_id / f"frame_{frame_number:04d}.jpg"
            if not frame_path.exists():
                frame_path = settings.STORAGE_DIR / "frames" / video_id / f"frame_{frame_number:04d}.jpg"

            if frame_path.exists():
                img_bgr = cv2.imread(str(frame_path))

        if img_bgr is None:
            return None

        h, w = img_bgr.shape[:2]

        # 3. Apply attribute-specific region crop
        if "blue shirt" in q_lower or "grey shirt" in q_lower or "gray shirt" in q_lower:
            # Upper torso region (top 55%)
            crop_h = max(10, int(h * 0.55))
            img_bgr = img_bgr[0:crop_h, 0:w]
        elif "glasses" in q_lower or "sunglasses" in q_lower:
            # Head/upper body region (top 35%)
            crop_h = max(10, int(h * 0.35))
            img_bgr = img_bgr[0:crop_h, 0:w]

        if img_bgr is None or img_bgr.size == 0:
            return None

        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        return Image.fromarray(img_rgb)

    @classmethod
    def compute_siglip_score(cls, pil_img: Image.Image, formatted_query: str) -> Tuple[float, float]:
        """
        Computes SigLIP2 cosine similarity and sigmoid-scaled siglipScore [0.0, 1.0].
        """
        if cls._model is None or cls._preprocess is None or cls._tokenizer is None:
            return 0.0, 0.0

        try:
            with torch.inference_mode():
                img_tensor = cls._preprocess(pil_img).unsqueeze(0).to(cls._device)
                text_tensor = cls._tokenizer([formatted_query]).to(cls._device)

                img_feats = cls._model.encode_image(img_tensor)
                text_feats = cls._model.encode_text(text_tensor)

                img_feats = F.normalize(img_feats, dim=-1)
                text_feats = F.normalize(text_feats, dim=-1)

                cos_sim = float((img_feats @ text_feats.T).item())

                # SigLIP logit scale & bias calculation
                logit_scale = float(getattr(cls._model, 'logit_scale', torch.tensor(1.0)).exp().item()) if hasattr(cls._model, 'logit_scale') else 1.0
                logit_bias = float(getattr(cls._model, 'logit_bias', torch.tensor(0.0)).item()) if hasattr(cls._model, 'logit_bias') else 0.0

                logit = (cos_sim * logit_scale) + logit_bias
                # Clamp logit to prevent overflow in sigmoid
                c_logit = max(-50.0, min(50.0, logit))
                siglip_score = round(1.0 / (1.0 + math.exp(-c_logit)), 4)

                return round(cos_sim, 4), siglip_score
        except Exception as err:
            logger.warning(f"[AttributeReranker] Score computation failed for '{formatted_query}': {str(err)}")
            return 0.0, 0.0

    @classmethod
    def rerank_attribute_candidates(
        cls,
        query_text: str,
        candidate_tracks: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, float]]:
        """
        Runs Stage A diagnostic & Stage B experimental reranking for attribute candidate tracks.
        Attaches siglipScore to each candidate without modifying the production finalScore.
        Returns (updated_candidates, timing_metrics_dict).
        """
        if not candidate_tracks:
            return candidate_tracks, {"load_ms": 0.0, "inference_ms": 0.0, "rerank_ms": 0.0}

        t_total_start = time.time()
        load_ms = cls._initialize_model()

        if cls._model is None:
            return candidate_tracks, {"load_ms": load_ms, "inference_ms": 0.0, "rerank_ms": round((time.time() - t_total_start) * 1000.0, 2)}

        formatted_query = cls.format_query_text(query_text)
        logger.info(f"[AttributeReranker] Reranking {len(candidate_tracks)} candidates for '{query_text}' (template: '{formatted_query}')")

        t_inf_start = time.time()
        updated_tracks = []

        # 1. Identify cached vs uncached candidates
        uncached_indices = []
        uncached_keys = []
        uncached_pil_crops = []

        for idx, item in enumerate(candidate_tracks):
            item_copy = dict(item)
            vid = str(item_copy.get("videoId", ""))
            tid = int(item_copy.get("trackId", 0))
            fn = int(item_copy.get("frameNumber", 1))
            crop_url = str(item_copy.get("cropThumbnail", ""))

            cache_key = (vid, tid, fn, formatted_query)
            if cache_key in cls._score_cache:
                cos_sim, siglip_score = cls._score_cache[cache_key]
                item_copy["siglipScore"] = siglip_score
                item_copy["siglipCosSim"] = cos_sim
            else:
                pil_crop = cls.extract_attribute_crop(vid, tid, fn, crop_url, query_text)
                if pil_crop is not None:
                    uncached_indices.append(idx)
                    uncached_keys.append(cache_key)
                    uncached_pil_crops.append(pil_crop)
                else:
                    item_copy["siglipScore"] = 0.0
                    item_copy["siglipCosSim"] = 0.0

            updated_tracks.append(item_copy)

        # 2. Run Batched Inference for Uncached Crops
        if uncached_pil_crops:
            try:
                with torch.inference_mode():
                    text_tensor = cls._tokenizer([formatted_query]).to(cls._device)
                    text_feats = cls._model.encode_text(text_tensor)
                    text_feats = F.normalize(text_feats, dim=-1)

                    batch_size = 32
                    logit_scale = float(getattr(cls._model, 'logit_scale', torch.tensor(1.0)).exp().item()) if hasattr(cls._model, 'logit_scale') else 1.0
                    logit_bias = float(getattr(cls._model, 'logit_bias', torch.tensor(0.0)).item()) if hasattr(cls._model, 'logit_bias') else 0.0

                    for b_start in range(0, len(uncached_pil_crops), batch_size):
                        chunk_crops = uncached_pil_crops[b_start : b_start + batch_size]
                        img_tensors = torch.stack([cls._preprocess(c) for c in chunk_crops]).to(cls._device)

                        img_feats = cls._model.encode_image(img_tensors)
                        img_feats = F.normalize(img_feats, dim=-1)

                        cos_sims = (img_feats @ text_feats.T).squeeze(-1).cpu().numpy()

                        for idx_in_chunk, cs in enumerate(cos_sims):
                            cs_val = float(cs)
                            logit = (cs_val * logit_scale) + logit_bias
                            c_logit = max(-50.0, min(50.0, logit))
                            siglip_score = round(1.0 / (1.0 + math.exp(-c_logit)), 4)
                            res_tuple = (round(cs_val, 4), siglip_score)

                            orig_idx = uncached_indices[b_start + idx_in_chunk]
                            c_key = uncached_keys[b_start + idx_in_chunk]

                            cls._score_cache[c_key] = res_tuple
                            updated_tracks[orig_idx]["siglipScore"] = siglip_score
                            updated_tracks[orig_idx]["siglipCosSim"] = res_tuple[0]

            except Exception as batch_err:
                logger.warning(f"[AttributeReranker] Batched inference error: {batch_err}")
                for idx, c_key in zip(uncached_indices, uncached_keys):
                    if "siglipScore" not in updated_tracks[idx]:
                        updated_tracks[idx]["siglipScore"] = 0.0
                        updated_tracks[idx]["siglipCosSim"] = 0.0

        inf_ms = round((time.time() - t_inf_start) * 1000.0, 2)
        rerank_ms = round((time.time() - t_total_start) * 1000.0, 2)

        metrics = {
            "load_ms": load_ms,
            "inference_ms": inf_ms,
            "rerank_ms": rerank_ms
        }

        logger.info(f"[AttributeReranker] Reranked {len(updated_tracks)} candidates in {rerank_ms}ms (inf={inf_ms}ms, load={load_ms}ms)")
        return updated_tracks, metrics


attribute_reranker = AttributeReranker()
