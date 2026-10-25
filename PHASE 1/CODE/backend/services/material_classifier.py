"""
services/material_classifier.py

Loads the real Wrapture MobileNetV2 SavedModel and runs inference.
Classes: cardboard, compost, glass, metal, paper, plastic, trash
Reported accuracy: ~86.98% on unseen test set (645 images).

This is a MATERIAL classifier, not a product detector.
"""
import json
import os
import numpy as np
from PIL import Image
import io

import config

_model = None
_class_names = None


def _load():
    global _model, _class_names
    if _model is not None:
        return

    import tensorflow as tf

    saved_model_dir = os.path.abspath(config.MATERIAL_SAVEDMODEL_DIR)

    if not os.path.isdir(saved_model_dir):
        raise FileNotFoundError(
            f"Material model SavedModel not found at: {saved_model_dir}"
        )

    _model = tf.saved_model.load(saved_model_dir)

    with open(config.MATERIAL_CLASSES_PATH, 'r') as f:
        _class_names = json.load(f)


def classify_material(image_bytes: bytes) -> dict:
    """
    Run the real MobileNetV2 material classifier on image_bytes.
    Returns top prediction and all class probabilities.
    Does NOT invent values.
    """
    _load()

    import tensorflow as tf

    img = Image.open(io.BytesIO(image_bytes)).convert('RGB').resize((224, 224))
    arr = np.array(img, dtype=np.float32)
    arr = np.expand_dims(arr, axis=0)  # (1, 224, 224, 3)

    infer = _model.signatures['serving_default']
    input_key = list(infer.structured_input_signature[1].keys())[0]
    output = infer(**{input_key: tf.constant(arr)})
    output_key = list(output.keys())[0]
    probs = output[output_key].numpy()[0]  # shape (7,)

    top_idx = int(np.argmax(probs))
    results = [
        {'class': _class_names[i], 'confidence': float(probs[i])}
        for i in range(len(_class_names))
    ]
    results.sort(key=lambda x: x['confidence'], reverse=True)

    return {
        'predicted_class': _class_names[top_idx],
        'confidence': float(probs[top_idx]),
        'all_classes': results,
        'model': 'Wrapture MobileNetV2 Material Classifier',
        'model_classes': 7,
        'note': 'Classifies packaging/waste material. Not a product detector.',
    }
