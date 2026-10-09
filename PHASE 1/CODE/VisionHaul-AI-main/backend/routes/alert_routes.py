from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from sqlalchemy import desc
from backend.database.db import SessionLocal
from backend.database.models import AlertLog
from backend.services.alert_manager import alert_manager

alert_bp = Blueprint('alert_bp', __name__)

@alert_bp.route('', methods=['GET'])
def get_alerts():
    """
    List alerts with severity filtering and pagination.
    """
    db = SessionLocal()
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        severity = request.args.get('severity', '').strip().upper()
        alert_type = request.args.get('alert_type', '').strip().upper()
        unack_only = request.args.get('unacknowledged', '').lower() == 'true'

        query = db.query(AlertLog)

        if severity:
            query = query.filter(AlertLog.severity == severity)
        if alert_type:
            query = query.filter(AlertLog.alert_type == alert_type)
        if unack_only:
            query = query.filter(AlertLog.acknowledged == False)

        total = query.count()
        alerts = query.order_by(desc(AlertLog.timestamp)).offset((page - 1) * limit).limit(limit).all()

        return jsonify({
            'total': total,
            'page': page,
            'limit': limit,
            'total_pages': (total + limit - 1) // limit,
            'alerts': [a.to_dict() for a in alerts]
        })
    finally:
        db.close()


@alert_bp.route('/recent', methods=['GET'])
def get_recent_alerts():
    """
    Fast lightweight polling endpoint for real-time siren / dashboard notification banners.
    """
    db = SessionLocal()
    try:
        recent = db.query(AlertLog).filter(
            AlertLog.acknowledged == False
        ).order_by(desc(AlertLog.timestamp)).limit(5).all()

        return jsonify({
            'unacknowledged_count': db.query(AlertLog).filter(AlertLog.acknowledged == False).count(),
            'recent_alerts': [a.to_dict() for a in recent]
        })
    finally:
        db.close()


@alert_bp.route('/<int:alert_id>/ack', methods=['POST'])
def acknowledge_alert(alert_id):
    """
    Mark an alert as acknowledged by authorized personnel.
    """
    db = SessionLocal()
    try:
        alert = db.query(AlertLog).filter(AlertLog.id == alert_id).first()
        if not alert:
            return jsonify({'error': 'Alert not found'}), 404

        alert.acknowledged = True
        db.commit()
        return jsonify({'success': True, 'alert': alert.to_dict()})
    finally:
        db.close()


@alert_bp.route('/test-email', methods=['POST'])
def test_email_dispatch():
    """
    Triggers a test email notification to verify SMTP settings.
    """
    data = request.json or {}
    plate = data.get('license_plate', 'TN38AB1234')
    alert_type = data.get('alert_type', 'MANUAL_TEST_ALERT')
    severity = data.get('severity', 'HIGH')

    alert_dict = alert_manager.trigger_alert(
        alert_type=alert_type,
        track_id='TEST_TRK',
        license_plate=plate,
        speed=78.5,
        message=f"Manual Security System Diagnostic Test for Authorized Personnel (Target Plate: {plate}).",
        severity=severity
    )

    return jsonify({
        'success': True,
        'message': 'Test alert dispatched successfully',
        'alert': alert_dict
    })
