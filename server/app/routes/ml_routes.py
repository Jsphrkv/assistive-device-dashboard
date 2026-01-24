from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app.services.ml_service import ml_service
from app.services.ml_storage_service import ml_storage  # ← Add this
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

# ========== Anomaly Detection ==========

@ml_bp.route('/detect/anomaly', methods=['POST'])
def detect_anomaly():
    """Detect anomalies in device telemetry"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Missing telemetry data'}), 400
        
        # Get device_id from request (optional)
        device_id = data.pop('device_id', None)
        
        # Validate input
        try:
            telemetry = DeviceTelemetry(**data)
        except ValidationError as e:
            return jsonify({
                'error': 'Invalid telemetry data',
                'details': e.errors()
            }), 400
        
        # Call ML service
        result = ml_service.detect_anomaly(telemetry.dict())
        
        # Validate output
        response = AnomalyDetectionResponse(**result)
        
        # Save to database if device_id provided
        if device_id:
            ml_storage.save_anomaly_prediction(
                device_id=device_id,
                prediction_data=result,
                telemetry_data=telemetry.dict()
            )
        
        return jsonify(response.dict()), 200
        
    except RuntimeError as e:
        return jsonify({'error': str(e)}), 503
    except Exception as e:
        print(f"Anomaly detection error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Anomaly detection failed: {str(e)}'}), 500

# ========== Predictive Maintenance ==========

@ml_bp.route('/predict/maintenance', methods=['POST'])
def predict_maintenance():
    """Predict if device needs maintenance"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Missing device data'}), 400
        
        # Get device_id from request (optional)
        device_id = data.pop('device_id', None)
        
        # Validate input
        try:
            device_info = DeviceMaintenanceInfo(**data)
        except ValidationError as e:
            return jsonify({
                'error': 'Invalid device data',
                'details': e.errors()
            }), 400
        
        # Call ML service
        result = ml_service.predict_maintenance(device_info.dict())
        
        # Validate output
        response = MaintenancePredictionResponse(**result)
        
        # Save to database if device_id provided
        if device_id:
            ml_storage.save_maintenance_prediction(
                device_id=device_id,
                prediction_data=result,
                device_info=device_info.dict()
            )
        
        return jsonify(response.dict()), 200
        
    except RuntimeError as e:
        return jsonify({'error': str(e)}), 503
    except Exception as e:
        print(f"Maintenance prediction error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Maintenance prediction failed: {str(e)}'}), 500

# ========== Activity Recognition ==========

@ml_bp.route('/recognize/activity', methods=['POST'])
def recognize_activity():
    """Recognize user activity from sensor data"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Missing sensor data'}), 400
        
        # Get device_id from request (optional)
        device_id = data.pop('device_id', None)
        
        # Validate input
        try:
            sensor_data = DeviceSensorData(**data)
        except ValidationError as e:
            return jsonify({
                'error': 'Invalid sensor data',
                'details': e.errors()
            }), 400
        
        # Call ML service
        result = ml_service.recognize_activity(sensor_data.dict())
        
        # Validate output
        response = ActivityRecognitionResponse(**result)
        
        # Save to database if device_id provided
        if device_id:
            ml_storage.save_activity_prediction(
                device_id=device_id,
                prediction_data=result,
                sensor_data=sensor_data.dict()
            )
        
        return jsonify(response.dict()), 200
        
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