"""
Convert SavedModel to TF.js GraphModel format directly via Python API,
bypassing the CLI and its broken tensorflow_hub import chain.
"""
import sys
import os

# Patch pkg_resources before any tensorflow_hub import
try:
    import pkg_resources
except ModuleNotFoundError:
    import importlib
    import types
    pkg_resources = types.ModuleType('pkg_resources')
    pkg_resources.parse_version = lambda v: tuple(int(x) for x in v.split('.')[:3])
    sys.modules['pkg_resources'] = pkg_resources

import tensorflow as tf
from tensorflowjs.converters import tf_saved_model_conversion_v2

SAVED_MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    'content', 'wrapture_material_model'
)
OUTPUT_PATH = os.path.join(
    os.path.dirname(__file__),
    '..', 'public', 'models', 'wrapture-material'
)

os.makedirs(OUTPUT_PATH, exist_ok=True)

print(f"Converting: {SAVED_MODEL_PATH}")
print(f"Output:     {OUTPUT_PATH}")

tf_saved_model_conversion_v2.convert_tf_saved_model(
    saved_model_dir=SAVED_MODEL_PATH,
    output_dir=OUTPUT_PATH,
    signature_def='serving_default',
    saved_model_tags='serve',
)

print("Conversion complete.")
