"""
routes/ecopoints.py

GET  /api/ecopoints              — current user summary
POST /api/ecopoints/events       — record a new eco event
GET  /api/ecopoints/leaderboard  — ranked list from real DB data
GET  /api/ecopoints/rules        — documented point rules
"""
from flask import Blueprint, request, jsonify
from services.eco_points import (
    get_summary, record_event, get_leaderboard, POINT_RULES
)

ecopoints_bp = Blueprint('ecopoints', __name__)


@ecopoints_bp.route('', methods=['GET'])
def summary():
    return jsonify(get_summary())


@ecopoints_bp.route('/events', methods=['POST'])
def add_event():
    data = request.get_json(force=True) or {}

    event_type = str(data.get('event_type', '')).strip()
    if not event_type:
        return jsonify({'error': 'event_type is required.'}), 400

    # Reject any attempt to submit raw point values from the frontend
    if 'points' in data:
        return jsonify({
            'error': 'points cannot be submitted by the client. '
                     'Points are determined by the backend from event_type.'
        }), 400

    metadata = data.get('metadata')
    if metadata is not None and not isinstance(metadata, dict):
        return jsonify({'error': 'metadata must be a JSON object.'}), 400

    result = record_event(event_type=event_type, metadata=metadata)

    if result.get('status') == 'error':
        return jsonify(result), 400

    return jsonify(result)


@ecopoints_bp.route('/leaderboard', methods=['GET'])
def leaderboard():
    return jsonify(get_leaderboard())


@ecopoints_bp.route('/rules', methods=['GET'])
def rules():
    """Return the documented point rules so the frontend can display them."""
    return jsonify({
        'rules': [
            {'event_type': k, 'points': v}
            for k, v in sorted(POINT_RULES.items())
        ],
        'note': (
            'Points are determined by the backend. '
            'The frontend cannot submit arbitrary point values.'
        ),
    })
