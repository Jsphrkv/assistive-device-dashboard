from flask import Flask, request, jsonify
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
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
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
    from app.routes.admin import admin_bp
    from app.routes.devices import devices_bp     
    from app.routes.device_routes import device_bp
    from app.routes.detections import detections_bp
    from app.routes.ml_history import ml_history_bp
    from app.routes.statistics import statistics_bp
    from app.routes.settings import settings_bp
    from app.routes.camera_routes import camera_bp
    
    app.register_blueprint(auth_bp)   
    app.register_blueprint(admin_bp)      
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
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
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
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
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
        """Basic health check - no auth required"""
        return {'status': 'healthy', 'message': 'Assistive Device API is running'}, 200
    
    # ✅ NEW: Detailed health endpoint for admin dashboard
    @app.route('/api/health')
    def api_health():
        """
        Detailed health check for admin dashboard.
        Returns status of HF Space, Render backend, and ML models.
        Public endpoint - no auth required.
        """
        import requests as http_requests
        import time
        
        ML_URL = os.getenv('HF_URL', 'https://Josephrkv-capstone2_proj.hf.space')
        
        # Check HF Space
        hf_online = False
        hf_latency = None
        try:
            start = time.time()
            hf_resp = http_requests.get(f"{ML_URL}/health", timeout=3)
            hf_latency = int((time.time() - start) * 1000)
            hf_online = hf_resp.status_code == 200
        except Exception as e:
            print(f"⚠️ HF Space health check failed: {e}")
        
        # Check ML Models
        ml_models = {
            'yolo': {'status': 'unknown', 'source': 'yolo_onnx'},
            'danger': {'status': 'unknown', 'source': 'ml_model'},
            'anomaly': {'status': 'unknown', 'source': 'ml_model'},
            'object': {'status': 'unknown', 'source': 'ml_model'}
        }
        
        try:
            model_resp = http_requests.get(f"{ML_URL}/model-status", timeout=3)
            if model_resp.status_code == 200:
                model_data = model_resp.json()
                for name in ('yolo', 'danger', 'anomaly', 'object'):
                    m = model_data.get(name, {})
                    ml_models[name] = {
                        'status': 'ok' if m.get('loaded') else 'error',
                        'source': m.get('source', 'unknown')
                    }
        except Exception as e:
            print(f"⚠️ Failed to fetch model status: {e}")
        
        return jsonify({
            'status': 'online',
            'hfSpace': {
                'status': 'ok' if hf_online else 'error',
                'latencyMs': hf_latency
            },
            'renderBackend': {
                'status': 'ok',  # If this runs, backend is online
                'latencyMs': 0
            },
            'mlModels': ml_models
        }), 200
    
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