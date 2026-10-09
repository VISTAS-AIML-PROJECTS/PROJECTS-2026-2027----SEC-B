from flask import Blueprint, request, jsonify
from backend.database.db import SessionLocal
from backend.database.models import SystemConfig
from backend.ai_engine.pipeline_manager import pipeline_manager
from backend.config import Config

config_bp = Blueprint('config_bp', __name__)

@config_bp.route('', methods=['GET'])
def get_config():
    """
    Returns system settings.
    """
    db = SessionLocal()
    try:
        configs = db.query(SystemConfig).all()
        config_map = {c.key: c.value for c in configs}
        
        # Ensure default keys
        return jsonify({
            'speed_limit': float(config_map.get('speed_limit', Config.DEFAULT_SPEED_LIMIT)),
            'sound_alert_enabled': config_map.get('sound_alert_enabled', 'true').lower() == 'true',
            'email_alert_enabled': config_map.get('email_alert_enabled', 'true').lower() == 'true',
            'alert_recipient_email': config_map.get('alert_recipient_email', Config.ALERT_EMAIL_RECIPIENT),
            'homography_calibration': float(config_map.get('homography_calibration', Config.PIXELS_PER_METER)),
            'camera_source': pipeline_manager.active_source,
            'fps': Config.FPS
        })
    finally:
        db.close()


@config_bp.route('', methods=['POST'])
def update_config():
    """
    Updates system settings and synchronizes live pipeline.
    """
    data = request.json or {}
    db = SessionLocal()
    try:
        if 'speed_limit' in data:
            val = str(float(data['speed_limit']))
            _set_config_val(db, 'speed_limit', val)
            pipeline_manager.update_speed_limit(float(val))
            
        if 'sound_alert_enabled' in data:
            val = 'true' if data['sound_alert_enabled'] else 'false'
            _set_config_val(db, 'sound_alert_enabled', val)
            Config.SOUND_ALERT_ENABLED = (val == 'true')
            
        if 'email_alert_enabled' in data:
            val = 'true' if data['email_alert_enabled'] else 'false'
            _set_config_val(db, 'email_alert_enabled', val)
            Config.EMAIL_ALERT_ENABLED = (val == 'true')
            
        if 'alert_recipient_email' in data:
            val = str(data['alert_recipient_email']).strip()
            _set_config_val(db, 'alert_recipient_email', val)
            Config.ALERT_EMAIL_RECIPIENT = val
            
        if 'homography_calibration' in data:
            val = str(float(data['homography_calibration']))
            _set_config_val(db, 'homography_calibration', val)
            pipeline_manager.speed_estimator.set_calibration(float(val))

        db.commit()
        return jsonify({'success': True, 'message': 'System configuration updated successfully'})
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        db.close()


def _set_config_val(db, key, value):
    cfg = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if cfg:
        cfg.value = value
    else:
        db.add(SystemConfig(key=key, value=value))
