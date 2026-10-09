import os
import cv2
import time
import threading
import numpy as np
from datetime import datetime, timezone
from backend.ai_engine.detector import YOLOv26TruckDetector
from backend.ai_engine.tracker import ByteTracker
from backend.ai_engine.speed_estimator import SpeedEstimator
from backend.ai_engine.plate_ocr import LicensePlateOCR
from backend.ai_engine.vit_classifier import MTLViTClassifier
from backend.ai_engine.surveillance_simulator import SurveillanceSimulator
from backend.services.alert_manager import alert_manager
from backend.services.logistics import logistics_service
from backend.services.fc_service import fc_service
from backend.database.models import Blocklist
from backend.database.db import SessionLocal
from backend.config import Config


class PipelineManager:
    """
    Central Video AI Pipeline Orchestrator.
    Executes the exact workflow:
    CCTV -> YOLOv26 (Truck Only) -> ByteTrack (TRK001) -> [Speed, Plate OCR, MTL-ViT] -> Alert Manager -> Logistics DB.
    """
    def __init__(self):
        self.detector = YOLOv26TruckDetector()
        self.tracker = ByteTracker()
        self.speed_estimator = SpeedEstimator(
            pixels_per_meter=Config.PIXELS_PER_METER,
            fps=Config.FPS,
            speed_limit=Config.DEFAULT_SPEED_LIMIT
        )
        self.plate_ocr = LicensePlateOCR()
        self.vit_classifier = MTLViTClassifier()
        self.simulator = SurveillanceSimulator()
        
        # State
        self.active_source = 'SIMULATED' # 'SIMULATED', 'WEBCAM', 'VIDEO_FILE'
        self.cap = None
        self.video_file_path = None
        self.is_running = True
        self.current_frame = None
        self.active_tracks_data = [] # Current frame tracked trucks data for telemetry
        self.fps_stat = 30.0
        self.last_frame_time = time.time()
        self.frame_idx = 0
        self.cached_detections = []
        self.frame_skip_ratio = 2 # Detect on alternate frames, extrapolate in between for steady 30 FPS
        
        # Settings
        self.show_bboxes = True
        self.show_speed = True
        self.show_plates = True
        self.show_vit = True
        self.show_trajectories = True
        
        # Thread synchronization & Real-Time Broadcast
        self.lock = threading.Lock()
        self.frame_condition = threading.Condition()
        self.latest_jpeg_bytes = None
        
        # Start dedicated background surveillance worker
        self._worker_thread = threading.Thread(target=self._surveillance_pipeline_worker, daemon=True)
        self._worker_thread.start()

    def _surveillance_pipeline_worker(self):
        """
        Dedicated single-threaded surveillance pipeline worker.
        Continuously captures, runs AI inference/tracking, overlays HUD, and pre-encodes JPEG.
        Runs at steady 25-30 FPS, completely decoupled from HTTP stream request threads.
        """
        while self.is_running:
            try:
                t_start = time.time()
                frame = self.process_frame()
                if frame is not None and getattr(frame, 'size', 0) > 0:
                    ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
                    if ret:
                        jpeg_bytes = buffer.tobytes()
                        with self.frame_condition:
                            self.latest_jpeg_bytes = jpeg_bytes
                            self.frame_condition.notify_all()

                # Maintain steady ~28-30 FPS playback rate
                elapsed = time.time() - t_start
                target_dt = 1.0 / 30.0
                sleep_dur = max(0.001, target_dt - elapsed)
                time.sleep(sleep_dur)
            except Exception as e:
                print(f"⚠️ Pipeline worker error: {e}")
                time.sleep(0.03)

    def set_source(self, source_type, video_path=None):
        with self.lock:
            if self.cap is not None:
                try:
                    self.cap.release()
                except Exception:
                    pass
                self.cap = None
                
            self.active_source = source_type
            if source_type == 'WEBCAM':
                self.cap = cv2.VideoCapture(0)
            elif source_type == 'VIDEO_FILE' and video_path:
                self.video_file_path = os.path.abspath(video_path)
                self.cap = cv2.VideoCapture(self.video_file_path)
                if not self.cap.isOpened():
                    try:
                        self.cap = cv2.VideoCapture(self.video_file_path, cv2.CAP_FFMPEG)
                    except Exception:
                        pass
                # Reset tracker state for the new video
                self.tracker = ByteTracker()
                self.active_tracks_data = []
                self.frame_idx = 0
                # Pre-scan video plates in background thread
                threading.Thread(target=self.plate_ocr.scan_video_plates, args=(self.video_file_path,), daemon=True).start()
            else:
                self.active_source = 'SIMULATED'
                self.tracker = ByteTracker()
                self.active_tracks_data = []
                self.frame_idx = 0

    def update_speed_limit(self, new_limit):
        self.speed_estimator.set_speed_limit(new_limit)

    def process_frame(self):
        """
        Reads one frame from active source, runs AI pipeline, overlays AI HUD, and updates telemetry.
        """
        raw_frame = None
        sim_dets = []

        # 1. Capture Frame from selected source
        if self.active_source == 'SIMULATED':
            raw_frame, sim_dets = self.simulator.step()
        elif self.cap is not None and self.cap.isOpened():
            with self.lock:
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    # Loop video if file
                    if self.active_source == 'VIDEO_FILE' and self.video_file_path:
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        ret, frame = self.cap.read()
                        if not ret or frame is None:
                            try:
                                self.cap.release()
                                self.cap = cv2.VideoCapture(self.video_file_path)
                                if not self.cap.isOpened():
                                    self.cap = cv2.VideoCapture(self.video_file_path, cv2.CAP_FFMPEG)
                                ret, frame = self.cap.read()
                            except Exception as loop_err:
                                print(f"⚠️ Video loop error: {loop_err}")
            if ret and frame is not None:
                raw_frame = frame
            else:
                raw_frame, sim_dets = self.simulator.step()
        else:
            raw_frame, sim_dets = self.simulator.step()

        if raw_frame is None or getattr(raw_frame, 'size', 0) == 0:
            raw_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        else:
            h, w = raw_frame.shape[:2]
            if w != 1280 or h != 720:
                scale = min(1280.0 / w, 720.0 / h)
                nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
                resized = cv2.resize(raw_frame, (nw, nh), interpolation=cv2.INTER_LINEAR)
                top = (720 - nh) // 2
                bottom = 720 - nh - top
                left = (1280 - nw) // 2
                right = 1280 - nw - left
                raw_frame = cv2.copyMakeBorder(resized, top, bottom, left, right, cv2.BORDER_CONSTANT, value=[10, 10, 10])

        # 2. YOLO Heavy Vehicle & Transport Detection with Alternate-Frame Interpolation
        self.frame_idx += 1
        is_detect_frame = (self.frame_idx % self.frame_skip_ratio == 0) or (self.active_source == 'SIMULATED')

        tracked_objects = []
        if self.active_source == 'SIMULATED' and sim_dets:
            tracked_objects = self.tracker.update(sim_dets)
        elif is_detect_frame:
            detections = self.detector.detect(raw_frame)
            tracked_objects = self.tracker.update(detections)
        else:
            # Sub-millisecond (0.05ms) velocity extrapolation between YOLO detections for smooth 30 FPS
            tracked_objects = self.tracker.predict_tracks()

        # 3. Parallel Processing per Tracked Truck (Lazy database session allocation)
        current_active = []
        db_session = None
        def get_db():
            nonlocal db_session
            if db_session is None:
                db_session = SessionLocal()
            return db_session
        
        try:
            for track in tracked_objects:
                x1, y1, x2, y2 = [int(v) for v in track.bbox]
                h, w = raw_frame.shape[:2]
                x1 = max(0, min(w - 1, x1))
                y1 = max(0, min(h - 1, y1))
                x2 = max(0, min(w, x2))
                y2 = max(0, min(h, y2))
                
                truck_crop = raw_frame[y1:y2, x1:x2] if (x2 > x1 and y2 > y1) else None

                # Branch A: Speed Detection & Overspeed Check
                speed_kmh, is_overspeed = self.speed_estimator.estimate_speed(track)

                # Branch B: License Plate OCR, Blocklist Check & FC Verification
                gt_plate = getattr(track, 'ground_truth_plate', None) if self.active_source == 'SIMULATED' else None
                needs_plate = (track.license_plate is None) or (track.license_plate in ['SCANNING...', 'UNKNOWN', 'UNREADABLE']) or (getattr(track, 'is_fallback_plate', False) and track.hits % 3 == 0)
                if needs_plate:
                    v_path = self.video_file_path if self.active_source == 'VIDEO_FILE' else None
                    plate, conf, is_real, _ = self.plate_ocr.extract_plate(
                        raw_frame, track.bbox, track.track_id, video_path=v_path, ground_truth_plate=gt_plate
                    )
                    
                    if is_real or track.license_plate is None or track.license_plate == 'SCANNING...':
                        track.license_plate = plate
                        track.plate_confidence = conf
                        track.is_fallback_plate = not is_real
                        
                        # Check database blocklist (uses in-memory cache first, falls back to lazy DB)
                        is_blocked, reason, severity = self.plate_ocr.check_blocklist(
                            plate, 
                            get_db() if plate.replace(' ', '').upper() not in self.plate_ocr.blocklist_mem_cache else None, 
                            Blocklist
                        )
                        track.is_blocklisted = is_blocked
                        track.blocklist_reason = reason
                        track.blocklist_severity = severity or 'CRITICAL'

                        # Verify Vehicle Fitness Certificate (FC) & Police Action (uses in-memory cache first)
                        fc_info = fc_service.verify_fc_status(
                            plate, 
                            db_session=get_db() if plate.replace(' ', '').upper() not in fc_service.fc_cache else None
                        )
                        track.fc_status = fc_info.get('fc_status', 'VALID')
                        track.vehicle_age_years = fc_info.get('vehicle_age_years', 4)
                        track.police_action_required = fc_info.get('police_action_required', 'NONE')
                        track.police_notice_number = fc_info.get('police_notice_number', None)
                        track.fc_fine_amount = fc_info.get('fine_amount', 0.0)
                        fc_exp_iso = fc_info.get('fc_expiry_date')
                        track.fc_expiry_date = datetime.fromisoformat(fc_exp_iso) if fc_exp_iso else None

                        # If previously logged with a fallback plate, sync real plate to database
                        if is_real and getattr(track, 'logged_to_db', False):
                            try:
                                from backend.database.models import TruckLog
                                active_db = get_db()
                                existing_log = active_db.query(TruckLog).filter(
                                    TruckLog.track_id == track.track_id
                                ).order_by(TruckLog.arrival_time.desc()).first()
                                if existing_log:
                                    existing_log.license_plate = plate
                                    existing_log.fc_status = track.fc_status
                                    existing_log.vehicle_age_years = track.vehicle_age_years
                                    existing_log.police_action_required = track.police_action_required
                                    existing_log.police_notice_number = track.police_notice_number
                                    existing_log.fc_fine_amount = track.fc_fine_amount
                                    active_db.commit()
                            except Exception as sync_err:
                                print(f"⚠️ Plate DB sync notice: {sync_err}")

                # Branch C: MTL-ViT Classification (Type, Color, Cargo)
                if track.truck_type is None:
                    vit_res = self.vit_classifier.classify(
                        truck_crop, 
                        track_id=track.track_id,
                        class_id=getattr(track, 'class_id', 7),
                        vehicle_label=getattr(track, 'label', 'truck')
                    )
                    track.truck_type = vit_res['truck_type']
                    track.color = vit_res['color']
                    track.cargo_attributes = vit_res['cargo_attributes']

                # Trigger Alerts & Record Event when truck is confirmed (hits >= 4)
                if track.hits >= 4 and not getattr(track, 'logged_to_db', False):
                    track.logged_to_db = True
                    
                    # Capture & Save CCTV Snapshot Image
                    snapshot_filename = None
                    try:
                        ts_str = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
                        clean_pl = (track.license_plate or 'NOPLATE').replace(' ', '')
                        base_name = f"live_{track.track_id}_{clean_pl}_{ts_str}"
                        snapshot_filename = f"{base_name}.jpg"
                        snap_path = os.path.join(Config.SNAPSHOT_DIR, snapshot_filename)
                        
                        # Save CCTV frame with BBox overlay
                        snap_frame = raw_frame.copy()
                        cv2.rectangle(snap_frame, (x1, y1), (x2, y2), (0, 242, 254), 2)
                        cv2.putText(snap_frame, f"{track.track_id} | {track.license_plate} | {speed_kmh} km/h", (x1, max(20, y1 - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 242, 254), 2)
                        cv2.imwrite(snap_path, snap_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
                        
                        # Also save plate crop if available
                        _, _, _, plate_crop = self.plate_ocr.extract_plate(raw_frame, track.bbox, track.track_id)
                        if plate_crop is not None:
                            plate_snap_path = os.path.join(Config.SNAPSHOT_DIR, f"{base_name}_plate.jpg")
                            cv2.imwrite(plate_snap_path, plate_crop, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
                    except Exception as snap_err:
                        print(f"⚠️ Error saving snapshot: {snap_err}")

                    # 1. Alert Manager Dispatch: Overspeed Alert
                    if is_overspeed:
                        alert_manager.trigger_alert(
                            alert_type='OVERSPEED',
                            track_id=track.track_id,
                            license_plate=track.license_plate,
                            speed=speed_kmh,
                            message=f"Overspeed Violation: {track.track_id} ({track.license_plate}) recorded at {speed_kmh} km/h (Limit: {self.speed_estimator.speed_limit} km/h).",
                            severity='HIGH' if speed_kmh > (self.speed_estimator.speed_limit + 15) else 'MEDIUM',
                            db_session=get_db()
                        )
                        
                    # 2. Alert Manager Dispatch: Blocklist / Watchlist Alert
                    if track.is_blocklisted:
                        alert_manager.trigger_alert(
                            alert_type='BLOCKLIST_MATCH',
                            track_id=track.track_id,
                            license_plate=track.license_plate,
                            speed=speed_kmh,
                            message=f"WATCHLIST DETECTED: {track.license_plate} [{track.blocklist_reason}]",
                            severity=track.blocklist_severity or 'CRITICAL',
                            db_session=get_db()
                        )

                    # 3. Alert Manager Dispatch: Police Destruction / FC Expired Alert
                    police_act = getattr(track, 'police_action_required', 'NONE')
                    veh_age = getattr(track, 'vehicle_age_years', 4)
                    notice_no = getattr(track, 'police_notice_number', '')

                    if police_act == 'DESTROY_VEHICLE_SCRAP':
                        alert_manager.trigger_alert(
                            alert_type='FC_SCRAP_DESTROY',
                            track_id=track.track_id,
                            license_plate=track.license_plate,
                            speed=speed_kmh,
                            message=f"POLICE DESTRUCTION ORDER: Vehicle {track.license_plate} is {veh_age} yrs old with expired FC. Immediate impoundment & RVSF scrapping ordered (Notice #{notice_no}).",
                            severity='CRITICAL',
                            db_session=get_db()
                        )
                    elif police_act == 'FC_RENEWAL_PROCESS':
                        alert_manager.trigger_alert(
                            alert_type='FC_EXPIRED_RENEWAL',
                            track_id=track.track_id,
                            license_plate=track.license_plate,
                            speed=speed_kmh,
                            message=f"FC EXPIRED: Vehicle {track.license_plate} (Age: {veh_age} yrs) operating without valid FC. Mandatory FC renewal & fine ₹5,000 required (Challan #{notice_no}).",
                            severity='HIGH',
                            db_session=get_db()
                        )
                        
                    # 4. Logistics & Cargo Event: Arrival & Visit Counting with FC details
                    logistics_service.record_truck_event(
                        track_id=track.track_id,
                        license_plate=track.license_plate,
                        speed=speed_kmh,
                        speed_limit=self.speed_estimator.speed_limit,
                        is_overspeed=is_overspeed,
                        truck_type=track.truck_type,
                        color=track.color,
                        cargo_attributes=track.cargo_attributes,
                        camera_id='CAM-HIGHWAY-01',
                        snapshot_path=snapshot_filename,
                        fc_status=getattr(track, 'fc_status', 'VALID'),
                        fc_expiry_date=getattr(track, 'fc_expiry_date', None),
                        vehicle_age_years=veh_age,
                        police_action_required=police_act,
                        police_notice_number=notice_no,
                        fc_fine_amount=getattr(track, 'fc_fine_amount', 0.0),
                        db_session=get_db()
                    )

                # Collect Telemetry Data
                current_active.append({
                    'track_id': track.track_id,
                    'bbox': [x1, y1, x2, y2],
                    'speed': speed_kmh,
                    'is_overspeed': is_overspeed,
                    'license_plate': track.license_plate,
                    'is_blocklisted': track.is_blocklisted,
                    'truck_type': track.truck_type,
                    'color': track.color,
                    'cargo_attributes': track.cargo_attributes,
                    'fc_status': getattr(track, 'fc_status', 'VALID'),
                    'vehicle_age_years': getattr(track, 'vehicle_age_years', 4),
                    'police_action_required': getattr(track, 'police_action_required', 'NONE'),
                    'police_notice_number': getattr(track, 'police_notice_number', None),
                    'fc_fine_amount': getattr(track, 'fc_fine_amount', 0.0),
                    'age': track.age
                })

        except Exception as e:
            print(f"❌ Error in frame analysis loop: {e}")
        finally:
            if db_session is not None:
                try:
                    db_session.close()
                except Exception:
                    pass

        # 5. Draw Cyber AI HUD Overlays on Frame
        annotated_frame = self._render_ai_hud(raw_frame, tracked_objects)

        # FPS calculation
        now = time.time()
        dt = now - self.last_frame_time
        if dt > 0:
            self.fps_stat = 0.9 * self.fps_stat + 0.1 * (1.0 / dt)
        self.last_frame_time = now

        with self.lock:
            self.current_frame = annotated_frame
            self.active_tracks_data = current_active

        return annotated_frame

    def _render_ai_hud(self, frame, tracks):
        """
        Draws high-tech cyber-surveillance AI HUD overlays:
        - Bounding boxes (Neon Green / Amber Overspeed / Red Blocklist / Dark Red Destroy)
        - Track ID badge
        - Speed speedometer badge
        - License plate badge with flag
        - Fitness Certificate (FC) Compliance & Police Enforcement Badge
        - MTL-ViT multi-task tags (Type / Color / Cargo)
        - Trajectory path breadcrumbs
        """
        if frame is None or getattr(frame, 'size', 0) == 0:
            frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        hud = frame.copy()
        
        for track in tracks:
            x1, y1, x2, y2 = [int(v) for v in track.bbox]
            is_over = getattr(track, 'is_overspeed', False)
            is_blocked = getattr(track, 'is_blocklisted', False)
            p_action = getattr(track, 'police_action_required', 'NONE')
            fc_stat = getattr(track, 'fc_status', 'VALID')
            
            # Box Color Palette
            if p_action == 'DESTROY_VEHICLE_SCRAP':
                box_color = (0, 0, 255)       # Flashing Red (Police Destruction Order)
            elif is_blocked:
                box_color = (0, 0, 255)       # Neon Red (Blocklisted)
            elif p_action == 'FC_RENEWAL_PROCESS':
                box_color = (0, 165, 255)     # Amber (FC Renewal Required)
            elif is_over:
                box_color = (0, 140, 255)     # Neon Amber (Overspeeding)
            else:
                box_color = (0, 242, 254)     # Neon Cyan (Normal)

            # 1. Trajectory Breadcrumbs
            if self.show_trajectories and len(track.history) > 1:
                pts = [(int(p[0]), int(p[1])) for p in list(track.history)]
                for i in range(1, len(pts)):
                    alpha = i / len(pts)
                    thickness = max(1, int(3 * alpha))
                    cv2.line(hud, pts[i-1], pts[i], box_color, thickness)

            # 2. Main Bounding Box with Corner Accents
            if self.show_bboxes:
                # Box outline
                cv2.rectangle(hud, (x1, y1), (x2, y2), box_color, 2)
                
                # Tech Corner Brackets
                c_len = min(20, (x2 - x1) // 4)
                # Top-Left
                cv2.line(hud, (x1, y1), (x1 + c_len, y1), (255, 255, 255), 3)
                cv2.line(hud, (x1, y1), (x1, y1 + c_len), (255, 255, 255), 3)
                # Top-Right
                cv2.line(hud, (x2, y1), (x2 - c_len, y1), (255, 255, 255), 3)
                cv2.line(hud, (x2, y1), (x2, y1 + c_len), (255, 255, 255), 3)
                # Bottom-Left
                cv2.line(hud, (x1, y2), (x1 + c_len, y2), (255, 255, 255), 3)
                cv2.line(hud, (x1, y2), (x1, y2 - c_len), (255, 255, 255), 3)
                # Bottom-Right
                cv2.line(hud, (x2, y2), (x2 - c_len, y2), (255, 255, 255), 3)
                cv2.line(hud, (x2, y2), (x2, y2 - c_len), (255, 255, 255), 3)

            # 3. Track ID Header Badge
            header_y = max(24, y1 - 8)
            v_type_lbl = (getattr(track, 'label', None) or getattr(track, 'truck_type', None) or 'VEHICLE').upper()
            track_label = f"[{track.track_id}] YOLO {v_type_lbl}"
            (tw, th), _ = cv2.getTextSize(track_label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
            cv2.rectangle(hud, (x1, header_y - th - 6), (x1 + tw + 10, header_y + 4), (15, 23, 42), -1)
            cv2.rectangle(hud, (x1, header_y - th - 6), (x1 + tw + 10, header_y + 4), box_color, 1)
            cv2.putText(hud, track_label, (x1 + 5, header_y - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)

            # 4. Speed, Plate & FC Overlay Badge
            tag_y = y2 + 18
            speed_val = getattr(track, 'speed_kmh', 50.0)
            plate_val = getattr(track, 'license_plate', 'SEARCHING...')
            
            speed_str = f"SPEED: {speed_val} km/h"
            if is_over:
                speed_str += " ⚠️ OVERSPEED"
                
            plate_str = f"PLATE: {plate_val}"
            if is_blocked:
                plate_str += " 🚨 BLOCKED"

            # FC Status text
            if p_action == 'DESTROY_VEHICLE_SCRAP':
                fc_badge_str = "FC: EXPIRED 🚨 POLICE: DESTROY/SCRAP"
                fc_color = (0, 0, 255)
            elif p_action == 'FC_RENEWAL_PROCESS':
                fc_badge_str = "FC: EXPIRED ⚠️ RENEWAL REQ (₹5K FINE)"
                fc_color = (0, 165, 255)
            else:
                fc_badge_str = "FC: VALID (COMPLIANT)"
                fc_color = (0, 240, 100)

            # Draw Badge Container (height expanded for FC badge)
            badge_h = 52 if not self.show_vit else 68
            cv2.rectangle(hud, (x1, y2 + 4), (x2 + 35, y2 + 4 + badge_h), (10, 15, 26), -1)
            cv2.rectangle(hud, (x1, y2 + 4), (x2 + 35, y2 + 4 + badge_h), box_color, 1)
            
            # Speed text
            s_color = (0, 0, 255) if is_over else (0, 240, 100)
            cv2.putText(hud, speed_str, (x1 + 6, y2 + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.40, s_color, 1)
            
            # Plate text
            p_color = (0, 0, 255) if is_blocked else (0, 242, 254)
            cv2.putText(hud, plate_str, (x1 + 6, y2 + 32), cv2.FONT_HERSHEY_SIMPLEX, 0.40, p_color, 1)

            # FC Status text
            cv2.putText(hud, fc_badge_str, (x1 + 6, y2 + 46), cv2.FONT_HERSHEY_SIMPLEX, 0.38, fc_color, 1)

            # 5. MTL-ViT Classification Attributes (Type | Color | Cargo)
            if self.show_vit:
                t_type = getattr(track, 'truck_type', 'Container Carrier')
                t_cargo = getattr(track, 'cargo_attributes', 'Sealed ISO')
                vit_str = f"ViT: {t_type[:16]} | {t_cargo[:14]}"
                cv2.putText(hud, vit_str, (x1 + 6, y2 + 60), cv2.FONT_HERSHEY_SIMPLEX, 0.36, (200, 220, 240), 1)


        # 6. Global HUD Telemetry Header
        cv2.rectangle(hud, (0, hud.shape[0] - 28), (hud.shape[1], hud.shape[0]), (10, 15, 26), -1)
        cv2.line(hud, (0, hud.shape[0] - 28), (hud.shape[1], hud.shape[0] - 28), (0, 242, 254), 1)
        
        telemetry_text = f"FPS: {self.fps_stat:.1f} | TRACKED TRUCKS: {len(tracks)} | SPEED LIMIT: {self.speed_estimator.speed_limit:.0f} km/h | PIPELINE: YOLOv26 + ByteTrack + ALPR Deep OCR + MTL-ViT"
        cv2.putText(hud, telemetry_text, (20, hud.shape[0] - 9), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 242, 254), 1)

        return hud

    def generate_mjpeg_stream(self):
        """
        High-performance non-blocking MJPEG broadcast generator.
        Yields pre-encoded JPEG frames from the dedicated background worker.
        Zero redundant inference, zero CPU spikes, supporting unlimited concurrent stream views.
        """
        last_yielded = None
        while self.is_running:
            try:
                with self.frame_condition:
                    if self.latest_jpeg_bytes is None or self.latest_jpeg_bytes == last_yielded:
                        self.frame_condition.wait(timeout=0.08)
                    frame_bytes = self.latest_jpeg_bytes

                if frame_bytes and frame_bytes != last_yielded:
                    last_yielded = frame_bytes
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                else:
                    time.sleep(0.01)
            except Exception:
                time.sleep(0.02)

pipeline_manager = PipelineManager()

