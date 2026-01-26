from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app.services.supabase_client import get_supabase
from app.middleware.auth import token_required
import time
from app.services.ml_service import ml_service
from app.services.ml_storage_service import ml_storage
from app.ml_models.model_loader import model_loader
from app.schemas.detection import AnomalyDetectionResponse, ActivityRecognitionResponse, MaintenancePredictionResponse
from app.schemas.device import (
    # Device,
    # DeviceCreate,
    # DeviceUpdate,
    DeviceTelemetry,
    DeviceMaintenanceInfo,
    DeviceSensorData,
    DeviceAnalysisRequest
)


ml_bp = Blueprint('ml', __name__, url_prefix='/api/ml')

# ========== Anomaly Detection ==========

@ml_bp.route('/detect/anomaly', methods=['POST'])
@token_required  # Added auth
def detect_anomaly():
    """Detect anomalies in device telemetry"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Missing telemetry data'}), 400
        
        device_id = data.get('device_id')  # Changed from pop to get
        
        if not device_id:
            return jsonify({'error': 'device_id is required'}), 400
        
        # Validate input
        try:
            telemetry = DeviceTelemetry(**data)
        except ValidationError as e:
            return jsonify({
                'error': 'Invalid telemetry data',
                'details': e.errors()
            }), 400
        
        # Call ML service (UNCHANGED - your actual ML model)
        result = ml_service.detect_anomaly(telemetry.dict())
        
        # Save to ml_predictions table (UPDATED format)
        supabase = get_supabase()
        prediction = {
            'device_id': device_id,
            'prediction_type': 'anomaly',
            'is_anomaly': result.get('is_anomaly', False),
            'anomaly_score': result.get('anomaly_score', 0),
            'anomaly_severity': result.get('severity', 'low'),  # Changed field name
            'anomaly_message': result.get('message', ''),  # Changed field name
            'telemetry_data': data.get('sensor_data', {}),  # Added
            'model_version': 'v1.0',  # Added
            'created_at': 'now()'
        }
        
        supabase.table('ml_predictions').insert(prediction).execute()
        
        # Return response matching frontend format (UPDATED)
        return jsonify({
            'is_anomaly': result.get('is_anomaly', False),
            'anomaly_score': float(result.get('anomaly_score', 0)),
            'confidence': float(result.get('confidence', result.get('anomaly_score', 0))),
            'severity': result.get('severity', 'low'),
            'message': result.get('message', ''),
            'timestamp': int(time.time() * 1000)  # JS timestamp
        }), 200
        
    except Exception as e:
        print(f"Anomaly detection error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Anomaly detection failed'}), 500


# ========== Predictive Maintenance ==========

@ml_bp.route('/predict/maintenance', methods=['POST'])
@token_required  # Added auth
def predict_maintenance():
    """Predict if device needs maintenance"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Missing device data'}), 400
        
        device_id = data.get('device_id')  # Changed from pop to get
        
        if not device_id:
            return jsonify({'error': 'device_id is required'}), 400
        
        # Validate input
        try:
            device_info = DeviceMaintenanceInfo(**data)
        except ValidationError as e:
            return jsonify({
                'error': 'Invalid device data',
                'details': e.errors()
            }), 400
        
        # Call ML service (UNCHANGED - your actual ML model)
        result = ml_service.predict_maintenance(device_info.dict())
        
        # Save to ml_predictions table (UPDATED format)
        supabase = get_supabase()
        prediction = {
            'device_id': device_id,
            'prediction_type': 'maintenance',
            'needs_maintenance': result.get('needs_maintenance', False),
            'maintenance_confidence': result.get('probability', 0),
            'maintenance_priority': result.get('priority', 'low'),
            'maintenance_recommendations': result.get('recommendations', {}),
            'telemetry_data': device_info.dict(),
            'model_version': 'v1.0',
            'created_at': 'now()'
        }
        
        supabase.table('ml_predictions').insert(prediction).execute()
        
        # Return response matching frontend format (UPDATED)
        return jsonify({
            'maintenance_needed': result.get('needs_maintenance', False),
            'probability': float(result.get('probability', 0)),
            'days_until': result.get('days_until', 0),
            'message': result.get('message', ''),
            'timestamp': int(time.time() * 1000)
        }), 200
        
    except RuntimeError as e:
        return jsonify({'error': str(e)}), 503
    except Exception as e:
        print(f"Maintenance prediction error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Maintenance prediction failed: {str(e)}'}), 500

# ========== Activity Recognition ==========

@ml_bp.route('/recognize/activity', methods=['POST'])
@token_required  # Added auth
def recognize_activity():
    """Recognize user activity from sensor data"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Missing sensor data'}), 400
        
        device_id = data.get('device_id')  # Changed from pop to get
        
        if not device_id:
            return jsonify({'error': 'device_id is required'}), 400
        
        # Validate input
        try:
            sensor_data = DeviceSensorData(**data)
        except ValidationError as e:
            return jsonify({
                'error': 'Invalid sensor data',
                'details': e.errors()
            }), 400
        
        # Call ML service (UNCHANGED - your actual ML model)
        result = ml_service.recognize_activity(sensor_data.dict())
        
        # Save to ml_predictions table (UPDATED format)
        supabase = get_supabase()
        prediction = {
            'device_id': device_id,
            'prediction_type': 'activity',
            'detected_activity': result.get('activity', ''),
            'activity_confidence': result.get('confidence', 0),
            'activity_intensity': result.get('intensity', 'low'),
            'activity_probabilities': result.get('probabilities', {}),
            'sensor_data': sensor_data.dict(),
            'model_version': 'v1.0',
            'created_at': 'now()'
        }
        
        supabase.table('ml_predictions').insert(prediction).execute()
        
        # Return response matching frontend format (UPDATED)
        return jsonify({
            'activity': result.get('activity', ''),
            'confidence': float(result.get('confidence', 0)),
            'message': result.get('message', f"User is {result.get('activity', 'unknown')}"),
            'timestamp': int(time.time() * 1000)
        }), 200
        
    except RuntimeError as e:
        return jsonify({'error': str(e)}), 503
    except Exception as e:
        print(f"Activity recognition error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Activity recognition failed: {str(e)}'}), 500

# ========== NEW: ML History Endpoints ==========

@ml_bp.route('/history', methods=['GET'])
def get_ml_history():
    """
    Get ML prediction history
    
    Query params:
    - device_id: Filter by device (optional)
    - type: Filter by prediction type (anomaly, maintenance, activity)
    - days: Number of days to look back (default: 7)
    - limit: Max number of records (default: 100)
    """
    try:
        device_id = request.args.get('device_id')
        prediction_type = request.args.get('type')
        days = int(request.args.get('days', 7))
        limit = int(request.args.get('limit', 100))
        
        history = ml_storage.get_ml_history(
            device_id=device_id,
            prediction_type=prediction_type,
            limit=limit,
            days=days
        )
        
        return jsonify({
            'success': True,
            'count': len(history),
            'data': history
        }), 200
        
    except Exception as e:
        print(f"Error fetching history: {e}")
        return jsonify({'error': 'Failed to fetch history'}), 500

@ml_bp.route('/statistics', methods=['GET'])
def get_ml_statistics():
    """
    Get aggregated ML statistics
    
    Query params:
    - device_id: Filter by device (optional)
    - days: Number of days to look back (default: 7)
    """
    try:
        device_id = request.args.get('device_id')
        days = int(request.args.get('days', 7))
        
        stats = ml_storage.get_statistics(
            device_id=device_id,
            days=days
        )
        
        return jsonify({
            'success': True,
            'period_days': days,
            'statistics': stats
        }), 200
        
    except Exception as e:
        print(f"Error fetching statistics: {e}")
        return jsonify({'error': 'Failed to fetch statistics'}), 500

# ========== Comprehensive Analysis (with DB save) ==========

@ml_bp.route('/analyze/device', methods=['POST'])
def analyze_device():
    """Comprehensive device analysis with database storage"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Missing request data'}), 400
        
        # Get device_id
        device_id = data.get('device_id')
        
        # Validate entire request
        try:
            analysis_request = DeviceAnalysisRequest(**data)
        except ValidationError as e:
            return jsonify({
                'error': 'Invalid analysis request',
                'details': e.errors()
            }), 400
        
        analysis = {}
        
        # Anomaly detection
        if analysis_request.telemetry:
            try:
                result = ml_service.detect_anomaly(analysis_request.telemetry.dict())
                analysis['anomaly'] = AnomalyDetectionResponse(**result).dict()
                
                # Save to DB
                if device_id:
                    ml_storage.save_anomaly_prediction(
                        device_id, result, analysis_request.telemetry.dict()
                    )
            except Exception as e:
                analysis['anomaly'] = {'error': str(e)}
        
        # Maintenance prediction
        if analysis_request.device_info:
            try:
                result = ml_service.predict_maintenance(analysis_request.device_info.dict())
                analysis['maintenance'] = MaintenancePredictionResponse(**result).dict()
                
                # Save to DB
                if device_id:
                    ml_storage.save_maintenance_prediction(
                        device_id, result, analysis_request.device_info.dict()
                    )
            except Exception as e:
                analysis['maintenance'] = {'error': str(e)}
        
        # Activity recognition
        if analysis_request.sensor_data:
            try:
                result = ml_service.recognize_activity(analysis_request.sensor_data.dict())
                analysis['activity'] = ActivityRecognitionResponse(**result).dict()
                
                # Save to DB
                if device_id:
                    ml_storage.save_activity_prediction(
                        device_id, result, analysis_request.sensor_data.dict()
                    )
            except Exception as e:
                analysis['activity'] = {'error': str(e)}
        
        return jsonify(analysis), 200
        
    except Exception as e:
        print(f"Analysis error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500
    
@ml_bp.route('/anomaly-detection', methods=['POST'])
def detect_anomaly_alias():
    """Alias for /detect/anomaly to match frontend"""
    return detect_anomaly()

@ml_bp.route('/activity-recognition', methods=['POST'])
def recognize_activity_alias():
    """Alias for /recognize/activity to match frontend"""
    return recognize_activity()

@ml_bp.route('/maintenance-prediction', methods=['POST'])
def predict_maintenance_alias():
    """Alias for /predict/maintenance to match frontend"""
    return predict_maintenance()