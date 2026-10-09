import numpy as np
from collections import deque
import time

class STrack:
    """
    Single Track Object representing a tracked truck instance.
    """
    _count = 1

    def __init__(self, bbox, score, class_id=7, label=None, ground_truth_plate=None):
        # Format track ID as TRK001, TRK002, etc.
        self.track_id = f"TRK{STrack._count:03d}"
        STrack._count += 1
        
        self.bbox = np.array(bbox, dtype=float)  # [x1, y1, x2, y2]
        self.score = score
        self.class_id = class_id
        self.label = label or ('truck' if class_id in [7, 6] else ('bus' if class_id == 5 else ('car' if class_id == 2 else 'vehicle')))
        self.history = deque(maxlen=60)          # centroid history for trajectory & speed
        self.ground_truth_plate = ground_truth_plate
        
        cx = (bbox[0] + bbox[2]) / 2.0
        cy = (bbox[1] + bbox[3]) / 2.0
        self.history.append((cx, cy, time.time()))
        
        self.state = 'Tracked'                   # 'New', 'Tracked', 'Lost'
        self.time_since_update = 0
        self.hits = 1
        self.age = 1
        
        # Attributes attached during analysis
        self.speed_kmh = 0.0
        self.license_plate = ground_truth_plate
        self.plate_confidence = 0.98 if ground_truth_plate else 0.0
        self.is_real_plate = True if ground_truth_plate else False
        self.is_fallback_plate = False
        self.truck_type = None
        self.color = None
        self.cargo_attributes = None
        self.is_overspeed = False
        self.is_blocklisted = False
        self.first_seen = time.time()
        self.last_seen = time.time()
        self.alert_dispatched = False

    def update(self, new_bbox, score):
        self.bbox = np.array(new_bbox, dtype=float)
        self.score = score
        self.time_since_update = 0
        self.hits += 1
        self.age += 1
        self.state = 'Tracked'
        self.last_seen = time.time()
        
        cx = (new_bbox[0] + new_bbox[2]) / 2.0
        cy = (new_bbox[1] + new_bbox[3]) / 2.0
        self.history.append((cx, cy, time.time()))

    def mark_missed(self):
        self.time_since_update += 1
        self.age += 1
        if self.time_since_update > 15:
            self.state = 'Removed'
        elif self.time_since_update > 3:
            self.state = 'Lost'


def compute_iou(box1, box2):
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    inter_w = max(0.0, x2 - x1)
    inter_h = max(0.0, y2 - y1)
    inter_area = inter_w * inter_h

    area1 = max(0.0, (box1[2] - box1[0])) * max(0.0, (box1[3] - box1[1]))
    area2 = max(0.0, (box2[2] - box2[0])) * max(0.0, (box2[3] - box2[1]))
    union_area = area1 + area2 - inter_area

    if union_area <= 0:
        return 0.0
    return inter_area / union_area


class ByteTracker:
    """
    ByteTrack Multi-Object Tracker.
    Associates high-confidence detections first, then low-confidence detections.
    Maintains persistent IDs: TRK001, TRK002, etc.
    """
    def __init__(self, high_thresh=0.5, match_thresh=0.7, max_time_lost=25):
        self.tracked_stracks = []  # Active tracks
        self.lost_stracks = []     # Temporarily lost
        self.removed_stracks = []
        self.high_thresh = high_thresh
        self.match_thresh = match_thresh
        self.max_time_lost = max_time_lost

    def update(self, detections):
        """
        Input: detections = [{'bbox': [x1,y1,x2,y2], 'confidence': float, 'class_id': int}, ...]
        Returns: list of active STrack objects
        """
        # Split detections into high score and low score
        high_dets = [d for d in detections if d.get('confidence', 0.8) >= self.high_thresh]
        low_dets = [d for d in detections if d.get('confidence', 0.8) < self.high_thresh]

        pool_tracks = [t for t in self.tracked_stracks if t.state == 'Tracked'] + self.lost_stracks

        # 1st association: High score detections with existing tracks
        unmatched_tracks = []
        unmatched_dets = []
        matched_tracks = []

        if pool_tracks and high_dets:
            # Build IoU cost matrix
            iou_matrix = np.zeros((len(pool_tracks), len(high_dets)), dtype=float)
            for i, track in enumerate(pool_tracks):
                for j, det in enumerate(high_dets):
                    iou_matrix[i, j] = compute_iou(track.bbox, det['bbox'])

            # Greedy matching
            used_tracks = set()
            used_dets = set()
            
            # Sort by highest IoU matches
            indices = np.dstack(np.unravel_index(np.argsort(-iou_matrix.ravel()), iou_matrix.shape))[0]
            for i, j in indices:
                if iou_matrix[i, j] < 0.25:
                    break
                if i in used_tracks or j in used_dets:
                    continue
                
                track = pool_tracks[i]
                det = high_dets[j]
                track.update(det['bbox'], det.get('confidence', 0.9))
                if det.get('_ground_truth_plate') and not track.ground_truth_plate:
                    track.ground_truth_plate = det['_ground_truth_plate']
                    track.license_plate = det['_ground_truth_plate']
                    track.plate_confidence = 0.98
                    track.is_real_plate = True
                matched_tracks.append(track)
                used_tracks.add(i)
                used_dets.add(j)

            unmatched_tracks = [pool_tracks[i] for i in range(len(pool_tracks)) if i not in used_tracks]
            unmatched_dets = [high_dets[j] for j in range(len(high_dets)) if j not in used_dets]
        else:
            unmatched_tracks = pool_tracks
            unmatched_dets = high_dets

        # 2nd association: Low score detections with unmatched tracks
        if unmatched_tracks and low_dets:
            used_tracks_2 = set()
            for i, track in enumerate(unmatched_tracks):
                best_iou = 0.0
                best_det = None
                for det in low_dets:
                    iou = compute_iou(track.bbox, det['bbox'])
                    if iou > best_iou:
                        best_iou = iou
                        best_det = det
                if best_iou >= 0.3 and best_det is not None:
                    track.update(best_det['bbox'], best_det.get('confidence', 0.5))
                    if best_det.get('_ground_truth_plate') and not track.ground_truth_plate:
                        track.ground_truth_plate = best_det['_ground_truth_plate']
                        track.license_plate = best_det['_ground_truth_plate']
                        track.plate_confidence = 0.98
                        track.is_real_plate = True
                    matched_tracks.append(track)
                    used_tracks_2.add(i)
            unmatched_tracks = [t for i, t in enumerate(unmatched_tracks) if i not in used_tracks_2]

        # Process remaining unmatched tracks
        for track in unmatched_tracks:
            track.mark_missed()

        # Initialize new tracks for unmatched high-score detections
        for det in unmatched_dets:
            new_track = STrack(
                det['bbox'], 
                det.get('confidence', 0.9), 
                det.get('class_id', 7), 
                label=det.get('label'),
                ground_truth_plate=det.get('_ground_truth_plate')
            )
            matched_tracks.append(new_track)

        # Update track state lists
        self.tracked_stracks = [t for t in matched_tracks if t.state == 'Tracked']
        self.lost_stracks = [t for t in unmatched_tracks if t.state == 'Lost']
        
        return self.tracked_stracks

    def predict_tracks(self):
        """
        Sub-millisecond velocity extrapolation for intermediate frames between YOLO detections.
        Keeps tracked vehicles moving naturally at 30 FPS with virtually zero CPU cost.
        """
        now = time.time()
        active = []
        for track in self.tracked_stracks:
            if track.state == 'Tracked':
                if len(track.history) >= 2:
                    p1 = track.history[-1]
                    p0 = track.history[-2]
                    # Compute velocity in pixels per frame
                    dt = max(0.001, p1[2] - p0[2])
                    if dt < 1.0:
                        vx = (p1[0] - p0[0])
                        vy = (p1[1] - p0[1])
                        # Bound velocity to avoid runaway jumps
                        vx = max(-35.0, min(35.0, vx))
                        vy = max(-35.0, min(35.0, vy))
                        track.bbox = track.bbox + np.array([vx, vy, vx, vy], dtype=float)
                        cx = (track.bbox[0] + track.bbox[2]) / 2.0
                        cy = (track.bbox[1] + track.bbox[3]) / 2.0
                        track.history.append((cx, cy, now))
                track.age += 1
                active.append(track)
        self.tracked_stracks = active
        return self.tracked_stracks

