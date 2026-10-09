import os
import sys
import warnings

# Suppress benign PyTorch & third-party UserWarnings for clean telemetry output
warnings.filterwarnings('ignore', category=UserWarning)

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Configure PyTorch CPU thread count to prevent 100% CPU thread starvation
try:
    import torch
    torch.set_num_threads(4)
except Exception:
    pass


from flask import Flask, jsonify
from flask_cors import CORS
from backend.config import Config
from backend.database.db import init_db
from backend.routes.stream_routes import stream_bp
from backend.routes.truck_routes import truck_bp
from backend.routes.alert_routes import alert_bp
from backend.routes.blocklist_routes import blocklist_bp
from backend.routes.config_routes import config_bp
from backend.routes.export_routes import export_bp
from backend.routes.auth_routes import auth_bp
from backend.routes.dataset_routes import dataset_bp
from backend.routes.fc_routes import fc_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Enable CORS for all routes (supporting frontend on localhost:5173 or production)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Initialize Database Schema & Seed Data
    init_db()
    
    # Register Blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(stream_bp, url_prefix='/api/stream')
    app.register_blueprint(truck_bp, url_prefix='/api/trucks')
    app.register_blueprint(alert_bp, url_prefix='/api/alerts')
    app.register_blueprint(blocklist_bp, url_prefix='/api/blocklist')
    app.register_blueprint(config_bp, url_prefix='/api/config')
    app.register_blueprint(export_bp, url_prefix='/api/export')
    app.register_blueprint(dataset_bp, url_prefix='/api/dataset')
    app.register_blueprint(fc_bp, url_prefix='/api/fc')
    
    @app.route('/api/health', methods=['GET'])
    def health():
        return jsonify({
            'status': 'healthy',
            'system': 'VisionHaul Heavy Vehicle CCTV AI Monitoring System',
            'version': '2.6.0'
        })
        
    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('PORT', 5000))
    print(f"🚀 DEMO AI CCTV Surveillance Server starting on http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
