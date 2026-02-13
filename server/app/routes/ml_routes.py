from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app.services.supabase_client import get_supabase
from app.middleware.auth import token_required
import time
from datetime import datetime, timezone
from app.services.ml_service import ml_service
from app.services.ml_storage_service import ml_storage
from app.ml_models.model_loader import model_loader
from app.schemas.detection import AnomalyDetectionResponse, ActivityRecognitionResponse, MaintenancePredictionResponse
from app.schemas.device import (
    DeviceTelemetry,
    DeviceMaintenanceInfo,
    DeviceSensorData,
    DeviceAnalysisRequest
)
from app.schemas.ml_types import (
    ObjectDetectionRequest,
    FallDetectionRequest,
    RoutePredictionRequest
)


ml_bp = Blueprint('ml', __name__, url_prefix='/api/ml')

# ========== Anomaly Detection ==========

@ml_bp.route('/detect/anomaly', methods=['POST'])
@token_required
def detect_anomaly():
    """Detect anomalies in device telemetry"""
    try:
        data = request.get_json()
        print(f"🔍 [Anomaly] Received data: {data}")  # Debug log
        
        if not data:
            return jsonify({'error': 'Missing telemetry data'}), 400
        
        device_id = data.get('device_id')
        
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
        
        # Call ML service
        result = ml_service.detect_anomaly(telemetry.dict())
        print(f"✅ [Anomaly] ML result: {result}")  # Debug log
        
        # Save to ml_predictions table
        try:
            supabase = get_supabase()
            prediction = {
                'device_id': device_id,
                'prediction_type': 'anomaly',
                'is_anomaly': result.get('is_anomaly', False),
                'anomaly_score': result.get('anomaly_score', 0),
                'anomaly_severity': result.get('severity', 'low'),
                'anomaly_message': result.get('message', ''),
                'telemetry_data': telemetry.dict(),  # Fixed: use validated data
                'model_version': 'v1.0'
                # Removed 'created_at' - let Supabase default handle it
            }
            
            print(f"💾 [Anomaly] Saving to DB: {prediction}")  # Debug log
            db_result = supabase.table('ml_predictions').insert(prediction).execute()
            print(f"✅ [Anomaly] Saved to DB successfully! ID: {db_result.data[0].get('id') if db_result.data else 'unknown'}")  # Debug log
            
        except Exception as db_error:
            print(f"❌ [Anomaly] Database save failed: {db_error}")
            import traceback
            traceback.print_exc()
            # Don't fail the request if DB save fails
        
        # Return response
        return jsonify({
            'is_anomaly': result.get('is_anomaly', False),
            'anomaly_score': float(result.get('anomaly_score', 0)),
            'confidence': float(result.get('confidence', result.get('anomaly_score', 0))),
            'severity': result.get('severity', 'low'),
            'message': result.get('message', ''),
            'timestamp': int(time.time() * 1000)
        }), 200
        
    except Exception as e:
        print(f"❌ [Anomaly] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Anomaly detection failed'}), 500


# ========== Predictive Maintenance ==========

@ml_bp.route('/predict/maintenance', methods=['POST'])
@token_required
def predict_maintenance():
    """Predict if device needs maintenance"""
    try:
        data = request.get_json()
        print(f"🔍 [Maintenance] Received data: {data}")  # Debug log
        
        if not data:
            return jsonify({'error': 'Missing device data'}), 400
        
        device_id = data.get('device_id')
        
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
        
        # Call ML service
        result = ml_service.predict_maintenance(device_info.dict())
        print(f"✅ [Maintenance] ML result: {result}")  # Debug log
        
        # Save to ml_predictions table
        try:
            supabase = get_supabase()
            prediction = {
                'device_id': device_id,
                'prediction_type': 'maintenance',
                'needs_maintenance': result.get('needs_maintenance', False),
                'maintenance_confidence': result.get('probability', 0),
                'maintenance_priority': result.get('priority', 'low'),
                'maintenance_recommendations': result.get('recommendations', {}),
                'telemetry_data': device_info.dict(),
                'model_version': 'v1.0'
            }
            
            print(f"💾 [Maintenance] Saving to DB: {prediction}")  # Debug log
            db_result = supabase.table('ml_predictions').insert(prediction).execute()
            print(f"✅ [Maintenance] Saved to DB successfully!")  # Debug log
            
        except Exception as db_error:
            print(f"❌ [Maintenance] Database save failed: {db_error}")
            import traceback
            traceback.print_exc()
        
        # Return response
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
        print(f"❌ [Maintenance] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Maintenance prediction failed: {str(e)}'}), 500


# ========== Activity Recognition ==========

@ml_bp.route('/recognize/activity', methods=['POST'])
@token_required
def recognize_activity():
    """Recognize user activity from sensor data"""
    try:
        data = request.get_json()
        print(f"🔍 [Activity] Received data: {data}")  # Debug log
        
        if not data:
            return jsonify({'error': 'Missing sensor data'}), 400
        
        device_id = data.get('device_id')
        
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
        
        # Call ML service
        result = ml_service.recognize_activity(sensor_data.dict())
        print(f"✅ [Activity] ML result: {result}")  # Debug log
        
        # Save to ml_predictions table
        try:
            supabase = get_supabase()
            prediction = {
                'device_id': device_id,
                'prediction_type': 'activity',
                'detected_activity': result.get('activity', ''),
                'activity_confidence': result.get('confidence', 0),
                'activity_intensity': result.get('intensity', 'low'),
                'activity_probabilities': result.get('probabilities', {}),
                'sensor_data': sensor_data.dict(),
                'model_version': 'v1.0'
            }
            
            print(f"💾 [Activity] Saving to DB: {prediction}")  # Debug log
            db_result = supabase.table('ml_predictions').insert(prediction).execute()
            print(f"✅ [Activity] Saved to DB successfully!")  # Debug log
            
        except Exception as db_error:
            print(f"❌ [Activity] Database save failed: {db_error}")
            import traceback
            traceback.print_exc()
        
        # Return response
        return jsonify({
            'activity': result.get('activity', ''),
            'confidence': float(result.get('confidence', 0)),
            'message': result.get('message', f"User is {result.get('activity', 'unknown')}"),
            'timestamp': int(time.time() * 1000)
        }), 200
        
    except RuntimeError as e:
        return jsonify({'error': str(e)}), 503
    except Exception as e:
        print(f"❌ [Activity] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Activity recognition failed: {str(e)}'}), 500
    
# ========== OBJECT/OBSTACLE DETECTION ==========

@ml_new_bp.route('/detect/object', methods=['POST'])
@token_required
def detect_object():
    """Detect and classify objects/obstacles"""
    try:
        data = request.get_json()
        print(f"🔍 [Object Detection] Received data: {data}")
        
        if not data:
            return jsonify({'error': 'Missing detection data'}), 400
        
        device_id = data.get('device_id')
        if not device_id:
            return jsonify({'error': 'device_id is required'}), 400
        
        # Validate input
        try:
            detection_request = ObjectDetectionRequest(**data)
        except ValidationError as e:
            return jsonify({
                'error': 'Invalid detection data',
                'details': e.errors()
            }), 400
        
        # Call ML service
        result = ml_service.detect_object(detection_request.dict())
        print(f"✅ [Object Detection] Result: {result}")
        
        # Save to database
        try:
            supabase = get_supabase()
            prediction = {
                'device_id': device_id,
                'prediction_type': 'detection',
                'object_detected': result.get('object_detected'),
                'distance_cm': result.get('distance_cm'),
                'danger_level': result.get('danger_level'),
                'detection_source': data.get('detection_source'),
                'detection_confidence': result.get('detection_confidence'),
                'is_anomaly': result.get('danger_level') in ['High', 'Critical'],
                'model_version': 'v1.0'
            }
            
            print(f"💾 [Object Detection] Saving to DB: {prediction}")
            db_result = supabase.table('ml_predictions').insert(prediction).execute()
            print(f"✅ [Object Detection] Saved successfully!")
            
        except Exception as db_error:
            print(f"❌ [Object Detection] Database save failed: {db_error}")
            import traceback
            traceback.print_exc()
        
        # Return response
        return jsonify({
            'object_detected': result.get('object_detected'),
            'distance_cm': result.get('distance_cm'),
            'danger_level': result.get('danger_level'),
            'detection_confidence': result.get('detection_confidence'),
            'message': result.get('message'),
            'timestamp': int(time.time() * 1000)
        }), 200
        
    except Exception as e:
        print(f"❌ [Object Detection] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Object detection failed'}), 500


# ========== FALL DETECTION ==========

@ml_new_bp.route('/detect/fall', methods=['POST'])
@token_required
def detect_fall():
    """Detect if user has fallen"""
    try:
        data = request.get_json()
        print(f"🔍 [Fall Detection] Received data: {data}")
        
        if not data:
            return jsonify({'error': 'Missing sensor data'}), 400
        
        device_id = data.get('device_id')
        if not device_id:
            return jsonify({'error': 'device_id is required'}), 400
        
        # Validate input
        try:
            fall_request = FallDetectionRequest(**data)
        except ValidationError as e:
            return jsonify({
                'error': 'Invalid sensor data',
                'details': e.errors()
            }), 400
        
        # Call ML service
        result = ml_service.detect_fall(fall_request.dict())
        print(f"✅ [Fall Detection] Result: {result}")
        
        # Save to database
        try:
            supabase = get_supabase()
            prediction = {
                'device_id': device_id,
                'prediction_type': 'fall_detection',
                'fall_detected': result.get('fall_detected'),
                'fall_confidence': result.get('confidence'),
                'fall_severity': result.get('severity'),
                'post_fall_movement': result.get('post_fall_movement'),
                'impact_magnitude': result.get('impact_magnitude'),
                'is_anomaly': result.get('fall_detected'),  # Falls are anomalies
                'sensor_data': fall_request.dict(),
                'model_version': 'v1.0'
            }
            
            print(f"💾 [Fall Detection] Saving to DB: {prediction}")
            db_result = supabase.table('ml_predictions').insert(prediction).execute()
            print(f"✅ [Fall Detection] Saved successfully!")
            
            # If emergency alert, trigger notification (implement later)
            if result.get('emergency_alert'):
                print(f"🚨 [Fall Detection] EMERGENCY ALERT - Fall detected!")
                # TODO: Send emergency notification to contacts
            
        except Exception as db_error:
            print(f"❌ [Fall Detection] Database save failed: {db_error}")
            import traceback
            traceback.print_exc()
        
        # Return response
        return jsonify({
            'fall_detected': result.get('fall_detected'),
            'confidence': result.get('confidence'),
            'severity': result.get('severity'),
            'post_fall_movement': result.get('post_fall_movement'),
            'impact_magnitude': result.get('impact_magnitude'),
            'message': result.get('message'),
            'emergency_alert': result.get('emergency_alert'),
            'timestamp': int(time.time() * 1000)
        }), 200
        
    except Exception as e:
        print(f"❌ [Fall Detection] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Fall detection failed'}), 500


# ========== ROUTE PREDICTION ==========

@ml_new_bp.route('/predict/route', methods=['POST'])
@token_required
def predict_route():
    """Predict best route to destination"""
    try:
        data = request.get_json()
        print(f"🔍 [Route Prediction] Received data: {data}")
        
        if not data:
            return jsonify({'error': 'Missing route data'}), 400
        
        device_id = data.get('device_id')
        if not device_id:
            return jsonify({'error': 'device_id is required'}), 400
        
        # Validate input
        try:
            route_request = RoutePredictionRequest(**data)
        except ValidationError as e:
            return jsonify({
                'error': 'Invalid route data',
                'details': e.errors()
            }), 400
        
        # Call ML service
        result = ml_service.predict_route(route_request.dict())
        print(f"✅ [Route Prediction] Result: {result}")
        
        # Save to database
        try:
            supabase = get_supabase()
            prediction = {
                'device_id': device_id,
                'prediction_type': 'route_prediction',
                'predicted_route': result.get('predicted_route'),
                'route_difficulty_score': result.get('difficulty_score'),
                'estimated_obstacles': result.get('estimated_obstacles'),
                'route_recommendation': result.get('recommendation'),
                'estimated_time_minutes': result.get('estimated_time_minutes'),
                'is_anomaly': False,  # Routes are not anomalies
                'telemetry_data': route_request.dict(),
                'model_version': 'v1.0'
            }
            
            print(f"💾 [Route Prediction] Saving to DB: {prediction}")
            db_result = supabase.table('ml_predictions').insert(prediction).execute()
            print(f"✅ [Route Prediction] Saved successfully!")
            
        except Exception as db_error:
            print(f"❌ [Route Prediction] Database save failed: {db_error}")
            import traceback
            traceback.print_exc()
        
        # Return response
        return jsonify({
            'predicted_route': result.get('predicted_route'),
            'route_confidence': result.get('route_confidence'),
            'estimated_obstacles': result.get('estimated_obstacles'),
            'difficulty_score': result.get('difficulty_score'),
            'estimated_time_minutes': result.get('estimated_time_minutes'),
            'recommendation': result.get('recommendation'),
            'timestamp': int(time.time() * 1000)
        }), 200
        
    except Exception as e:
        print(f"❌ [Route Prediction] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Route prediction failed'}), 500


# ========== ML History Endpoints ==========

# @ml_bp.route('/history', methods=['GET'])
# @token_required
# def get_ml_history():
#     """Get ML prediction history"""
#     try:
#         device_id = request.args.get('device_id')
#         prediction_type = request.args.get('type')
#         days = int(request.args.get('days', 7))
#         limit = int(request.args.get('limit', 100))
        
#         history = ml_storage.get_ml_history(
#             device_id=device_id,
#             prediction_type=prediction_type,
#             limit=limit,
#             days=days
#         )
        
#         return jsonify({
#             'success': True,
#             'count': len(history),
#             'data': history
#         }), 200
        
#     except Exception as e:
#         print(f"Error fetching history: {e}")
#         return jsonify({'error': 'Failed to fetch history'}), 500


# @ml_bp.route('/statistics', methods=['GET'])
# @token_required
# def get_ml_statistics():
#     """Get aggregated ML statistics"""
#     try:
#         device_id = request.args.get('device_id')
#         days = int(request.args.get('days', 7))
        
#         stats = ml_storage.get_statistics(
#             device_id=device_id,
#             days=days
#         )
        
#         return jsonify({
#             'success': True,
#             'period_days': days,
#             'statistics': stats
#         }), 200
        
#     except Exception as e:
#         print(f"Error fetching statistics: {e}")
#         return jsonify({'error': 'Failed to fetch statistics'}), 500


# ========== Aliases for frontend compatibility ==========

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