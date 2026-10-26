import math
import logging
from typing import List, Dict, Tuple, Optional
from collections import defaultdict, Counter
from app.models.schemas import DetectionItem, TrackItem

logger = logging.getLogger("chronolens.processing.tracker")


class ByteTracker:
    """
    ByteTrack Multi-Object Tracker:
    Associates object detections across sequential frames using IoU, Centroid Spatial Distance,
    Track Buffering (max_age retention), and Majority Class Voting.
    Preserves unique object identities and accurate track metadata (duration, timestamps, classes).
    """
    def __init__(
        self,
        match_thresh: float = 0.15,
        max_centroid_dist: float = 300.0,
        track_buffer: int = 5
    ):
        self.match_thresh = match_thresh
        self.max_centroid_dist = max_centroid_dist
        self.track_buffer = track_buffer

    @staticmethod
    def _compute_iou(boxA: List[float], boxB: List[float]) -> float:
        """Calculates Intersection-over-Union (IoU) between two bounding boxes [x1, y1, x2, y2]."""
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])

        interArea = max(0.0, xB - xA) * max(0.0, yB - yA)
        boxAArea = max(0.0, boxA[2] - boxA[0]) * max(0.0, boxA[3] - boxA[1])
        boxBArea = max(0.0, boxB[2] - boxB[0]) * max(0.0, boxB[3] - boxB[1])

        denominator = float(boxAArea + boxBArea - interArea)
        return interArea / denominator if denominator > 0 else 0.0

    @staticmethod
    def _compute_centroid_distance(boxA: List[float], boxB: List[float]) -> float:
        """Calculates Euclidean distance between centers of two bounding boxes."""
        cA = ((boxA[0] + boxA[2]) / 2.0, (boxA[1] + boxA[3]) / 2.0)
        cB = ((boxB[0] + boxB[2]) / 2.0, (boxB[1] + boxB[3]) / 2.0)
        return math.hypot(cA[0] - cB[0], cA[1] - cB[1])

    def track_objects(self, detections: List[DetectionItem], video_id: str) -> Tuple[List[DetectionItem], List[TrackItem]]:
        """
        Processes detections frame-by-frame, applying ByteTrack multi-object tracking.
        Returns (updated_detections_with_track_ids, consolidated_tracks_list).
        """
        logger.info(f"[ByteTracker] Starting tracking execution for {len(detections)} detections in video_id={video_id}")

        if not detections:
            return [], []

        # Sort detections strictly by frame number
        sorted_detections = sorted(detections, key=lambda d: d.frameNumber)

        # Group detections by frame
        frames_map = defaultdict(list)
        for det in sorted_detections:
            frames_map[det.frameNumber].append(det)

        active_tracks: Dict[int, Dict] = {}
        next_track_id = 1
        all_tracks_store: Dict[int, Dict] = {}

        # Process frames in sequential order
        for frame_num in sorted(frames_map.keys()):
            frame_dets = frames_map[frame_num]
            unmatched_dets = list(frame_dets)

            # Stage 1: Match existing active tracks with current frame detections
            matched_pairs = []

            for track_id, track in list(active_tracks.items()):
                # Skip tracks that expired beyond track_buffer retention window
                if frame_num - track["last_frame"] > self.track_buffer:
                    continue

                best_det = None
                best_score = -1.0

                for det in unmatched_dets:
                    iou = self._compute_iou(track["last_box"], det.boundingBox)
                    dist = self._compute_centroid_distance(track["last_box"], det.boundingBox)
                    
                    # Class matching check: same class OR flexible class smoothing
                    class_match = (det.objectClass.lower() == track["objectClass"].lower())

                    # Calculate spatial association score
                    score = 0.0
                    if iou >= self.match_thresh:
                        score = iou + (1.0 if class_match else 0.5)
                    elif dist <= self.max_centroid_dist:
                        norm_dist = 1.0 - (dist / self.max_centroid_dist)
                        score = (norm_dist * 0.5) + (0.5 if class_match else 0.2)

                    if score > best_score and score >= 0.35:
                        best_score = score
                        best_det = det

                if best_det:
                    matched_pairs.append((track_id, best_det))

            # Apply matched pairs & update track metadata
            for track_id, det in matched_pairs:
                if det in unmatched_dets:
                    unmatched_dets.remove(det)
                    det.trackId = track_id
                    
                    track = active_tracks[track_id]
                    track["last_frame"] = frame_num
                    track["last_box"] = det.boundingBox
                    track["endTime"] = det.timestamp  # FIX: Continuously update endTime
                    track["frames"].append(frame_num)
                    track["confidences"].append(det.confidence)
                    track["classes"].append(det.objectClass)
                    track["trajectory"].append({
                        "frameNumber": frame_num,
                        "timestamp": det.timestamp,
                        "boundingBox": det.boundingBox,
                        "confidence": det.confidence
                    })

            # Stage 2: Create new tracks for remaining unmatched detections
            for det in unmatched_dets:
                t_id = next_track_id
                next_track_id += 1
                det.trackId = t_id

                track_info = {
                    "trackId": t_id,
                    "videoId": video_id,
                    "objectClass": det.objectClass,
                    "classes": [det.objectClass],
                    "confidences": [det.confidence],
                    "startTime": det.timestamp,
                    "endTime": det.timestamp,  # Initialized at start timestamp
                    "last_frame": frame_num,
                    "last_box": det.boundingBox,
                    "frames": [frame_num],
                    "trajectory": [{
                        "frameNumber": frame_num,
                        "timestamp": det.timestamp,
                        "boundingBox": det.boundingBox,
                        "confidence": det.confidence
                    }]
                }
                active_tracks[t_id] = track_info
                all_tracks_store[t_id] = track_info

        # Post-processing: Majority Class Voting & Track Metadata Consolidation
        tracks_list: List[TrackItem] = []
        for t_id, t_info in all_tracks_store.items():
            # Determine majority class across the track's history from matched detections
            majority_class = Counter(t_info["classes"]).most_common(1)[0][0] if t_info["classes"] else t_info["objectClass"]
            avg_conf = sum(t_info["confidences"]) / len(t_info["confidences"]) if t_info["confidences"] else 0.0

            # Update detection object classes to match smoothed majority class
            for det in sorted_detections:
                if det.trackId == t_id:
                    det.objectClass = majority_class

            tracks_list.append(
                TrackItem(
                    trackId=t_id,
                    videoId=video_id,
                    objectClass=majority_class,
                    confidence=round(avg_conf, 4),
                    startTime=t_info["startTime"],
                    endTime=t_info["endTime"],  # FIX: Uses updated endTime
                    frames=t_info["frames"],
                    trajectory=t_info["trajectory"]
                )
            )

        # Sort tracks by Track ID
        tracks_list = sorted(tracks_list, key=lambda t: t.trackId)
        logger.info(f"[ByteTracker] Successfully consolidated {len(tracks_list)} persistent tracks across video {video_id}")
        return sorted_detections, tracks_list


tracker = ByteTracker()
