"""
app.py — Wrapture Flask Backend

Endpoints:
  POST /api/packaging/recommend
  POST /api/vision/material
  POST /api/vision/analyze
  GET  /api/products/search
  POST /api/products/lookup
  POST /api/reviews/analyze
  POST /api/chat
  GET  /api/dashboard/stats
  GET  /api/ecopoints
  POST /api/ecopoints/events
  GET  /api/ecopoints/leaderboard
  GET  /api/ecopoints/rules
  GET  /api/recycling/nearby
  GET  /api/health
  GET  /api/models
"""
import json
import os

from flask import Flask, jsonify
from flask_cors import CORS

import config
from services.dashboard import init_db
from services.eco_points import init_eco_db
from routes.packaging import packaging_bp
from routes.vision import vision_bp
from routes.products import products_bp
from routes.reviews import reviews_bp
from routes.chatbot import chatbot_bp
from routes.dashboard import dashboard_bp
from routes.sustainability import sustainability_bp
from routes.ecopoints import ecopoints_bp
from routes.recycling import recycling_bp

app = Flask(__name__)
CORS(app, origins=config.CORS_ORIGINS)

# Initialise SQLite database tables
init_db()
init_eco_db()

# Register blueprints
app.register_blueprint(packaging_bp,      url_prefix='/api/packaging')
app.register_blueprint(vision_bp,         url_prefix='/api/vision')
app.register_blueprint(products_bp,       url_prefix='/api/products')
app.register_blueprint(reviews_bp,        url_prefix='/api/reviews')
app.register_blueprint(chatbot_bp,        url_prefix='/api/chat')
app.register_blueprint(dashboard_bp,      url_prefix='/api/dashboard')
app.register_blueprint(sustainability_bp,  url_prefix='/api/sustainability')
app.register_blueprint(ecopoints_bp,      url_prefix='/api/ecopoints')
app.register_blueprint(recycling_bp,      url_prefix='/api/recycling')


@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'service': 'Wrapture Backend'})


@app.route('/api/models')
def models():
    registry_path = os.path.join(os.path.dirname(__file__), 'models', 'model_registry.json')
    with open(registry_path) as f:
        registry = json.load(f)

    # Add live availability check
    from config import YOLO_WEIGHTS_PATH, MATERIAL_MODEL_DIR
    registry['product_detector']['weights_present'] = os.path.isfile(YOLO_WEIGHTS_PATH)
    registry['material_classifier']['model_present'] = os.path.isdir(MATERIAL_MODEL_DIR)

    return jsonify(registry)


if __name__ == '__main__':
    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=config.FLASK_DEBUG)
