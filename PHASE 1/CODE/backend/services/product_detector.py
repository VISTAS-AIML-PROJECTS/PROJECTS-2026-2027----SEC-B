"""
services/product_detector.py

Wrapture YOLO11s product detector.
Weights: backend/models/yolo/best.pt
Classes: read from model.names (embedded in .pt) or classes.json if present.

Target classes (15):
    laptop, cell_phone, keyboard, mouse, bottle, cup, backpack,
    handbag, book, clock, vase, chair, remote, scissors, teddy_bear

Metrics (held-out test set):
    Precision: 62.20%  Recall: 50.97%
    mAP@50:    54.09%  mAP@50-95: 37.16%
"""
import json
import os
import numpy as np
from PIL import Image
import io

import config

_model = None
_class_names = None
_model_loaded = False
_load_error = None

# Canonical 15-class list (fallback if model.names is unavailable)
_FALLBACK_CLASSES = [
    'laptop', 'cell_phone', 'keyboard', 'mouse', 'bottle',
    'cup', 'backpack', 'handbag', 'book', 'clock',
    'vase', 'chair', 'remote', 'scissors', 'teddy_bear',
]


def _try_load():
    global _model, _class_names, _model_loaded, _load_error

    if not os.path.isfile(config.YOLO_WEIGHTS_PATH):
        _load_error = (
            f"PRODUCT_DETECTOR_UNAVAILABLE: weights not found at "
            f"{config.YOLO_WEIGHTS_PATH}"
        )
        return

    try:
        from ultralytics import YOLO
        _model = YOLO(config.YOLO_WEIGHTS_PATH)

        # Prefer classes.json if present; otherwise read from model.names
        if os.path.isfile(config.YOLO_CLASSES_PATH):
            with open(config.YOLO_CLASSES_PATH, 'r') as f:
                _class_names = json.load(f)
        elif hasattr(_model, 'names') and _model.names:
            names = _model.names
            # model.names is a dict {int: str} in Ultralytics
            _class_names = [names[i] for i in sorted(names.keys())]
        else:
            _class_names = _FALLBACK_CLASSES

        _model_loaded = True
    except Exception as e:
        _load_error = f"PRODUCT_DETECTOR_UNAVAILABLE: failed to load model — {e}"


_try_load()


def detect_products(image_bytes: bytes, confidence_threshold: float = 0.35) -> dict:
    """
    Run YOLO11s inference on image_bytes.
    Returns real detections or a clear error. Never returns fake detections.
    """
    if not _model_loaded:
        return {
            'status': 'MODEL_NOT_INSTALLED',
            'error': _load_error,
            'detections': [],
        }

    try:
        img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    except Exception as e:
        return {
            'status': 'INVALID_IMAGE',
            'error': f'Could not decode image: {e}',
            'detections': [],
        }

    arr = np.array(img)
    results = _model(arr, conf=confidence_threshold, verbose=False)
    detections = []

    for result in results:
        for box in result.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            xyxy = box.xyxy[0].tolist()
            class_name = (
                _class_names[cls_id]
                if cls_id < len(_class_names)
                else str(cls_id)
            )
            detections.append({
                'class_id': cls_id,
                'class_name': class_name,
                'confidence': round(conf, 4),
                'bbox': {
                    'x1': round(xyxy[0], 1),
                    'y1': round(xyxy[1], 1),
                    'x2': round(xyxy[2], 1),
                    'y2': round(xyxy[3], 1),
                },
            })

    detections.sort(key=lambda d: d['confidence'], reverse=True)

    return {
        'status': 'OK',
        'detections': detections,
        'model': 'Wrapture YOLO11s Product Detector',
        'model_classes': len(_class_names),
    }
