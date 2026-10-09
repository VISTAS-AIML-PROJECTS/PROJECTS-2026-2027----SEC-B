import os
from flask import Blueprint, Response, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from backend.ai_engine.pipeline_manager import pipeline_manager
from backend.config import Config

stream_bp = Blueprint('stream_bp', __name__)

@stream_bp.route('/video_feed', methods=['GET'])
def video_feed():
    """
    MJPEG Live Video Stream with AI HUD overlays.
    """
    return Response(
        pipeline_manager.generate_mjpeg_stream(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@stream_bp.route('/video_file/<path:filename>', methods=['GET'])
def get_video_file(filename):
    """
    Serves uploaded raw video files for HTML5 video player previews with HTTP Range support.
    """
    clean_name = secure_filename(os.path.basename(filename))
    return send_from_directory(Config.UPLOAD_DIR, clean_name, conditional=True)

@stream_bp.route('/telemetry', methods=['GET'])
def get_telemetry():
    """
    Returns real-time active tracks and system metrics without lock contention.
    """
    tracks_copy = list(getattr(pipeline_manager, 'active_tracks_data', []))
    data = {
        'fps': round(getattr(pipeline_manager, 'fps_stat', 30.0), 1),
        'active_source': getattr(pipeline_manager, 'active_source', 'SIMULATED'),
        'speed_limit': getattr(pipeline_manager.speed_estimator, 'speed_limit', 60.0),
        'active_tracks': tracks_copy,
        'track_count': len(tracks_copy),
        'overlays': {
            'bboxes': getattr(pipeline_manager, 'show_bboxes', True),
            'speed': getattr(pipeline_manager, 'show_speed', True),
            'plates': getattr(pipeline_manager, 'show_plates', True),
            'vit': getattr(pipeline_manager, 'show_vit', True),
            'trajectories': getattr(pipeline_manager, 'show_trajectories', True)
        }
    }
    return jsonify(data)

@stream_bp.route('/source', methods=['POST'])
def set_camera_source():
    """
    Switch camera source (SIMULATED, WEBCAM, VIDEO_FILE).
    """
    data = request.json or {}
    source_type = data.get('source', 'SIMULATED').upper()
    video_path = data.get('video_path', None)
    
    pipeline_manager.set_source(source_type, video_path)
    return jsonify({'success': True, 'active_source': pipeline_manager.active_source})

@stream_bp.route('/upload_video', methods=['POST'])
def upload_video():
    """
    Uploads a video file to analyze and switches the live HUD stream to the video file.
    """
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
        
    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400

    os.makedirs(Config.UPLOAD_DIR, exist_ok=True)
    filename = secure_filename(file.filename)
    save_path = os.path.join(Config.UPLOAD_DIR, filename)
    file.save(save_path)
    
    # Switch pipeline source to uploaded video file
    pipeline_manager.set_source('VIDEO_FILE', save_path)
    
    # Read video properties
    import cv2
    cap = cv2.VideoCapture(save_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    duration_sec = round(frame_count / max(1.0, fps), 1) if frame_count > 0 else 0
    cap.release()

    video_url = f"/api/stream/video_file/{filename}"

    return jsonify({
        'success': True,
        'filename': filename,
        'video_url': video_url,
        'source': 'VIDEO_FILE',
        'metadata': {
            'fps': round(fps, 1),
            'frame_count': frame_count,
            'resolution': f"{width}x{height}",
            'duration_seconds': duration_sec
        }
    })

@stream_bp.route('/analyze_video', methods=['POST'])
def analyze_video_batch():
    """
    Performs full automated AI scanning on an uploaded video file.
    Detects all heavy vehicles, computes speed, reads plates, classifies ViT, checks FC compliance,
    and logs all detections into the surveillance database.
    """
    import cv2
    import time
    from datetime import datetime, timezone, timedelta
    from backend.database.db import SessionLocal
    from backend.database.models import TruckLog, AlertLog, Blocklist
    from backend.services.fc_service import fc_service

    save_path = None
    filename = "uploaded_video.mp4"

    if 'video' in request.files:
        file = request.files['video']
        if file.filename != '':
            os.makedirs(Config.UPLOAD_DIR, exist_ok=True)
            filename = secure_filename(file.filename)
            save_path = os.path.join(Config.UPLOAD_DIR, filename)
            file.save(save_path)
    else:
        data = request.json or {}
        req_filename = data.get('filename')
        if req_filename:
            save_path = os.path.join(Config.UPLOAD_DIR, secure_filename(req_filename))
        elif pipeline_manager.video_file_path and os.path.exists(pipeline_manager.video_file_path):
            save_path = pipeline_manager.video_file_path

    if not save_path or not os.path.exists(save_path):
        return jsonify({'error': 'No video file available for analysis'}), 400

    cap = cv2.VideoCapture(save_path)
    if not cap.isOpened():
        return jsonify({'error': 'Could not open video file with OpenCV'}), 400

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    
    detector = pipeline_manager.detector
    tracker = pipeline_manager.tracker
    speed_est = pipeline_manager.speed_estimator
    plate_ocr = pipeline_manager.plate_ocr
    vit_clf = pipeline_manager.vit_classifier

    # Ensure video is pre-scanned for exact ground-truth license plates
    if save_path not in plate_ocr.video_plate_cache:
        plate_ocr.scan_video_plates(save_path)

    db = SessionLocal()
    detected_vehicles = []
    seen_plates = set()
    frame_idx = 0
    step = max(1, int(fps // 5)) # Sample ~5 fps for efficiency

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                break

            if frame_idx % step == 0:
                h, w = frame.shape[:2]
                if w != 1280 or h != 720:
                    scale = min(1280.0 / w, 720.0 / h)
                    nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
                    resized = cv2.resize(frame, (nw, nh), interpolation=cv2.INTER_LINEAR)
                    top = (720 - nh) // 2
                    bottom = 720 - nh - top
                    left = (1280 - nw) // 2
                    right = 1280 - nw - left
                    frame = cv2.copyMakeBorder(resized, top, bottom, left, right, cv2.BORDER_CONSTANT, value=[10, 10, 10])

                dets = detector.detect(frame)
                tracks = tracker.update(dets)

                for trk in tracks:
                    needs_plate = (trk.license_plate is None) or getattr(trk, 'is_fallback_plate', False)
                    if needs_plate:
                        pl, conf, is_real, pl_crop = plate_ocr.extract_plate(frame, trk.bbox, trk.track_id, video_path=save_path)
                        if is_real or trk.license_plate is None:
                            trk.license_plate = pl
                            trk.plate_confidence = conf
                            trk.is_fallback_plate = not is_real

                    speed_kmh, is_over = speed_est.estimate_speed(trk)
                    
                    if trk.truck_type is None:
                        x1, y1, x2, y2 = [int(v) for v in trk.bbox]
                        crop = frame[max(0, y1):min(720, y2), max(0, x1):min(1280, x2)]
                        v_res = vit_clf.classify(
                            crop, 
                            track_id=trk.track_id,
                            class_id=getattr(trk, 'class_id', 7),
                            vehicle_label=getattr(trk, 'label', 'truck')
                        )
                        trk.truck_type = v_res['truck_type']
                        trk.color = v_res['color']
                        trk.cargo_attributes = v_res['cargo_attributes']

                    if trk.license_plate not in seen_plates and trk.hits >= 2:
                        seen_plates.add(trk.license_plate)
                        
                        # Save snapshot
                        ts_str = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
                        snap_name = f"video_analysis_{trk.track_id}_{trk.license_plate}_{ts_str}.jpg"
                        snap_path = os.path.join(Config.SNAPSHOT_DIR, snap_name)
                        
                        annotated = frame.copy()
                        x1, y1, x2, y2 = [int(v) for v in trk.bbox]
                        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 242, 254), 2)
                        cv2.putText(annotated, f"{trk.track_id} | {trk.license_plate} | {speed_kmh} km/h", (x1, max(20, y1 - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 242, 254), 2)
                        cv2.imwrite(snap_path, annotated)

                        plate_snap_name = None
                        if pl_crop is not None and getattr(pl_crop, 'size', 0) > 0:
                            plate_snap_name = f"video_analysis_{trk.track_id}_{trk.license_plate}_{ts_str}_plate.jpg"
                            cv2.imwrite(os.path.join(Config.SNAPSHOT_DIR, plate_snap_name), pl_crop)

                        # FC verification
                        fc_data = fc_service.verify_fc_status(trk.license_plate, db_session=db)
                        is_blocked, b_reason, b_sev = plate_ocr.check_blocklist(trk.license_plate, db, Blocklist)

                        arrival_dt = datetime.now(timezone.utc) - timedelta(seconds=(total_frames - frame_idx) / max(1.0, fps))
                        fc_exp = datetime.fromisoformat(fc_data['fc_expiry_date']) if fc_data.get('fc_expiry_date') else None

                        # Log to database
                        truck_log = TruckLog(
                            track_id=trk.track_id,
                            license_plate=trk.license_plate,
                            speed=speed_kmh,
                            speed_limit=speed_est.speed_limit,
                            is_overspeed=is_over,
                            truck_type=trk.truck_type,
                            color=trk.color,
                            cargo_attributes=trk.cargo_attributes,
                            arrival_time=arrival_dt,
                            visit_count=1,
                            fc_status=fc_data.get('fc_status', 'VALID'),
                            fc_expiry_date=fc_exp,
                            vehicle_age_years=fc_data.get('vehicle_age_years', 4),
                            police_action_required=fc_data.get('police_action_required', 'NONE'),
                            police_notice_number=fc_data.get('police_notice_number'),
                            fc_fine_amount=fc_data.get('fine_amount', 0.0),
                            camera_id='CAM-VIDEO-UPLOAD',
                            snapshot_path=snap_name,
                            created_at=arrival_dt
                        )
                        db.add(truck_log)

                        # Create alert if needed
                        if is_over:
                            db.add(AlertLog(
                                timestamp=arrival_dt,
                                alert_type='OVERSPEED',
                                severity='HIGH' if speed_kmh > speed_est.speed_limit + 15 else 'MEDIUM',
                                track_id=trk.track_id,
                                license_plate=trk.license_plate,
                                speed=speed_kmh,
                                message=f"Video Analysis: Overspeed violation {speed_kmh} km/h (Limit: {speed_est.speed_limit} km/h)",
                                created_at=arrival_dt
                            ))
                        if fc_data.get('police_action_required') == 'DESTROY_VEHICLE_SCRAP':
                            db.add(AlertLog(
                                timestamp=arrival_dt,
                                alert_type='FC_SCRAP_DESTROY',
                                severity='CRITICAL',
                                track_id=trk.track_id,
                                license_plate=trk.license_plate,
                                message=f"Video Analysis: Police Destruction Order - {trk.license_plate} (Age: {fc_data.get('vehicle_age_years')} yrs)",
                                created_at=arrival_dt
                            ))

                        detected_vehicles.append({
                            'track_id': trk.track_id,
                            'license_plate': trk.license_plate,
                            'speed': speed_kmh,
                            'is_overspeed': is_over,
                            'truck_type': trk.truck_type,
                            'color': trk.color,
                            'cargo_attributes': trk.cargo_attributes,
                            'fc_status': fc_data.get('fc_status', 'VALID'),
                            'police_action_required': fc_data.get('police_action_required', 'NONE'),
                            'vehicle_age_years': fc_data.get('vehicle_age_years', 4),
                            'snapshot_url': f"/api/trucks/snapshots/{snap_name}",
                            'plate_crop_url': f"/api/trucks/snapshots/{plate_snap_name}" if plate_snap_name else None,
                            'frame_timestamp': f"{(frame_idx / max(1.0, fps)):.1f}s"
                        })

            frame_idx += 1
        
        db.commit()
    finally:
        cap.release()
        db.close()

    # Also switch the live HUD stream to this video
    pipeline_manager.set_source('VIDEO_FILE', save_path)

    return jsonify({
        'success': True,
        'filename': filename,
        'summary': {
            'total_frames_processed': frame_idx,
            'duration_seconds': round(frame_idx / max(1.0, fps), 1),
            'unique_vehicles_detected': len(detected_vehicles),
            'overspeed_violations': sum(1 for v in detected_vehicles if v['is_overspeed']),
            'fc_scrap_orders': sum(1 for v in detected_vehicles if v['police_action_required'] == 'DESTROY_VEHICLE_SCRAP'),
            'fc_renewals_required': sum(1 for v in detected_vehicles if v['police_action_required'] == 'FC_RENEWAL_PROCESS')
        },
        'detected_vehicles': detected_vehicles
    })

@stream_bp.route('/overlays', methods=['POST'])
def toggle_overlays():
    """
    Toggles AI HUD display layers.
    """
    data = request.json or {}
    if 'bboxes' in data:
        pipeline_manager.show_bboxes = bool(data['bboxes'])
    if 'speed' in data:
        pipeline_manager.show_speed = bool(data['speed'])
    if 'plates' in data:
        pipeline_manager.show_plates = bool(data['plates'])
    if 'vit' in data:
        pipeline_manager.show_vit = bool(data['vit'])
    if 'trajectories' in data:
        pipeline_manager.show_trajectories = bool(data['trajectories'])
        
    return jsonify({
        'success': True,
        'overlays': {
            'bboxes': pipeline_manager.show_bboxes,
            'speed': pipeline_manager.show_speed,
            'plates': pipeline_manager.show_plates,
            'vit': pipeline_manager.show_vit,
            'trajectories': pipeline_manager.show_trajectories
        }
    })

