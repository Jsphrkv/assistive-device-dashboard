import time
from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app.services.supabase_client import get_supabase
from app.middleware.auth import device_token_required
from app.services.ml_service import ml_service
from app.services.yolo_service import run_yolo
from app.schemas.device import DeviceTelemetry
from app.schemas.ml_types import (
    YOLODetectionRequest,
    ObjectDetectionRequest,
    DangerPredictionRequest,
    EnvironmentClassificationRequest,
)

ml_bp = Blueprint('ml', __name__, url_prefix='/api/ml')


def save_to_db(prediction_data):
    """Save prediction result to Supabase ml_predictions table."""
    try:
        supabase = get_supabase()
        supabase.table('ml_predictions').insert(prediction_data).execute()
    except Exception as e:
        print(f"[DB] Save failed: {e}")


# ── YOLO Detection ────────────────────────────────────────────────────────────

@ml_bp.route('/detect/yolo', methods=['POST'])
@device_token_required
def detect_yolo():
    try:
        device_id = request.current_device['id']
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Missing data'}), 400
        data['device_id'] = device_id
        try:
            req = YOLODetectionRequest(**data)
        except ValidationError as e:
            return jsonify({'error': 'Invalid request', 'details': e.errors()}), 400

        print(f"[YOLO] Running inference for device {device_id}")
        result = run_yolo(req.image_data)
        print(f"[YOLO] Result: {result.get('message')}")

        if result.get('detected'):
            save_to_db({
                'device_id':            device_id,
                'prediction_type':      'yolo_detection',
                'object_detected':      result.get('object_type'),
                'distance_cm':          req.distance_cm,
                'detection_confidence': result.get('confidence'),
                'is_anomaly':           False
            })

        return jsonify({
            'detected':        result.get('detected',       False),
            'object_type':     result.get('object_type',    'none'),
            'raw_label':       result.get('raw_label',      'none'),
            'category':        result.get('category',       'navigation'),
            'confidence':      result.get('confidence',     0.0),
            'box':             result.get('box'),                     # NEW: for Option A
            'all_detections':  result.get('all_detections', []),
            'message':         result.get('message',        ''),
            'timestamp':       int(time.time() * 1000)
        }), 200

    except Exception as e:
        print(f"[YOLO] Error: {e}")
        import traceback; traceback.print_exc()
        return jsonify({'error': 'YOLO detection failed'}), 500


# ── Object Detection ──────────────────────────────────────────────────────────

@ml_bp.route('/detect/object', methods=['POST'])
@device_token_required
def detect_object():
    try:
        device_id = request.current_device['id']
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Missing data'}), 400
        data['device_id'] = device_id
        try:
            req = ObjectDetectionRequest(**data)
        except ValidationError as e:
            return jsonify({'error': 'Invalid detection data', 'details': e.errors()}), 400

        result = ml_service.detect_object(req.dict())

        save_to_db({
            'device_id':            device_id,
            'prediction_type':      'object_detection',
            'object_detected':      result.get('object_detected'),
            'distance_cm':          result.get('distance_cm'),
            'danger_level':         result.get('danger_level'),
            'detection_confidence': result.get('detection_confidence'),
            'model_source':         result.get('model_source'),       # NEW
            'is_anomaly':           result.get('danger_level') in ['High', 'Critical']
        })

        return jsonify({
            'object_detected':      result.get('object_detected'),
            'distance_cm':          result.get('distance_cm'),
            'danger_level':         result.get('danger_level'),
            'detection_confidence': result.get('detection_confidence'),
            'model_source':         result.get('model_source'),       # NEW
            'message':              result.get('message'),
            'timestamp':            int(time.time() * 1000)
        }), 200

    except Exception as e:
        print(f"[Object Detection] Error: {e}")
        return jsonify({'error': 'Object detection failed'}), 500


# ── Danger Prediction ─────────────────────────────────────────────────────────

@ml_bp.route('/predict/danger', methods=['POST'])
@device_token_required
def predict_danger():
    try:
        device_id = request.current_device['id']
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Missing data'}), 400
        data['device_id'] = device_id
        try:
            req = DangerPredictionRequest(**data)
        except ValidationError as e:
            return jsonify({'error': 'Invalid danger data', 'details': e.errors()}), 400

        result = ml_service.predict_danger(req.dict())

        save_to_db({
            'device_id':          device_id,
            'prediction_type':    'danger_prediction',
            'danger_score':       result.get('danger_score'),
            'recommended_action': result.get('recommended_action'),
            'time_to_collision':  result.get('time_to_collision'),
            'model_source':       result.get('model_source'),         # NEW
            'is_anomaly':         result.get('danger_score', 0) > 70
        })

        return jsonify({
            'danger_score':       result.get('danger_score'),
            'recommended_action': result.get('recommended_action'),
            'time_to_collision':  result.get('time_to_collision'),
            'confidence':         result.get('confidence'),
            'model_source':       result.get('model_source'),         # NEW
            'message':            result.get('message'),
            'timestamp':          int(time.time() * 1000)
        }), 200

    except Exception as e:
        print(f"[Danger Prediction] Error: {e}")
        return jsonify({'error': 'Danger prediction failed'}), 500


# ── Anomaly Detection ─────────────────────────────────────────────────────────

@ml_bp.route('/detect/anomaly', methods=['POST'])
@device_token_required
def detect_anomaly():
    try:
        device_id = request.current_device['id']
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Missing data'}), 400
        data['device_id'] = device_id
        try:
            req = DeviceTelemetry(**data)
        except ValidationError as e:
            return jsonify({'error': 'Invalid telemetry data', 'details': e.errors()}), 400

        result = ml_service.detect_anomaly(req.dict())

        save_to_db({
            'device_id':           device_id,
            'prediction_type':     'anomaly',
            'is_anomaly':          result.get('is_anomaly',          False),
            'anomaly_score':       result.get('anomaly_score',       0),
            'anomaly_severity':    result.get('severity',            'low'),
            'device_health_score': result.get('device_health_score', 100),
            'model_source':        result.get('model_source'),               # NEW
        })

        return jsonify({
            'is_anomaly':          result.get('is_anomaly',          False),
            'anomaly_score':       float(result.get('anomaly_score', 0)),
            'confidence':          float(result.get('confidence',    0)),
            'severity':            result.get('severity',            'low'),
            'device_health_score': result.get('device_health_score', 100),
            'model_source':        result.get('model_source'),               # NEW
            'message':             result.get('message',             ''),
            'timestamp':           int(time.time() * 1000)
        }), 200

    except Exception as e:
        print(f"[Anomaly] Error: {e}")
        return jsonify({'error': 'Anomaly detection failed'}), 500


# ── Environment Classification ────────────────────────────────────────────────

@ml_bp.route('/classify/environment', methods=['POST'])
@device_token_required
def classify_environment():
    try:
        device_id = request.current_device['id']
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Missing data'}), 400
        data['device_id'] = device_id
        try:
            req = EnvironmentClassificationRequest(**data)
        except ValidationError as e:
            return jsonify({'error': 'Invalid environment data', 'details': e.errors()}), 400

        result = ml_service.classify_environment(req.dict())

        save_to_db({
            'device_id':          device_id,
            'prediction_type':    'environment_classification',
            'environment_type':   result.get('environment_type'),
            'lighting_condition': result.get('lighting_condition'),
            'complexity_level':   result.get('complexity_level'),
            'model_source':       result.get('model_source'),         # NEW
            'is_anomaly':         False
        })

        return jsonify({
            'environment_type':   result.get('environment_type'),
            'lighting_condition': result.get('lighting_condition'),
            'complexity_level':   result.get('complexity_level'),
            'confidence':         result.get('confidence'),
            'model_source':       result.get('model_source'),         # NEW
            'message':            result.get('message'),
            'timestamp':          int(time.time() * 1000)
        }), 200

    except Exception as e:
        print(f"[Environment] Error: {e}")
        return jsonify({'error': 'Environment classification failed'}), 500