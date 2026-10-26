import os
import logging
import threading
from pathlib import Path
from typing import Union, List, Dict, Tuple, Optional, Any
import torch
import numpy as np
from PIL import Image
import open_clip
from app.core.config import settings, get_runtime_device

logger = logging.getLogger("chronolens.semantic.openclip")


class OpenCLIPEngine:
    """
    Singleton Semantic Embedding Engine powering ChronoLens with OpenCLIP ViT-L/14.
    Loads model weights once into memory during backend startup and reuses across processing runs.
    Binds automatically to CUDA GPU acceleration when available, else CPU.
    Includes thread-safe bounded LRU query text embedding cache (maxsize=256).
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(OpenCLIPEngine, cls).__new__(cls)
                    cls._instance._is_initialized = False
                    cls._instance._text_cache: Dict[str, np.ndarray] = {}
                    cls._instance._cache_order: List[str] = []
                    cls._instance._cache_lock = threading.Lock()
        return cls._instance

    def initialize(self):
        """Loads OpenCLIP ViT-L/14 model and logs runtime parameters."""
        if getattr(self, "_is_initialized", False):
            return

        with self._lock:
            if getattr(self, "_is_initialized", False):
                return

            self.model_name = settings.OPENCLIP_MODEL
            self.pretrained = settings.OPENCLIP_PRETRAINED
            self.device = get_runtime_device()

            logger.info(f"[OpenCLIPEngine] Loading OpenCLIP {self.model_name} (pretrained={self.pretrained}) on {self.device.upper()}...")

            try:
                model, _, preprocess = open_clip.create_model_and_transforms(
                    self.model_name,
                    pretrained=self.pretrained,
                    device=self.device
                )
                model.eval()

                self.model = model
                self.preprocess = preprocess

                # Determine runtime embedding dimension & model fingerprint
                with torch.inference_mode():
                    dummy_input = torch.randn(1, 3, 224, 224).to(self.device)
                    dummy_emb = self.model.encode_image(dummy_input)
                    self.embedding_dim = int(dummy_emb.shape[-1])
                    self.model_fingerprint = f"{self.model_name}:{self.pretrained}:{self.embedding_dim}"

                self._is_initialized = True

                print("\n==========================================")
                print("ChronoLens Semantic Engine\n")
                print("Embedding Model:")
                print(f"OpenCLIP {self.model_name}\n")
                print("Embedding Dimension:")
                print(f"{self.embedding_dim}\n")
                print("Device:")
                print(f"{self.device.upper()}")
                print("==========================================\n")

                logger.info(f"[OpenCLIPEngine] Initialized successfully. Dimension: {self.embedding_dim}, Device: {self.device.upper()}")

            except Exception as e:
                logger.error(f"[OpenCLIPEngine] Failed to initialize OpenCLIP model: {str(e)}")
                raise RuntimeError(f"OpenCLIP initialization error: {str(e)}")

    def prewarm(self):
        """Executes warm-up inference passes for both text and image encoders."""
        if not getattr(self, "_is_initialized", False):
            self.initialize()

        try:
            logger.info(f"[OpenCLIPEngine] Executing prewarming on {self.device.upper()}...")
            with torch.inference_mode():
                # Text warm-up
                self.generate_text_embedding("warmup query")
                # Image warm-up
                dummy_img = Image.new("RGB", (224, 224), color=(128, 128, 128))
                self.generate_image_embedding(dummy_img)
                self.generate_image_embeddings_batch([dummy_img, dummy_img], batch_size=2)
            logger.info(f"[OpenCLIPEngine] Prewarming completed successfully on {self.device.upper()}.")
        except Exception as e:
            logger.warning(f"[OpenCLIPEngine] Prewarming warning: {e}")

    def generate_image_embedding(self, image_input: Union[str, Path, Image.Image, np.ndarray]) -> np.ndarray:
        """
        Generates a 768-dimensional L2-normalized OpenCLIP embedding vector for an image or crop.
        Validates embedding for NaNs, dimensions, and norm.
        """
        if not getattr(self, "_is_initialized", False):
            self.initialize()

        # 1. Load / Convert Input to PIL Image
        try:
            if isinstance(image_input, (str, Path)):
                pil_img = Image.open(str(image_input)).convert("RGB")
            elif isinstance(image_input, np.ndarray):
                # OpenCV BGR to PIL RGB
                if len(image_input.shape) == 3 and image_input.shape[2] == 3:
                    pil_img = Image.fromarray(image_input[:, :, ::-1])
                else:
                    pil_img = Image.fromarray(image_input)
            elif isinstance(image_input, Image.Image):
                pil_img = image_input.convert("RGB")
            else:
                raise ValueError(f"Unsupported image input type: {type(image_input)}")
        except Exception as e:
            logger.error(f"[OpenCLIPEngine] Image loading error: {str(e)}")
            raise ValueError(f"Failed to load image input: {str(e)}")

        # 2. Preprocess & OpenCLIP Inference (FP16 autocast if CUDA)
        try:
            tensor_img = self.preprocess(pil_img).unsqueeze(0).to(self.device)

            with torch.inference_mode():
                if self.device == "cuda":
                    with torch.amp.autocast("cuda", dtype=torch.float16):
                        features = self.model.encode_image(tensor_img)
                else:
                    features = self.model.encode_image(tensor_img)

                features = features.cpu().numpy().flatten().astype(np.float32)

        except Exception as e:
            logger.error(f"[OpenCLIPEngine] Inference exception: {str(e)}")
            raise RuntimeError(f"Embedding generation error: {str(e)}")

        # 3. Embedding Validation
        raw_norm = float(np.linalg.norm(features))

        if features is None or len(features) == 0:
            raise ValueError("Generated embedding vector is empty.")

        if len(features) != self.embedding_dim:
            raise ValueError(f"Embedding dimension mismatch. Expected {self.embedding_dim}, got {len(features)}.")

        if np.isnan(features).any() or np.isinf(features).any():
            raise ValueError("Embedding vector contains NaN or Inf values.")

        if raw_norm <= 1e-7:
            raise ValueError(f"Invalid zero vector norm: {raw_norm}")

        # 4. L2 Normalization
        normalized_features = features / raw_norm

        return normalized_features

    def generate_image_embeddings_batch(self, image_inputs: list, batch_size: int = 32) -> np.ndarray:
        """
        Generates 768-dimensional L2-normalized OpenCLIP embedding vectors for a list of images or crops in GPU/CPU micro-batches.
        Uses parallel CPU preprocessing and FP16 CUDA mixed precision autocast.
        Returns a 2D numpy float32 array of shape (N, 768).
        """
        import os
        from concurrent.futures import ThreadPoolExecutor

        if not getattr(self, "_is_initialized", False):
            self.initialize()

        if not image_inputs:
            return np.empty((0, self.embedding_dim), dtype=np.float32)

        # 1. Parallel CPU preprocessing helper
        def _process_item(item):
            try:
                if isinstance(item, (str, Path)):
                    pil_img = Image.open(str(item)).convert("RGB")
                elif isinstance(item, np.ndarray):
                    if len(item.shape) == 3 and item.shape[2] == 3:
                        pil_img = Image.fromarray(item[:, :, ::-1])
                    else:
                        pil_img = Image.fromarray(item)
                elif isinstance(item, Image.Image):
                    pil_img = item.convert("RGB")
                else:
                    pil_img = Image.new("RGB", (224, 224), color=(0, 0, 0))
            except Exception as e:
                logger.warning(f"[OpenCLIPEngine] Batch image load fallback for item: {str(e)}")
                pil_img = Image.new("RGB", (224, 224), color=(0, 0, 0))

            return self.preprocess(pil_img)

        # Parallelize CPU preprocessing while preserving exact order
        num_workers = min(8, max(1, os.cpu_count() or 4))
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            all_tensors = list(executor.map(_process_item, image_inputs))

        all_embeddings = []
        total_items = len(all_tensors)
        actual_batch_size = batch_size if self.device == "cuda" else 16

        for i in range(0, total_items, actual_batch_size):
            chunk_tensors = all_tensors[i:i + actual_batch_size]
            tensors = torch.stack(chunk_tensors).to(self.device)

            with torch.inference_mode():
                if self.device == "cuda":
                    with torch.amp.autocast("cuda", dtype=torch.float16):
                        features = self.model.encode_image(tensors)
                else:
                    features = self.model.encode_image(tensors)

                features_np = features.cpu().numpy().astype(np.float32)

            # L2 normalize each vector in batch
            norms = np.linalg.norm(features_np, axis=1, keepdims=True)
            norms[norms <= 1e-7] = 1.0
            norm_features = features_np / norms
            all_embeddings.append(norm_features)

        result_matrix = np.vstack(all_embeddings).astype(np.float32)
        return result_matrix

    def generate_text_embedding(self, text_query: str) -> np.ndarray:
        """
        Generates a 768-dimensional L2-normalized OpenCLIP text embedding vector for an English query.
        Uses a bounded thread-safe LRU cache (max 256) keyed by (query_clean, device).
        """
        if not getattr(self, "_is_initialized", False):
            self.initialize()

        if not text_query or not isinstance(text_query, str) or not text_query.strip():
            raise ValueError("Query string cannot be empty.")

        query_clean = text_query.strip().lower()
        cache_key = f"{query_clean}::{self.device}"

        # 1. LRU Cache Lookup
        with self._cache_lock:
            if cache_key in self._text_cache:
                # Refresh LRU order
                self._cache_order.remove(cache_key)
                self._cache_order.append(cache_key)
                return self._text_cache[cache_key].copy()

        # 2. Text Tokenization & OpenCLIP Inference
        try:
            tokens = open_clip.tokenize([query_clean]).to(self.device)

            with torch.inference_mode():
                features = self.model.encode_text(tokens)
                features = features.cpu().numpy().flatten().astype(np.float32)

        except Exception as e:
            logger.error(f"[OpenCLIPEngine] Text encoding exception for query '{query_clean}': {str(e)}")
            raise RuntimeError(f"Text query embedding error: {str(e)}")

        raw_norm = float(np.linalg.norm(features))

        if features is None or len(features) == 0:
            raise ValueError("Generated text embedding vector is empty.")

        if len(features) != self.embedding_dim:
            raise ValueError(f"Text embedding dimension mismatch. Expected {self.embedding_dim}, got {len(features)}.")

        if np.isnan(features).any() or np.isinf(features).any():
            raise ValueError("Text embedding vector contains NaN or Inf values.")

        if raw_norm <= 1e-7:
            raise ValueError(f"Invalid zero vector norm for text query: {raw_norm}")

        normalized_features = features / raw_norm

        # 3. Store in LRU Cache (max size 256)
        with self._cache_lock:
            if cache_key not in self._text_cache:
                if len(self._cache_order) >= 256:
                    oldest_key = self._cache_order.pop(0)
                    self._text_cache.pop(oldest_key, None)
                self._text_cache[cache_key] = normalized_features.copy()
                self._cache_order.append(cache_key)

        return normalized_features

    def generate_crop_embeddings_with_cache(
        self,
        crop_items: List[Dict[str, Any]],
        batch_size: int = 32
    ) -> Tuple[np.ndarray, int, int]:
        """
        Generates 768-dimensional L2-normalized float32 OpenCLIP embedding vectors for candidate crops
        using per-crop persistent cache (storage/debug/{vid}/crop_embeddings_v1/{tid}/frame_XXXX_{sub_type}.npy).
        
        crop_items: list of dicts: {"crop_path": Path/str, "crop_sub": np.ndarray/PIL, "sub_type": str}
        Returns (result_matrix, cache_hits, cache_misses).
        """
        if not getattr(self, "_is_initialized", False):
            self.initialize()

        if not crop_items:
            return np.empty((0, self.embedding_dim), dtype=np.float32), 0, 0

        model_fp = getattr(self, "model_fingerprint", f"{self.model_name}:{self.pretrained}:768")

        results = [None] * len(crop_items)
        missing_indices = []
        missing_images = []

        cache_hits = 0
        cache_misses = 0

        # 1. Perform Per-Crop Cache Lookup
        for idx, item in enumerate(crop_items):
            c_path = item.get("crop_path")
            sub_type = item.get("sub_type", "full")

            cached_vec = TrackCropEmbeddingCache.load_cached_vector(
                crop_path=c_path,
                sub_type=sub_type,
                model_fingerprint=model_fp,
                embedding_dim=self.embedding_dim
            )

            if cached_vec is not None:
                results[idx] = cached_vec
                cache_hits += 1
            else:
                missing_indices.append(idx)
                missing_images.append(item.get("crop_sub"))
                cache_misses += 1

        # 2. Compute OpenCLIP Inference ONLY for Missing Crops
        if missing_indices:
            logger.info(f"[OpenCLIPEngine] Cache lookup: {cache_hits} hits, {cache_misses} misses. Computing FP16 GPU pass for {cache_misses} missing crops.")
            new_vectors = self.generate_image_embeddings_batch(missing_images, batch_size=batch_size)

            # 3. Persist newly computed vectors to cache
            for miss_idx, vec in zip(missing_indices, new_vectors):
                results[miss_idx] = vec
                item = crop_items[miss_idx]
                c_path = item.get("crop_path")
                sub_type = item.get("sub_type", "full")

                TrackCropEmbeddingCache.save_cached_vector(
                    crop_path=c_path,
                    sub_type=sub_type,
                    vector=vec,
                    model_fingerprint=model_fp,
                    embedding_dim=self.embedding_dim
                )

        result_matrix = np.vstack(results).astype(np.float32)
        return result_matrix, cache_hits, cache_misses


class TrackCropEmbeddingCache:
    """
    Phase 3 Persistent Per-Crop Embedding Cache for ChronoLens.
    Stores single float32 normalized 768-D vectors at:
      storage/debug/{videoId}/crop_embeddings_v1/{trackId}/frame_XXXX_{sub_type}.npy
    alongside companion metadata headers:
      storage/debug/{videoId}/crop_embeddings_v1/{trackId}/frame_XXXX_{sub_type}.meta.json
    """

    _locks: Dict[str, threading.Lock] = {}
    _global_lock = threading.Lock()

    @classmethod
    def _get_lock(cls, key: str) -> threading.Lock:
        with cls._global_lock:
            if key not in cls._locks:
                cls._locks[key] = threading.Lock()
            return cls._locks[key]

    @classmethod
    def get_cache_paths(cls, crop_path: Union[str, Path], sub_type: str = "full") -> Tuple[Path, Path, str]:
        p = Path(crop_path)
        vid = p.parent.parent.parent.name
        tid = p.parent.name
        stem = p.stem
        cache_dir = settings.DEBUG_DIR / vid / "crop_embeddings_v1" / str(tid)
        cache_dir.mkdir(parents=True, exist_ok=True)

        npy_path = cache_dir / f"{stem}_{sub_type}.npy"
        meta_path = cache_dir / f"{stem}_{sub_type}.meta.json"
        crop_key = f"{vid}:{tid}:{stem}:{sub_type}"
        return npy_path, meta_path, crop_key

    @classmethod
    def load_cached_vector(
        cls,
        crop_path: Union[str, Path],
        sub_type: str,
        model_fingerprint: str,
        embedding_dim: int = 768
    ) -> Optional[np.ndarray]:
        try:
            npy_path, meta_path, crop_key = cls.get_cache_paths(crop_path, sub_type)
        except Exception:
            return None

        if not npy_path.exists() or not meta_path.exists():
            return None

        lock = cls._get_lock(crop_key)
        with lock:
            if not npy_path.exists() or not meta_path.exists():
                return None

            try:
                import json
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)

                c_path = Path(crop_path)
                if not c_path.exists():
                    return None

                st = c_path.stat()
                if meta.get("file_size") != st.st_size or meta.get("file_mtime") != st.st_mtime:
                    logger.debug(f"[CropCache] Invalidation for {crop_key}: file mtime/size mismatch.")
                    return None

                if meta.get("model_fingerprint") != model_fingerprint:
                    logger.debug(f"[CropCache] Invalidation for {crop_key}: model fingerprint mismatch.")
                    return None

                if meta.get("embedding_dim") != embedding_dim or meta.get("preprocess_version") != "v1":
                    return None

                vec = np.load(str(npy_path))
                if vec is None or vec.shape != (embedding_dim,) or vec.dtype != np.float32:
                    logger.warning(f"[CropCache] Invalid vector shape/dtype for {crop_key}")
                    return None

                if np.isnan(vec).any() or np.isinf(vec).any():
                    logger.warning(f"[CropCache] NaN/Inf vector for {crop_key}")
                    return None

                norm = float(np.linalg.norm(vec))
                if abs(norm - 1.0) > 1e-2:
                    logger.warning(f"[CropCache] Vector norm not 1.0 for {crop_key}: {norm}")
                    return None

                return vec.astype(np.float32)

            except Exception as e:
                logger.warning(f"[CropCache] Cache read error for {crop_key}: {e}")
                return None

    @classmethod
    def save_cached_vector(
        cls,
        crop_path: Union[str, Path],
        sub_type: str,
        vector: np.ndarray,
        model_fingerprint: str,
        embedding_dim: int = 768
    ):
        try:
            npy_path, meta_path, crop_key = cls.get_cache_paths(crop_path, sub_type)
        except Exception as e:
            logger.warning(f"[CropCache] Path creation error: {e}")
            return

        lock = cls._get_lock(crop_key)
        with lock:
            try:
                import json
                c_path = Path(crop_path)
                if not c_path.exists():
                    return

                st = c_path.stat()

                meta_data = {
                    "crop_path": str(crop_path),
                    "file_size": st.st_size,
                    "file_mtime": st.st_mtime,
                    "model_fingerprint": model_fingerprint,
                    "embedding_dim": embedding_dim,
                    "preprocess_version": "v1",
                    "sub_type": sub_type,
                    "dtype": "float32",
                    "shape": [embedding_dim]
                }

                vec_f32 = vector.astype(np.float32)

                # Atomic write for .npy
                tmp_npy = npy_path.with_suffix(".tmp.npy")
                np.save(str(tmp_npy), vec_f32)
                os.replace(str(tmp_npy), str(npy_path))

                # Atomic write for .meta.json
                tmp_meta = meta_path.with_suffix(".tmp.json")
                with open(tmp_meta, "w", encoding="utf-8") as f:
                    json.dump(meta_data, f, indent=2)
                os.replace(str(tmp_meta), str(meta_path))

            except Exception as e:
                logger.warning(f"[CropCache] Save error for {crop_key}: {e}")


# Global singleton instance
openclip_engine = OpenCLIPEngine()


