"""
routes/sustainability.py

POST /api/sustainability/simulate
GET  /api/sustainability/materials
"""
from flask import Blueprint, request, jsonify
from services.sustainability import simulate, get_catalog_materials

sustainability_bp = Blueprint('sustainability', __name__)


@sustainability_bp.route('/simulate', methods=['POST'])
def simulate_route():
    data = request.get_json(force=True)

    # Validate required dimension inputs
    try:
        length_cm = float(data['length_cm'])
        width_cm  = float(data['width_cm'])
        height_cm = float(data['height_cm'])
    except (KeyError, TypeError, ValueError) as e:
        return jsonify({'error': f'length_cm, width_cm, height_cm are required floats: {e}'}), 400

    if length_cm <= 0 or width_cm <= 0 or height_cm <= 0:
        return jsonify({'error': 'Dimensions must be greater than zero.'}), 400

    try:
        weight_kg = float(data.get('weight_kg', 0) or 0)
    except (TypeError, ValueError):
        return jsonify({'error': 'weight_kg must be a number.'}), 400

    product_type      = str(data.get('product_type', '')).strip()
    packaging_sku     = str(data.get('packaging_sku', '')).strip() or None
    packaging_material = str(data.get('packaging_material', '')).strip() or None

    result = simulate(
        product_type=product_type,
        length_cm=length_cm,
        width_cm=width_cm,
        height_cm=height_cm,
        weight_kg=weight_kg,
        packaging_sku=packaging_sku,
        packaging_material=packaging_material,
    )

    if result.get('status') == 'error':
        return jsonify(result), 404 if 'not found' in result.get('error', '').lower() else 400

    return jsonify(result)


@sustainability_bp.route('/materials', methods=['GET'])
def materials_route():
    """Return the distinct material values present in the catalog calculated dynamically."""
    return jsonify(get_catalog_materials())
