import time
import logging
from typing import Tuple
import numpy as np
from app.services.semantic.openclip_engine import openclip_engine

logger = logging.getLogger("chronolens.search.query_embedder")


class QueryEmbedder:
    """
    Encapsulates text query embedding generation using OpenCLIP singleton.
    Validates text input and returns 768d L2-normalized vector along with latency timing in milliseconds.
    """

    @staticmethod
    def embed_query(query: str) -> Tuple[np.ndarray, float]:
        """
        Encodes query string into OpenCLIP text embedding.
        Returns (embedding_vector, embedding_time_ms).
        """
        if not query or not isinstance(query, str) or not query.strip():
            raise ValueError("Search query string cannot be empty.")

        t0 = time.time()
        embedding_vec = openclip_engine.generate_text_embedding(query.strip())
        elapsed_ms = round((time.time() - t0) * 1000.0, 2)

        logger.info(f"[QueryEmbedder] Generated 768d text embedding for '{query.strip()}' in {elapsed_ms}ms")
        return embedding_vec, elapsed_ms
