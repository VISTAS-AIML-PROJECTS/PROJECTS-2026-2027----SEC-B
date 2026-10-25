from flask import Blueprint, request, jsonify
from services.material_classifier import classify_material
from services.product_detector import detect_products
from services.product_catalog import get_representative_product
from services.packaging_recommender import recommend_packaging
from services.dashboard import record_material_classification

vision_bp = Blueprint('vision', __name__)

# YOLO class_name → ABO product_type mapping
COCO_TO_ABO = {
    'backpack':   'BACKPACK',
    'book':       'BOOK',
    'bottle':     'BOTTLE',
    'cell_phone': 'CELLULAR_PHONE',
    'cup':        'DRINKING_CUP',
    'handbag':    'HANDBAG',
    'keyboard':   'KEYBOARD',
    'laptop':     'LAPTOP',
    'mouse':      'MOUSE',
    'remote':     'REMOTE_CONTROL',
    'scissors':   'SCISSORS',
    'teddy_bear': 'TOY',
    'vase':       'VASE',
    'clock':      'CLOCK',
    'chair':      'CHAIR',
}


@vision_bp.route('/material', methods=['POST'])
def classify():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided.'}), 400

    image_bytes = request.files['image'].read()
    if not image_bytes:
        return jsonify({'error': 'Empty image file.'}), 400

    try:
        result = classify_material(image_bytes)
        record_material_classification(
            result.get('predicted_class', 'unknown'),
            result.get('confidence', 0.0)
        )
        return jsonify(result)
    except FileNotFoundError as e:
        return jsonify({'error': str(e), 'status': 'MODEL_NOT_FOUND'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@vision_bp.route('/analyze', methods=['POST'])
def analyze():
    """
    Full vision pipeline:
    1. YOLO11s product detection
    2. ABO product lookup (category-level, not exact SKU)
    3. MobileNetV2 material classification
    4. Packaging recommendation (Packrift catalog, 10% clearance)

    Accepts optional query param ?detection_index=N to select which
    YOLO detection to use for ABO lookup (default: 0, highest confidence).
    """
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided.'}), 400

    image_bytes = request.files['image'].read()
    if not image_bytes:
        return jsonify({'error': 'Empty image file.'}), 400

    # Step 1: YOLO product detection
    detection_result = detect_products(image_bytes)

    if detection_result['status'] in ('MODEL_NOT_INSTALLED', 'INVALID_IMAGE'):
        status_code = 503 if detection_result['status'] == 'MODEL_NOT_INSTALLED' else 400
        return jsonify({
            'success': False,
            'status': 'PRODUCT_DETECTOR_UNAVAILABLE'
                      if detection_result['status'] == 'MODEL_NOT_INSTALLED'
                      else detection_result['status'],
            'error': detection_result['error'],
            'detections': [],
            'selected_detection': None,
            'product': None,
            'material': None,
            'packaging': None,
        }), status_code

    detections = detection_result.get('detections', [])
    if not detections:
        return jsonify({
            'success': True,
            'status': 'NO_PRODUCT_DETECTED',
            'detections': [],
            'selected_detection': None,
            'product': None,
            'material': None,
            'packaging': None,
        })

    # Allow caller to select a specific detection by index
    try:
        det_idx = int(request.args.get('detection_index', 0))
        det_idx = max(0, min(det_idx, len(detections) - 1))
    except (TypeError, ValueError):
        det_idx = 0

    selected = detections[det_idx]
    detected_class = selected['class_name']

    # Step 2: ABO product lookup (category → representative product)
    abo_type = COCO_TO_ABO.get(detected_class)
    product_info = None
    if abo_type:
        raw = get_representative_product(abo_type)
        if raw:
            product_info = {
                'source': 'ABO',
                'detected_category': detected_class,
                'abo_product_type': abo_type,
                'item_id': raw.get('item_id'),
                'item_name': raw.get('item_name'),
                'dimensions': {
                    'length_in': raw.get('length_in'),
                    'width_in': raw.get('width_in'),
                    'height_in': raw.get('height_in'),
                },
                'weight': raw.get('weight'),
                'weight_unit': raw.get('weight_unit'),
                'catalog_candidates': raw.get('catalog_candidates'),
                'note': (
                    'Median-volume representative from ABO catalog. '
                    'YOLO detects product category, not exact SKU.'
                ),
            }

    if abo_type and product_info is None:
        product_info = {'status': 'ABO_PRODUCT_NOT_FOUND', 'detected_category': detected_class}

    # Step 3: Material classification
    try:
        material_result = classify_material(image_bytes)
        record_material_classification(
            material_result.get('predicted_class', 'unknown'),
            material_result.get('confidence', 0.0)
        )
    except Exception as e:
        material_result = {'error': str(e), 'status': 'MATERIAL_MODEL_ERROR'}

    # Step 4: Packaging recommendation
    packaging_result = None
    if product_info and 'dimensions' in product_info:
        dims = product_info['dimensions']
        if all(dims.get(k) for k in ('length_in', 'width_in', 'height_in')):
            packaging_result = recommend_packaging(
                product_l=dims['length_in'],
                product_w=dims['width_in'],
                product_h=dims['height_in'],
                is_fragile=False,
                top_n=5,
            )

    return jsonify({
        'success': True,
        'status': 'OK',
        'detections': detections,
        'selected_detection': selected,
        'product': product_info,
        'material': material_result,
        'packaging': packaging_result,
    })
