from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from sqlalchemy import desc
from backend.database.db import SessionLocal
from backend.database.models import Blocklist

blocklist_bp = Blueprint('blocklist_bp', __name__)

@blocklist_bp.route('', methods=['GET'])
def get_blocklist():
    """
    Get all active and inactive blocklist entries.
    """
    db = SessionLocal()
    try:
        search = request.args.get('search', '').strip()
        query = db.query(Blocklist)
        if search:
            query = query.filter(Blocklist.license_plate.ilike(f"%{search}%"))

        entries = query.order_by(desc(Blocklist.date_added)).all()
        return jsonify({'blocklist': [b.to_dict() for b in entries]})
    finally:
        db.close()


@blocklist_bp.route('', methods=['POST'])
def add_to_blocklist():
    """
    Add a new vehicle license plate to the security blocklist.
    """
    data = request.json or {}
    plate = data.get('license_plate', '').strip().upper()
    reason = data.get('reason', '').strip()
    severity = data.get('severity', 'CRITICAL').strip().upper()
    added_by = data.get('added_by', 'Security Supervisor').strip()

    if not plate or not reason:
        return jsonify({'error': 'license_plate and reason are required'}), 400

    db = SessionLocal()
    try:
        # Check if plate already exists
        existing = db.query(Blocklist).filter(Blocklist.license_plate == plate).first()
        if existing:
            existing.active = True
            existing.reason = reason
            existing.severity = severity
            existing.date_added = datetime.now(timezone.utc)
            db.commit()
            return jsonify({'success': True, 'entry': existing.to_dict(), 'updated': True})

        new_entry = Blocklist(
            license_plate=plate,
            reason=reason,
            severity=severity,
            added_by=added_by,
            date_added=datetime.now(timezone.utc),
            active=True
        )
        db.add(new_entry)
        db.commit()
        return jsonify({'success': True, 'entry': new_entry.to_dict()}), 201
    finally:
        db.close()


@blocklist_bp.route('/<int:entry_id>', methods=['PUT'])
def update_blocklist_entry(entry_id):
    """
    Update details or toggle active status of a blocklist entry.
    """
    data = request.json or {}
    db = SessionLocal()
    try:
        entry = db.query(Blocklist).filter(Blocklist.id == entry_id).first()
        if not entry:
            return jsonify({'error': 'Blocklist entry not found'}), 404

        if 'reason' in data:
            entry.reason = data['reason']
        if 'severity' in data:
            entry.severity = data['severity'].upper()
        if 'active' in data:
            entry.active = bool(data['active'])

        db.commit()
        return jsonify({'success': True, 'entry': entry.to_dict()})
    finally:
        db.close()


@blocklist_bp.route('/<int:entry_id>', methods=['DELETE'])
def delete_blocklist_entry(entry_id):
    """
    Delete entry or deactivate it.
    """
    db = SessionLocal()
    try:
        entry = db.query(Blocklist).filter(Blocklist.id == entry_id).first()
        if not entry:
            return jsonify({'error': 'Blocklist entry not found'}), 404

        db.delete(entry)
        db.commit()
        return jsonify({'success': True, 'message': 'Entry deleted from blocklist'})
    finally:
        db.close()
