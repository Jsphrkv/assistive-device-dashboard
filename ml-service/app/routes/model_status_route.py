from flask import Blueprint, jsonify
from ml_models.model_loader import load_model, get_yolo_model_path

model_status_bp = Blueprint('model_status', __name__)


@model_status_bp.route('/model-status', methods=['GET'])
def model_status():
    """
    Returns which models are loaded vs falling back to rules.
    Called by Render backend GET /api/admin/health.
    """
    # Check YOLO (ONNX)
    yolo_path  = get_yolo_model_path()
    yolo_ok    = yolo_path is not None

    # Check sklearn models
    def check_model(name):
        try:
            bundle = load_model(name)
            if bundle is None:
                return False, 'fallback'
            if isinstance(bundle, dict):
                return bundle.get('model') is not None, 'ml_model'
            return True, 'ml_model'
        except Exception:
            return False, 'fallback'

    danger_ok,  danger_src  = check_model('danger_predictor')
    anomaly_ok, anomaly_src = check_model('anomaly_detector')
    object_ok,  object_src  = check_model('object_detector')
    env_ok, env_src = check_model('environment_classifier')

    return jsonify({
        'yolo':    {'loaded': yolo_ok,    'source': 'yolo_onnx' if yolo_ok else 'fallback'},
        'danger':  {'loaded': danger_ok,  'source': danger_src},
        'anomaly': {'loaded': anomaly_ok, 'source': anomaly_src},
        'object':  {'loaded': object_ok,  'source': object_src},
        'environment': {'loaded': env_ok, 'source': env_src},
    }), 200


@model_status_bp.route('/health', methods=['GET'])
def health():
    """Simple liveness probe for the health ping."""
    return jsonify({'status': 'ok'}), 200