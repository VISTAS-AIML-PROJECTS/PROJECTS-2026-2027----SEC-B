import os
from dotenv import load_dotenv

load_dotenv()

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, '..', 'public')

PACKAGING_CATALOG_PATH = os.path.join(PUBLIC_DIR, 'data', 'wrapture_packaging_catalog.json')
ABO_CATALOG_PATH       = os.path.join(PUBLIC_DIR, 'wrapture_abo_products.json')
MATERIAL_MODEL_DIR     = os.path.join(PUBLIC_DIR, 'models', 'wrapture-material')
MATERIAL_CLASSES_PATH  = os.path.join(MATERIAL_MODEL_DIR, 'class_names.json')  # class_names.json lives here
MATERIAL_SAVEDMODEL_DIR = os.path.join(BASE_DIR, '..', 'model_conversion', 'content', 'wrapture_material_model')

# YOLO product detector — not yet trained; place best.pt here when ready
YOLO_WEIGHTS_PATH = os.path.join(BASE_DIR, 'models', 'yolo', 'best.pt')
YOLO_CLASSES_PATH = os.path.join(BASE_DIR, 'models', 'yolo', 'classes.json')

# ── LLM ───────────────────────────────────────────────────────────────────────
LLM_PROVIDER  = os.getenv('LLM_PROVIDER', 'openai')   # 'openai' | 'none'
LLM_API_KEY   = os.getenv('LLM_API_KEY', '')
LLM_MODEL     = os.getenv('LLM_MODEL', 'gpt-4o-mini')

# ── Flask ─────────────────────────────────────────────────────────────────────
FLASK_HOST    = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT    = int(os.getenv('FLASK_PORT', 5000))
FLASK_DEBUG   = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'

# ── Google Maps Platform ──────────────────────────────────────────────────────
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY', '')

# ── CORS ──────────────────────────────────────────────────────────────────────
CORS_ORIGINS  = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
