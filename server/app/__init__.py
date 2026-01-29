from flask import Flask, request
from flask_cors import CORS
from app.config import config
from app.services.email_service import init_mail 
import os
from app.ml_models.model_loader import model_loader

def create_app(config_name=None):
    """Application factory pattern"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": [
                "https://assistive-device-dashboard.vercel.app",
                "http://localhost:3000",
                "http://localhost:5173",
                "http://localhost:5000"  # Local backend testing
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-Device-Token"],
            "expose_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True,
            "max_age": 3600
        }
    })

    # Initialize Flask-Mail ✅ NEW
    init_mail(app)

     # Try to load ML models (don't crash if fails)
    try:
        from app.ml_models.model_loader import model_loader
        print("ML models initialization attempted")
    except Exception as e:
        print(f"⚠ ML models not loaded: {e}")
        print("  API will use fallback predictions")
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.devices import devices_bp     
    from app.routes.device_routes import device_bp
    from app.routes.detections import detections_bp
    from app.routes.ml_routes import ml_bp
    from app.routes.statistics import statistics_bp
    from app.routes.settings import settings_bp
    
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(devices_bp, url_prefix='/api/devices') 
    app.register_blueprint(device_bp, url_prefix='/api/device')
    app.register_blueprint(detections_bp, url_prefix='/api/detections')
    app.register_blueprint(ml_bp, url_prefix='/api/ml')
    app.register_blueprint(statistics_bp, url_prefix='/api/statistics')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin', '*'))
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Device-Token')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

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

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)