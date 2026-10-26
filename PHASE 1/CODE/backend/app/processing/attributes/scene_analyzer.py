import logging
from typing import Dict, Any, List, Optional
import numpy as np
from PIL import Image

from app.services.semantic.openclip_engine import openclip_engine

logger = logging.getLogger("chronolens.processing.scene")


ENVIRONMENT_PROMPTS = [
    ("indoor", "an indoor room or building environment"),
    ("outdoor", "an outdoor street, road, or open space environment")
]

LOCATION_PROMPTS = [
    ("office", "an indoor office or business meeting room"),
    ("classroom", "an indoor classroom or lecture hall"),
    ("corridor", "an indoor hallway or building corridor"),
    ("road", "an outdoor road, street, or highway"),
    ("parking", "a parking area, garage, or lot"),
    ("park", "an outdoor park, garden, or natural open field")
]


class SceneAnalyzer:
    """
    Phase 2.4 Scene Context & Environment Analyzer.
    Uses zero-shot OpenCLIP prompt similarity to classify frame environment (indoor/outdoor)
    and location type (office, road, corridor, classroom, etc.), combined with object presence count.
    Employs scene sampling to avoid redundant per-frame computation.
    """

    @classmethod
    def analyze_frame_scene(
        cls,
        frame_img: Any,
        frame_number: int,
        detections_in_frame: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Analyzes a single sampled video frame for scene environment and location type.
        """
        detections = detections_in_frame or []
        person_count = sum(1 for d in detections if d.get("objectClass") == "person")
        vehicle_classes = {"car", "truck", "bus", "motorcycle", "bicycle"}
        vehicle_count = sum(1 for d in detections if d.get("objectClass") in vehicle_classes)

        crowd_level = "high" if person_count >= 5 else ("medium" if person_count >= 2 else "low")

        env_name = "unknown"
        env_conf = 0.0
        loc_name = "unknown"
        loc_conf = 0.0

        try:
            # Generate frame image embedding
            frame_emb = openclip_engine.generate_image_embedding(frame_img)

            # Environment Zero-Shot Prompts
            env_sims = []
            for ename, eprompt in ENVIRONMENT_PROMPTS:
                p_emb = openclip_engine.generate_text_embedding(eprompt)
                sim = float(np.dot(frame_emb, p_emb))
                env_sims.append((ename, sim))

            best_env = max(env_sims, key=lambda x: x[1])
            if best_env[1] >= 0.20:
                env_name = best_env[0]
                env_conf = round(max(0.0, best_env[1]), 4)

            # Location Type Zero-Shot Prompts
            loc_sims = []
            for lname, lprompt in LOCATION_PROMPTS:
                p_emb = openclip_engine.generate_text_embedding(lprompt)
                sim = float(np.dot(frame_emb, p_emb))
                loc_sims.append((lname, sim))

            best_loc = max(loc_sims, key=lambda x: x[1])
            if best_loc[1] >= 0.22:
                loc_name = best_loc[0]
                loc_conf = round(max(0.0, best_loc[1]), 4)

        except Exception as e:
            logger.warning(f"[SceneAnalyzer] Exception during scene analysis for frame {frame_number}: {str(e)}")

        return {
            "frameNumber": frame_number,
            "environment": env_name,
            "environmentConfidence": env_conf,
            "locationType": loc_name,
            "locationConfidence": loc_conf,
            "crowdLevel": crowd_level,
            "peoplePresent": person_count,
            "vehiclesPresent": vehicle_count
        }
