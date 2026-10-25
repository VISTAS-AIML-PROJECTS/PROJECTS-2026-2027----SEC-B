from flask import Blueprint, request, jsonify
from services.product_catalog import search_products, get_representative_product

products_bp = Blueprint('products', __name__)


@products_bp.route('/search', methods=['GET'])
def search():
    q    = request.args.get('q', '')
    ptype = request.args.get('type', '')
    limit = min(int(request.args.get('limit', 20)), 100)
    return jsonify(search_products(query=q, product_type=ptype, limit=limit))


@products_bp.route('/lookup', methods=['POST'])
def lookup():
    data = request.get_json(force=True)
    ptype = data.get('product_type', '')
    if not ptype:
        return jsonify({'error': 'product_type is required'}), 400
    result = get_representative_product(ptype)
    if result is None:
        return jsonify({'error': f'No products found for type: {ptype}'}), 404
    return jsonify(result)
