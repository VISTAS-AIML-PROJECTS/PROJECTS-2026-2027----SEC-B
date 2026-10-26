import time
import logging
from typing import List, Dict, Any, Tuple
from collections import defaultdict

from app.search.representative_selector import RepresentativeSelector

logger = logging.getLogger("chronolens.search.grouping")


class TrackGrouper:
    """
    Phase 2.2 Duplicate Track Consolidator.
    Groups object detection search hits belonging to the same (videoId, trackId) trajectory
    into a single consolidated result card with trajectory timing metrics and a representative thumbnail.
    """

    @staticmethod
    def group_object_results(records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int, float]:
        """
        Groups list of raw object result items by (videoId, trackId).
        Returns (grouped_object_results, grouped_track_count, grouping_time_ms).
        """
        t0 = time.time()
        if not records:
            return [], 0, 0.0

        # Group by (videoId, trackId)
        groups = defaultdict(list)
        for item in records:
            vid = item.get("videoId")
            tid = item.get("trackId")
            groups[(vid, tid)].append(item)

        consolidated_results: List[Dict[str, Any]] = []

        for (vid, tid), items in groups.items():
            # Select single representative thumbnail & frame
            rep = RepresentativeSelector.select_representative(items)

            # Compute trajectory aggregate timing stats
            timestamps = [float(it.get("timestamp", 0.0)) for it in items]
            scores = [float(it.get("similarityScore", 0.0)) for it in items]

            first_seen = round(float(min(timestamps)), 2)
            last_seen = round(float(max(timestamps)), 2)
            duration = round(last_seen - first_seen, 2)
            appearance_count = len(items)

            best_sim = round(float(max(scores)), 4)
            best_sim_pct = f"{round(best_sim * 100.0, 2)}%"

            consolidated_item = {
                "videoId": vid,
                "trackId": tid,
                "objectClass": rep.get("objectClass", "object"),
                "frameNumber": rep.get("frameNumber"),
                "timestamp": rep.get("timestamp"),
                "cropThumbnail": rep.get("cropThumbnail"),
                "annotatedFrame": rep.get("annotatedFrame"),
                "faissId": rep.get("faissId"),
                "similarityScore": best_sim,
                "similarityPercentage": best_sim_pct,
                "appearanceCount": appearance_count,
                "firstSeen": first_seen,
                "lastSeen": last_seen,
                "trackDurationSec": duration,
                "indexOrigin": "Object FAISS Index",
                "visualAttributes": rep.get("visualAttributes") or next((it.get("visualAttributes") for it in items if it.get("visualAttributes")), None)
            }


            consolidated_results.append(consolidated_item)

        # Sort consolidated tracks by best similarity score descending
        consolidated_results.sort(key=lambda x: x["similarityScore"], reverse=True)

        elapsed_ms = round((time.time() - t0) * 1000.0, 3)
        logger.info(f"[TrackGrouper] Consolidated {len(records)} raw object hits into {len(consolidated_results)} unique tracks (time={elapsed_ms}ms)")

        return consolidated_results, len(consolidated_results), elapsed_ms
