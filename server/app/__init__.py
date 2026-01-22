from flask import Flask
from flask_cors import CORS
from app.config import config
import os

def create_app(config_name=None):
    """Application factory pattern"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize CORS
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.device import device_bp        # ← From device.py (singular)
    from app.routes.devices import devices_bp      # ← From devices.py (plural)
    from app.routes.detections import detections_bp
    from app.routes.statistics import statistics_bp
    from app.routes.settings import settings_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(device_bp, url_prefix='/api/device')
    app.register_blueprint(devices_bp, url_prefix='/api/devices')
    app.register_blueprint(detections_bp, url_prefix='/api/detections')
    app.register_blueprint(statistics_bp, url_prefix='/api/statistics')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'message': 'Assistive Device API is running'}, 200
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {'error': 'Internal server error'}, 500
    
    return app