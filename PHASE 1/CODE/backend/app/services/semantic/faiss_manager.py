import os
import logging
import threading
from pathlib import Path
from typing import Tuple
import faiss
import numpy as np
from app.core.config import settings

logger = logging.getLogger("chronolens.semantic.faiss")


class FAISSManager:
    """
    Manages dual independent FAISS vector indices for ChronoLens:
    1. frame.index  (Frame level embeddings)
    2. object.index (Tracked object crop embeddings)
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(FAISSManager, cls).__new__(cls)
                    cls._instance._is_initialized = False
        return cls._instance

    @property
    def frame_index_path(self) -> Path:
        return settings.FRAME_FAISS_PATH

    @property
    def object_index_path(self) -> Path:
        return settings.OBJECT_FAISS_PATH

    def initialize(self, dimension: int = 768, force_reload: bool = False):
        """Initializes or loads persisted FAISS indices from disk."""
        if getattr(self, "_is_initialized", False) and not force_reload:
            return

        with self._lock:
            if getattr(self, "_is_initialized", False) and not force_reload:
                return

            self.dimension = dimension
            settings.FAISS_DIR.mkdir(parents=True, exist_ok=True)


            # 1. Initialize or Load Frame Index
            if self.frame_index_path.exists():
                try:
                    self.frame_index = faiss.read_index(str(self.frame_index_path))
                    logger.info(f"[FAISSManager] Loaded persisted frame index with {self.frame_index.ntotal} vectors.")
                except Exception as e:
                    logger.warning(f"[FAISSManager] Failed to read frame index ({str(e)}). Creating fresh IndexFlatIP.")
                    self.frame_index = faiss.IndexFlatIP(self.dimension)
            else:
                self.frame_index = faiss.IndexFlatIP(self.dimension)

            # 2. Initialize or Load Object Index
            if self.object_index_path.exists():
                try:
                    self.object_index = faiss.read_index(str(self.object_index_path))
                    logger.info(f"[FAISSManager] Loaded persisted object index with {self.object_index.ntotal} vectors.")
                except Exception as e:
                    logger.warning(f"[FAISSManager] Failed to read object index ({str(e)}). Creating fresh IndexFlatIP.")
                    self.object_index = faiss.IndexFlatIP(self.dimension)
            else:
                self.object_index = faiss.IndexFlatIP(self.dimension)

            self._is_initialized = True
            logger.info(f"[FAISSManager] Initialized dual indices. Frame Vectors: {self.frame_index.ntotal}, Object Vectors: {self.object_index.ntotal}")

    def add_frame_vector(self, vector: np.ndarray) -> int:
        """
        Adds a single L2-normalized 768d float32 vector to the frame index.
        Persists index to disk and returns the assigned faissId.
        """
        if not getattr(self, "_is_initialized", False):
            self.initialize()

        vec_2d = np.ascontiguousarray(vector.reshape(1, -1).astype(np.float32))

        with self._lock:
            faiss_id = self.frame_index.ntotal
            self.frame_index.add(vec_2d)
            faiss.write_index(self.frame_index, str(self.frame_index_path))

        return faiss_id

    def add_frame_vectors_batch(self, vectors: np.ndarray) -> list:
        """
        Adds a batch of 768d vectors to frame FAISS index and writes index to disk ONCE.
        Returns list of assigned faissIds.
        """
        if not getattr(self, "_is_initialized", False):
            self.initialize()

        if vectors is None or len(vectors) == 0:
            return []

        if vectors.ndim == 1:
            vectors = vectors.reshape(1, -1)

        vec_2d = np.ascontiguousarray(vectors.astype(np.float32))
        num_vecs = vec_2d.shape[0]

        with self._lock:
            start_id = self.frame_index.ntotal
            self.frame_index.add(vec_2d)
            faiss.write_index(self.frame_index, str(self.frame_index_path))
            return list(range(start_id, start_id + num_vecs))

    def add_object_vector(self, vector: np.ndarray) -> int:
        """
        Adds a single L2-normalized 768d float32 vector to the object index.
        Persists index to disk and returns the assigned faissId.
        """
        if not getattr(self, "_is_initialized", False):
            self.initialize()

        vec_2d = np.ascontiguousarray(vector.reshape(1, -1).astype(np.float32))

        with self._lock:
            faiss_id = self.object_index.ntotal
            self.object_index.add(vec_2d)
            faiss.write_index(self.object_index, str(self.object_index_path))

        return faiss_id

    def add_object_vectors_batch(self, vectors: np.ndarray) -> list:
        """
        Adds a batch of 768d vectors to object FAISS index and writes index to disk ONCE.
        Returns list of assigned faissIds.
        """
        if not getattr(self, "_is_initialized", False):
            self.initialize()

        if vectors is None or len(vectors) == 0:
            return []

        if vectors.ndim == 1:
            vectors = vectors.reshape(1, -1)

        vec_2d = np.ascontiguousarray(vectors.astype(np.float32))
        num_vecs = vec_2d.shape[0]

        with self._lock:
            start_id = self.object_index.ntotal
            self.object_index.add(vec_2d)
            faiss.write_index(self.object_index, str(self.object_index_path))
            return list(range(start_id, start_id + num_vecs))

    def get_counts(self) -> Tuple[int, int]:
        """Returns (frame_faiss_size, object_faiss_size) synced from disk."""
        if not getattr(self, "_is_initialized", False):
            self.initialize()

        with self._lock:
            if hasattr(self, "frame_index_path") and self.frame_index_path.exists():
                try:
                    self.frame_index = faiss.read_index(str(self.frame_index_path))
                except Exception as e:
                    logger.warning(f"[FAISSManager] Sync frame index error: {str(e)}")

            if hasattr(self, "object_index_path") and self.object_index_path.exists():
                try:
                    self.object_index = faiss.read_index(str(self.object_index_path))
                except Exception as e:
                    logger.warning(f"[FAISSManager] Sync object index error: {str(e)}")

            return self.frame_index.ntotal, self.object_index.ntotal


    def reset_indices(self) -> bool:
        """
        Resets both frame and object FAISS indices in memory to empty IndexFlatIP(768)
        and overwrites index files on disk with empty indices.
        """
        with self._lock:
            dim = getattr(self, "dimension", 768)
            frame_path = getattr(self, "frame_index_path", settings.FRAME_FAISS_PATH)
            object_path = getattr(self, "object_index_path", settings.OBJECT_FAISS_PATH)

            settings.FAISS_DIR.mkdir(parents=True, exist_ok=True)

            self.frame_index = faiss.IndexFlatIP(dim)
            self.object_index = faiss.IndexFlatIP(dim)

            faiss.write_index(self.frame_index, str(frame_path))
            faiss.write_index(self.object_index, str(object_path))

            self._is_initialized = True
            logger.info(f"[FAISSManager] Reset dual FAISS indices to 0 vectors and persisted empty files to disk.")
            return True

    def search_frame_index(self, query_vector: np.ndarray, top_k: int = 10) -> list:
        """
        Searches frame FAISS index using L2-normalized 768d query vector.
        Returns list of (faiss_id, cosine_similarity) tuples sorted by similarity descending.
        """
        if not getattr(self, "_is_initialized", False):
            self.initialize()

        with self._lock:
            ntotal = self.frame_index.ntotal
            if ntotal == 0:
                return []

            k = min(top_k, ntotal)
            vec_2d = np.ascontiguousarray(query_vector.reshape(1, -1).astype(np.float32))
            distances, indices = self.frame_index.search(vec_2d, k)

            results = []
            if len(indices) > 0 and len(distances) > 0:
                for idx, dist in zip(indices[0], distances[0]):
                    if idx >= 0:
                        results.append((int(idx), float(dist)))
            return results

    def search_object_index(self, query_vector: np.ndarray, top_k: int = 10) -> list:
        """
        Searches object FAISS index using L2-normalized 768d query vector.
        Returns list of (faiss_id, cosine_similarity) tuples sorted by similarity descending.
        """
        if not getattr(self, "_is_initialized", False):
            self.initialize()

        with self._lock:
            ntotal = self.object_index.ntotal
            if ntotal == 0:
                return []

            k = min(top_k, ntotal)
            vec_2d = np.ascontiguousarray(query_vector.reshape(1, -1).astype(np.float32))
            distances, indices = self.object_index.search(vec_2d, k)

            results = []
            if len(indices) > 0 and len(distances) > 0:
                for idx, dist in zip(indices[0], distances[0]):
                    if idx >= 0:
                        results.append((int(idx), float(dist)))
            return results


# Global singleton instance
faiss_manager = FAISSManager()


