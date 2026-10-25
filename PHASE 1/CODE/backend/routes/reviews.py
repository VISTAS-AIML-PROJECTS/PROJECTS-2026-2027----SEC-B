from flask import Blueprint, request, jsonify
from services.review_analyzer import analyze_reviews
from services.dashboard import record_review_analysis

reviews_bp = Blueprint('reviews', __name__)


@reviews_bp.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json(force=True)
    text = data.get('text', '').strip()

    if not text:
        return jsonify({'error': 'No review text provided.'}), 400

    result = analyze_reviews(text)

    if result.get('status') == 'OK':
        s = result.get('sentiment', {})
        record_review_analysis(
            result.get('reviews_analyzed', 0),
            s.get('positive', 0),
            s.get('negative', 0),
            s.get('neutral', 0),
        )

    return jsonify(result)
