from flask import Flask, request
from flask_cors import CORS
from app.config import config
import os

def create_app(config_name=None):
    """Application factory pattern"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object('app.config.Config')

    app.url_map.strict_slashes = False
    
    # Initialize CORS
    CORS(app, 
         origins=[
             "https://assistive-device-dashboard.vercel.app",
             "http://localhost:3000",
             "http://localhost:5173"
         ],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         allow_headers=["Content-Type", "Authorization", "X-Device-Token"],
         supports_credentials=True,
         max_age=3600)

    print("="*60)
    print("📧 SENDGRID CONFIGURATION:")
    print(f"API KEY: {'✅ SET' if app.config.get('SENDGRID_API_KEY') else '❌ NOT SET'}")
    print(f"FROM EMAIL: {app.config.get('MAIL_DEFAULT_SENDER')}")
    print(f"FRONTEND URL: {app.config.get('FRONTEND_URL')}")
    print("="*60)

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.devices import devices_bp     
    from app.routes.device_routes import device_bp
    from app.routes.detections import detections_bp
    from app.routes.ml_history import ml_history_bp
    from app.routes.statistics import statistics_bp
    from app.routes.settings import settings_bp
    from app.routes.camera_routes import camera_bp
    
    app.register_blueprint(auth_bp)         
    app.register_blueprint(devices_bp)      
    app.register_blueprint(device_bp)      
    app.register_blueprint(detections_bp)     
    app.register_blueprint(ml_history_bp)  
    app.register_blueprint(statistics_bp)    
    app.register_blueprint(settings_bp)
    app.register_blueprint(camera_bp)

    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            response = app.make_default_options_response()
            response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Device-Token'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            return response

    @app.after_request
    def after_request(response):
        origin = request.headers.get('Origin')
        if origin in [
            "https://assistive-device-dashboard.vercel.app",
            "http://localhost:3000",
            "http://localhost:5173"
        ]:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Device-Token'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response
    
    @app.route('/')
    def root():
        """Root endpoint - API health check"""
        return {
            'status': 'online',
            'service': 'Assistive Device Backend API',
            'version': '1.0.0',
            'endpoints': {
                'devices': '/api/devices',
                'detections': '/api/detections',
                'statistics': '/api/statistics',
                'ml_history': '/api/ml-history'
            }
        }, 200
    
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'message': 'Assistive Device API is running'}, 200
    
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {'error': 'Internal server error'}, 500
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)