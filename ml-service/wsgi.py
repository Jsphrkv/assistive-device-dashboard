import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()


def create_app():
    app = Flask(__name__)
    CORS(app)

    # Register blueprints
    from app.routes.ml import ml_bp
    app.register_blueprint(ml_bp)

    # Admin health-check endpoints (used by Render backend /api/admin/health)
    from app.routes.model_status_route import model_status_bp
    app.register_blueprint(model_status_bp)

    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({'status': 'ok', 'service': 'assistive-device-ml'}), 200

    @app.route('/', methods=['GET'])
    def index():
        return jsonify({
            'service': 'Assistive Device ML Service',
            'endpoints': [
                'POST /api/ml/detect/yolo',
                'POST /api/ml/detect/object',
                'POST /api/ml/predict/danger',
                'POST /api/ml/classify/environment',
                'POST /api/ml/detect/anomaly',
                'GET  /health',
                'GET  /model-status',
            ]
        }), 200

    return app


app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 7860))
    app.run(host='0.0.0.0', port=port, debug=False)