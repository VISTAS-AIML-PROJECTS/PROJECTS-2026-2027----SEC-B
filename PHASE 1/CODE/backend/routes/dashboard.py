from flask import Blueprint, jsonify
from services.dashboard import get_stats

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/stats', methods=['GET'])
def stats():
    return jsonify(get_stats())
