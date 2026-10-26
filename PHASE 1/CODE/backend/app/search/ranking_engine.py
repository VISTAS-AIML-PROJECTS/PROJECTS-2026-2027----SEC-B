import time
import logging
from typing import List, Dict, Any, Tuple

from app.core.config import settings

logger = logging.getLogger("chronolens.search.ranking")


class HybridRankingEngine:
    """
    Phase 2.3 Hybrid Semantic Ranking & Retrieval Intelligence.
    Calculates final hybrid scores, confidence badges, ranking positions, and deterministic explanations
    for frame and object search results.

    STRICT CONSTRAINTS:
    - Completely read-only.
    - Zero MongoDB access inside ranking engine.
    - Accepts already-extracted signals (semanticSimilarity, averageYOLOConfidence, trackPersistence).
    - Ranks frameResults and objectResults independently.
    """

    def __init__(
        self,
        weight_semantic: float = None,
        weight_yolo: float = None,
        weight_persistence: float = None
    ):
        self.w_semantic = (
            weight_semantic if weight_semantic is not None else getattr(settings, "RANKING_WEIGHT_SEMANTIC", 0.75)
        )
        self.w_yolo = (
            weight_yolo if weight_yolo is not None else getattr(settings, "RANKING_WEIGHT_YOLO", 0.15)
        )
        self.w_persistence = (
            weight_persistence if weight_persistence is not None else getattr(settings, "RANKING_WEIGHT_PERSISTENCE", 0.10)
        )

        total_weight = round(self.w_semantic + self.w_yolo + self.w_persistence, 4)
        if abs(total_weight - 1.0) > 1e-3:
            raise ValueError(f"Hybrid Ranking weights must sum to 1.0, got sum = {total_weight}")

    @staticmethod
    def compute_confidence_badge(final_score: float) -> str:
        """
        Assigns confidence badge based on FinalScore thresholds:
        - >= 0.40 -> 'Excellent Match'
        - >= 0.30 and < 0.40 -> 'Good Match'
        - >= 0.20 and < 0.30 -> 'Possible Match'
        - < 0.20 -> 'Rejected'
        """
        if final_score >= 0.40:
            return "Excellent Match"
        elif final_score >= 0.30:
            return "Good Match"
        elif final_score >= 0.20:
            return "Possible Match"
        else:
            return "Rejected"

    @staticmethod
    def generate_explanation(
        sim: float,
        yolo_conf: float,
        persistence: float,
        is_object: bool = True
    ) -> str:
        """
        Generates deterministic, human-readable ranking explanation string
        derived directly from ranking signal values without external LLMs.
        """
        if is_object:
            if sim >= 0.30 and yolo_conf >= 0.80 and persistence >= 0.50:
                return "Strong semantic similarity with high YOLO confidence and persistent track presence."
            elif sim >= 0.30 and yolo_conf >= 0.80:
                return "Strong semantic similarity and high detection confidence."
            elif sim >= 0.30 and persistence >= 0.50:
                return "Strong semantic similarity with persistent track presence."
            elif sim >= 0.25:
                return "High semantic similarity match."
            elif yolo_conf >= 0.80:
                return "High detection confidence with relevant semantic match."
            else:
                return "Relevant track match based on hybrid ranking signals."
        else:
            if sim >= 0.30 and yolo_conf >= 0.80:
                return "High semantic similarity with strong detection confidence."
            elif sim >= 0.30:
                return "High semantic similarity match."
            elif yolo_conf >= 0.80:
                return "Frame match with high object detection confidence."
            else:
                return "Relevant frame match based on hybrid ranking signals."

    def calculate_final_score(self, sim: float, yolo_conf: float, persistence: float) -> float:
        """
        Calculates FinalScore = 0.75 * sim + 0.15 * yolo_conf + 0.10 * persistence.
        Clamps values strictly between 0.0 and 1.0.
        """
        c_sim = max(0.0, min(1.0, float(sim)))
        c_yolo = max(0.0, min(1.0, float(yolo_conf)))
        c_pers = max(0.0, min(1.0, float(persistence)))

        score = (self.w_semantic * c_sim) + (self.w_yolo * c_yolo) + (self.w_persistence * c_pers)
        return round(float(score), 4)

    def rank_frame_results(self, frame_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Ranks frameResults independently by finalScore DESC.
        """
        if not frame_items:
            return []

        ranked_items = []
        for item in frame_items:
            sim = float(item.get("similarityScore", 0.0))
            yolo_conf = float(item.get("averageYOLOConfidence", 0.0))
            pers = float(item.get("trackPersistence", 0.0))

            final_score = self.calculate_final_score(sim, yolo_conf, pers)
            badge = self.compute_confidence_badge(final_score)
            explanation = self.generate_explanation(sim, yolo_conf, pers, is_object=False)

            updated = dict(item)
            updated["finalScore"] = final_score
            updated["finalScorePercentage"] = f"{round(final_score * 100.0, 2)}%"
            updated["confidenceBadge"] = badge
            updated["explanation"] = explanation
            if "sceneContext" in item:
                updated["sceneContext"] = item.get("sceneContext")
            ranked_items.append(updated)

        # Sort independently by finalScore DESC
        ranked_items.sort(key=lambda x: x["finalScore"], reverse=True)

        # Assign 1-indexed ranking positions
        for idx, item in enumerate(ranked_items, start=1):
            item["rankingPosition"] = idx

        return ranked_items

    def rank_object_results(self, object_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Ranks objectResults / trajectory results independently by finalScore DESC.
        """
        if not object_items:
            return []

        ranked_items = []
        for item in object_items:
            sim = float(item.get("similarityScore", item.get("bestSimilarityScore", 0.0)))
            yolo_conf = float(item.get("averageYOLOConfidence", 0.0))
            pers = float(item.get("trackPersistence", 0.0))

            final_score = self.calculate_final_score(sim, yolo_conf, pers)
            badge = self.compute_confidence_badge(final_score)
            explanation = self.generate_explanation(sim, yolo_conf, pers, is_object=True)

            updated = dict(item)
            updated["bestSimilarityScore"] = sim
            updated["bestSimilarityPercentage"] = item.get("similarityPercentage", f"{round(sim * 100.0, 2)}%")
            updated["finalScore"] = final_score
            updated["finalScorePercentage"] = f"{round(final_score * 100.0, 2)}%"
            updated["confidenceBadge"] = badge
            updated["explanation"] = explanation
            if "visualAttributes" in item:
                updated["visualAttributes"] = item.get("visualAttributes")
            ranked_items.append(updated)


        # Sort independently by finalScore DESC
        ranked_items.sort(key=lambda x: x["finalScore"], reverse=True)

        # Assign 1-indexed ranking positions
        for idx, item in enumerate(ranked_items, start=1):
            item["rankingPosition"] = idx

        return ranked_items

    def rank(
        self,
        frame_items: List[Dict[str, Any]],
        object_items: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], float]:
        """
        Executes independent hybrid ranking on frameResults and objectResults.
        Returns (ranked_frame_results, ranked_object_results, ranking_time_ms).
        """
        t0 = time.time()

        ranked_frames = self.rank_frame_results(frame_items)
        ranked_objects = self.rank_object_results(object_items)

        elapsed_ms = round((time.time() - t0) * 1000.0, 3)
        logger.info(
            f"[HybridRankingEngine] Ranked {len(ranked_frames)} frames and {len(ranked_objects)} object tracks independently "
            f"(weights: {self.w_semantic}/{self.w_yolo}/{self.w_persistence}, latency: {elapsed_ms}ms)"
        )

        return ranked_frames, ranked_objects, elapsed_ms


hybrid_ranking_engine = HybridRankingEngine()
