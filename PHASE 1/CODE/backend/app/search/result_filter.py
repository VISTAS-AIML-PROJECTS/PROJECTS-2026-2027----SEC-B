import time
import logging
from typing import List, Tuple

logger = logging.getLogger("chronolens.search.filter")


class ResultFilter:
    """
    Phase 2.2 Similarity Threshold Filter.
    Rejects raw FAISS search hits whose cosine similarity is strictly less than SIMILARITY_THRESHOLD.
    """

    @staticmethod
    def filter_by_threshold(
        hits: List[Tuple[int, float]],
        threshold: float
    ) -> Tuple[List[Tuple[int, float]], int, float]:
        """
        Filters hits by similarity threshold.
        Returns (accepted_hits, rejected_count, filtering_time_ms).
        """
        t0 = time.time()
        accepted = []
        rejected_count = 0

        for faiss_id, score in hits:
            if float(score) >= float(threshold):
                accepted.append((faiss_id, float(score)))
            else:
                rejected_count += 1

        elapsed_ms = round((time.time() - t0) * 1000.0, 3)
        logger.info(f"[ResultFilter] Threshold={threshold}: Accepted={len(accepted)}, Rejected={rejected_count} (time={elapsed_ms}ms)")
        return accepted, rejected_count, elapsed_ms
