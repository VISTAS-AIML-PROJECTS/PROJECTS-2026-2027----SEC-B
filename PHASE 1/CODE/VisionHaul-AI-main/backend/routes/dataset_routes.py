import os
from flask import Blueprint, request, jsonify, send_file
from backend.services.training_service import training_service
from backend.ai_engine.image_dataset_generator import dataset_generator
from backend.database.db import refresh_image_database

dataset_bp = Blueprint('dataset_bp', __name__)

@dataset_bp.route('/gallery', methods=['GET'])
def get_dataset_gallery():
    """
    Returns paginated vehicle snapshot images and dossier metadata.
    """
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 24))
    truck_type = request.args.get('truck_type', '').strip() or None
    search = request.args.get('search', '').strip() or None

    data = training_service.get_gallery_images(page=page, limit=limit, truck_type=truck_type, search=search)
    return jsonify(data)

@dataset_bp.route('/stats', methods=['GET'])
def get_dataset_statistics():
    """
    Returns image dataset summary metrics, class distributions, and disk statistics.
    """
    stats = training_service.get_dataset_stats()
    return jsonify(stats)

@dataset_bp.route('/train', methods=['POST'])
def start_model_training():
    """
    Initiates AI model training / fine-tuning for YOLOv26 or MTL-ViT.
    """
    payload = request.json or {}
    model_type = payload.get('model_type', 'YOLOv26-Truck')
    epochs = int(payload.get('epochs', 25))
    batch_size = int(payload.get('batch_size', 16))
    lr = float(payload.get('learning_rate', 0.001))
    backbone = payload.get('backbone', 'YOLOv26-Nano')

    result = training_service.start_training(
        model_type=model_type,
        epochs=epochs,
        batch_size=batch_size,
        lr=lr,
        backbone=backbone
    )

    if 'error' in result:
        return jsonify(result), 400
    return jsonify(result)

@dataset_bp.route('/training_status', methods=['GET'])
def get_training_status():
    """
    Returns live training telemetry (current epoch, loss curve, mAP@50, logs).
    """
    state = training_service.get_training_state()
    return jsonify(state)

@dataset_bp.route('/export', methods=['GET'])
def export_dataset():
    """
    Exports and downloads the complete annotated YOLO training dataset (.zip).
    """
    try:
        zip_path, zip_filename = training_service.export_dataset_zip()
        return send_file(
            zip_path,
            mimetype='application/zip',
            as_attachment=True,
            download_name=zip_filename
        )
    except Exception as e:
        return jsonify({'error': f'Failed to generate export archive: {str(e)}'}), 500

@dataset_bp.route('/generate_batch', methods=['POST'])
def generate_more_images():
    """
    Generates an additional batch of synthetic CCTV snapshot records.
    """
    payload = request.json or {}
    count = int(payload.get('count', 50))
    count = max(10, min(150, count))

    try:
        refresh_image_database(count=count)
        return jsonify({
            'success': True,
            'message': f'Generated and integrated {count} new image-backed vehicle records into database.',
            'stats': training_service.get_dataset_stats()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
