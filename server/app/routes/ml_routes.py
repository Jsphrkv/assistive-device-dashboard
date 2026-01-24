from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app.services.ml_service import ml_service
from app.ml_models.model_loader import model_loader
from app.schemas import (
    DeviceTelemetry,
    DeviceMaintenanceInfo,
    DeviceSensorData,
    DeviceAnalysisRequest,
    AnomalyDetectionResponse,
    MaintenancePredictionResponse,
    ActivityRecognitionResponse
)

ml_bp = Blueprint('ml', __name__, url_prefix='/api/ml')

# ========== Health & Status ==========

@ml_bp.route('/health', methods=['GET'])
def health_check():
    """Check if ML service is ready"""
    models_loaded = {
        'device_classifier': ml_service.device_classifier is not None,
        'anomaly_detector': ml_service.anomaly_detector is not None,
        'maintenance_predictor': ml_service.maintenance_predictor is not None,
        'activity_recognizer': ml_service.activity_recognizer is not None
    }
    
    all_loaded = all(models_loaded.values())
    
    return jsonify({
        'status': 'ready' if all_loaded else 'partial',
        'models': models_loaded,
        'total_loaded': sum(models_loaded.values()),
        'total_expected': len(models_loaded)
    }), 200 if all_loaded else 206

@ml_bp.route('/models', methods=['GET'])
def list_models():
    """List available models"""
    return jsonify({
        'available_models': model_loader.list_available_models()
    }), 200

# ========== Device Classification ==========

@ml_bp.route('/predict/device', methods=['POST'])
def predict_device():
    """Predict device type based on features"""
    try:
        data = request.get_json()
        
        if not data or 'features' not in data:
            return jsonify({'error': 'Missing features in request body'}), 400
        
        features = data['features']
        
        if len(features) != 5:
            return jsonify({'error': 'Expected 5 features'}), 400
        
        result = ml_service.predict_device_type(features)
        return jsonify(result), 200
        
    except RuntimeError as e:
        return jsonify({'error': str(e)}), 503
    except Exception as e:
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500

# ========== Anomaly Detection ==========

@ml_bp.route('/detect/anomaly', methods=['POST'])
def detect_anomaly():
    """
    Detect anomalies in device telemetry
    
    Request body (DeviceTelemetry):
    {
        "battery_level": 15,
        "usage_duration": 350,
        "temperature": 52,
        "signal_strength": -85,
        "error_count": 8
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Missing telemetry data'}), 400
        
        # Validate input using Pydantic schema
        try:
            telemetry = DeviceTelemetry(**data)
        except ValidationError as e:
            return jsonify({
                'error': 'Invalid telemetry data',
                'details': e.errors()
            }), 400
        
        # Call ML service with validated data
        result = ml_service.detect_anomaly(telemetry.dict())
        
        # Validate output using Pydantic schema
        response = AnomalyDetectionResponse(**result)
        
        return jsonify(response.dict()), 200
        
    except RuntimeError as e:
        return jsonify({'error': str(e)}), 503
    except Exception as e:
        return jsonify({'error': f'Anomaly detection failed: {str(e)}'}), 500

# ========== Predictive Maintenance ==========

@ml_bp.route('/predict/maintenance', methods=['POST'])
def predict_maintenance():
    """
    Predict if device needs maintenance
    
    Request body (DeviceMaintenanceInfo):
    {
        "device_age_days": 450,
        "battery_cycles": 620,
        "usage_intensity": 0.75,
        "error_rate": 1.2,
        "last_maintenance_days": 120
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Missing device data'}), 400
        
        # Validate input using Pydantic schema
        try:
            device_info = DeviceMaintenanceInfo(**data)
        except ValidationError as e:
            return jsonify({
                'error': 'Invalid device data',
                'details': e.errors()
            }), 400
        
        # Call ML service with validated data
        result = ml_service.predict_maintenance(device_info.dict())
        
        # Validate output using Pydantic schema
        response = MaintenancePredictionResponse(**result)
        
        return jsonify(response.dict()), 200
        
    except RuntimeError as e:
        return jsonify({'error': str(e)}), 503
    except Exception as e:
        return jsonify({'error': f'Maintenance prediction failed: {str(e)}'}), 500

# ========== Activity Recognition ==========

@ml_bp.route('/recognize/activity', methods=['POST'])
def recognize_activity():
    """
    Recognize user activity from sensor data
    
    Request body (DeviceSensorData):
    {
        "acc_x": 0.5,
        "acc_y": 0.3,
        "acc_z": 9.8,
        "gyro_x": 5.2,
        "gyro_y": 3.1,
        "gyro_z": 2.5
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Missing sensor data'}), 400
        
        # Validate input using Pydantic schema
        try:
            sensor_data = DeviceSensorData(**data)
        except ValidationError as e:
            return jsonify({
                'error': 'Invalid sensor data',
                'details': e.errors()
            }), 400
        
        # Call ML service with validated data
        result = ml_service.recognize_activity(sensor_data.dict())
        
        # Validate output using Pydantic schema
        response = ActivityRecognitionResponse(**result)
        
        return jsonify(response.dict()), 200
        
    except RuntimeError as e:
        return jsonify({'error': str(e)}), 503
    except Exception as e:
        return jsonify({'error': f'Activity recognition failed: {str(e)}'}), 500

# ========== Batch Predictions ==========

@ml_bp.route('/analyze/device', methods=['POST'])
def analyze_device():
    """
    Comprehensive device analysis combining multiple ML models
    
    Request body (DeviceAnalysisRequest):
    {
        "telemetry": { battery_level, usage_duration, temperature, signal_strength, error_count },
        "device_info": { device_age_days, battery_cycles, usage_intensity, error_rate, last_maintenance_days },
        "sensor_data": { acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z }
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Missing request data'}), 400
        
        # Validate entire request using Pydantic schema
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
            except Exception as e:
                analysis['anomaly'] = {'error': str(e)}
        
        # Maintenance prediction
        if analysis_request.device_info:
            try:
                result = ml_service.predict_maintenance(analysis_request.device_info.dict())
                analysis['maintenance'] = MaintenancePredictionResponse(**result).dict()
            except Exception as e:
                analysis['maintenance'] = {'error': str(e)}
        
        # Activity recognition
        if analysis_request.sensor_data:
            try:
                result = ml_service.recognize_activity(analysis_request.sensor_data.dict())
                analysis['activity'] = ActivityRecognitionResponse(**result).dict()
            except Exception as e:
                analysis['activity'] = {'error': str(e)}
        
        return jsonify(analysis), 200
        
    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500