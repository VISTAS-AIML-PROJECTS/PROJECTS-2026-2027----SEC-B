import unittest
from app.search.ranking_engine import HybridRankingEngine, hybrid_ranking_engine


class TestHybridRankingEngine(unittest.TestCase):

    def test_weight_validation(self):
        engine = HybridRankingEngine(0.75, 0.15, 0.10)
        self.assertEqual(engine.w_semantic, 0.75)
        self.assertEqual(engine.w_yolo, 0.15)
        self.assertEqual(engine.w_persistence, 0.10)

        with self.assertRaises(ValueError):
            HybridRankingEngine(0.50, 0.50, 0.50)

    def test_calculate_final_score(self):
        engine = HybridRankingEngine(0.75, 0.15, 0.10)

        # sim=0.80, yolo=0.90, pers=0.60
        # Score = 0.75*0.80 + 0.15*0.90 + 0.10*0.60 = 0.60 + 0.135 + 0.06 = 0.7950
        score = engine.calculate_final_score(0.80, 0.90, 0.60)
        self.assertEqual(score, 0.7950)

    def test_confidence_badge_thresholds(self):
        self.assertEqual(HybridRankingEngine.compute_confidence_badge(0.45), "Excellent Match")
        self.assertEqual(HybridRankingEngine.compute_confidence_badge(0.40), "Excellent Match")
        self.assertEqual(HybridRankingEngine.compute_confidence_badge(0.35), "Good Match")
        self.assertEqual(HybridRankingEngine.compute_confidence_badge(0.30), "Good Match")
        self.assertEqual(HybridRankingEngine.compute_confidence_badge(0.25), "Possible Match")
        self.assertEqual(HybridRankingEngine.compute_confidence_badge(0.20), "Possible Match")
        self.assertEqual(HybridRankingEngine.compute_confidence_badge(0.15), "Rejected")

    def test_independent_ranking(self):
        frames = [
            {"videoId": "v1", "frameNumber": 1, "similarityScore": 0.40, "averageYOLOConfidence": 0.50, "trackPersistence": 0.50},
            {"videoId": "v1", "frameNumber": 2, "similarityScore": 0.80, "averageYOLOConfidence": 0.90, "trackPersistence": 0.50},
        ]

        objects = [
            {"videoId": "v1", "trackId": 1, "similarityScore": 0.30, "averageYOLOConfidence": 0.40, "trackPersistence": 0.20},
            {"videoId": "v1", "trackId": 2, "similarityScore": 0.70, "averageYOLOConfidence": 0.85, "trackPersistence": 0.90},
        ]

        engine = HybridRankingEngine(0.75, 0.15, 0.10)
        ranked_frames, ranked_objects, elapsed_ms = engine.rank(frames, objects)

        # Check frame ranking
        self.assertEqual(len(ranked_frames), 2)
        self.assertEqual(ranked_frames[0]["frameNumber"], 2)  # Higher score first
        self.assertEqual(ranked_frames[0]["rankingPosition"], 1)
        self.assertEqual(ranked_frames[1]["rankingPosition"], 2)

        # Check object ranking
        self.assertEqual(len(ranked_objects), 2)
        self.assertEqual(ranked_objects[0]["trackId"], 2)  # Higher score first
        self.assertEqual(ranked_objects[0]["rankingPosition"], 1)
        self.assertEqual(ranked_objects[1]["rankingPosition"], 2)


if __name__ == "__main__":
    unittest.main()
