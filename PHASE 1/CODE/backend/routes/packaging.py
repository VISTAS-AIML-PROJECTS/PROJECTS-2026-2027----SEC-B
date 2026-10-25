from flask import Blueprint, request, jsonify
from services.packaging_recommender import recommend_packaging
from services.dashboard import record_recommendation

packaging_bp = Blueprint('packaging', __name__)


@packaging_bp.route('/recommend', methods=['POST'])
def recommend():
    data = request.get_json(force=True)

    try:
        product_l = float(data['product_length'])
        product_w = float(data['product_width'])
        product_h = float(data['product_height'])
    except (KeyError, TypeError, ValueError) as e:
        return jsonify({'error': f'Invalid dimensions: {e}'}), 400

    is_fragile        = bool(data.get('is_fragile', False))
    clearance         = float(data.get('clearance_fraction', 0.10))
    top_n             = int(data.get('top_n', 10))

    result = recommend_packaging(
        product_l=product_l,
        product_w=product_w,
        product_h=product_h,
        is_fragile=is_fragile,
        clearance_fraction=clearance,
        top_n=top_n,
    )

    top_sku = None
    if result['recommendations']:
        top_sku = result['recommendations'][0].get('sku')

    record_recommendation(
        product_l, product_w, product_h, is_fragile,
        result['status'], result['meta']['totalPhysicalFits'], top_sku
    )

    return jsonify(result)
