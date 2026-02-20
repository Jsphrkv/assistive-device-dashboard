# from flask import Blueprint, request, jsonify
# from pydantic import ValidationError
# from app.services.supabase_client import get_supabase
# from app.middleware.auth import device_token_required  # ✅ CHANGED from token_required
# import time
# from datetime import datetime, timezone
# from app.services.ml_service import ml_service
# from app.schemas.device import (
#     DeviceTelemetry,
#     DeviceMaintenanceInfo
# )
# from app.schemas.ml_types import (
#     ObjectDetectionRequest,
#     DangerPredictionRequest,
#     EnvironmentClassificationRequest
# )


# ml_bp = Blueprint('ml', __name__, url_prefix='/api/ml')

# # ========== DEVICE ANOMALY DETECTION ==========

# @ml_bp.route('/detect/anomaly', methods=['POST'])
# @device_token_required  # ✅ CHANGED - RPi uses device token
# def detect_anomaly():
#     """Detect anomalies in device telemetry"""
#     try:
#         device_id = request.current_device['id']  # ✅ CHANGED - Get from device context
#         data = request.get_json()
#         print(f"🔍 [Anomaly] Received data: {data}")
        
#         if not data:
#             return jsonify({'error': 'Missing telemetry data'}), 400
        
#         # ✅ CHANGED - Use device_id from auth context
#         data['device_id'] = device_id
        
#         # Validate input
#         try:
#             telemetry = DeviceTelemetry(**data)
#         except ValidationError as e:
#             return jsonify({
#                 'error': 'Invalid telemetry data',
#                 'details': e.errors()
#             }), 400
        
#         # Call ML service
#         result = ml_service.detect_anomaly(telemetry.dict())
#         print(f"✅ [Anomaly] ML result: {result}")
        
#         # Save to ml_predictions table
#         try:
#             supabase = get_supabase()
            
#             prediction = {
#                 'device_id': device_id,
#                 'prediction_type': 'anomaly',
#                 'is_anomaly': result.get('is_anomaly', False),
#                 'anomaly_score': result.get('anomaly_score', 0),
#                 'anomaly_severity': result.get('severity', 'low'),
#                 'device_health_score': result.get('device_health_score', 100)
#             }
            
#             print(f"💾 [Anomaly] Saving to DB: {prediction}")
#             db_result = supabase.table('ml_predictions').insert(prediction).execute()
#             print(f"✅ [Anomaly] Saved to DB successfully!")
            
#         except Exception as db_error:
#             print(f"❌ [Anomaly] Database save failed: {db_error}")
#             import traceback
#             traceback.print_exc()
        
#         # Return response
#         return jsonify({
#             'is_anomaly': result.get('is_anomaly', False),
#             'anomaly_score': float(result.get('anomaly_score', 0)),
#             'confidence': float(result.get('confidence', result.get('anomaly_score', 0))),
#             'severity': result.get('severity', 'low'),
#             'device_health_score': result.get('device_health_score', 100),
#             'message': result.get('message', ''),
#             'timestamp': int(time.time() * 1000)
#         }), 200
        
#     except Exception as e:
#         print(f"❌ [Anomaly] Error: {e}")
#         import traceback
#         traceback.print_exc()
#         return jsonify({'error': 'Anomaly detection failed'}), 500


# # ========== PREDICTIVE MAINTENANCE ==========

# @ml_bp.route('/predict/maintenance', methods=['POST'])
# @device_token_required  # ✅ CHANGED - RPi uses device token
# def predict_maintenance():
#     """Predict if device needs maintenance"""
#     try:
#         device_id = request.current_device['id']  # ✅ CHANGED
#         data = request.get_json()
#         print(f"🔍 [Maintenance] Received data: {data}")
        
#         if not data:
#             return jsonify({'error': 'Missing device data'}), 400
        
#         # ✅ CHANGED - Use device_id from auth context
#         data['device_id'] = device_id
        
#         # Validate input
#         try:
#             device_info = DeviceMaintenanceInfo(**data)
#         except ValidationError as e:
#             return jsonify({
#                 'error': 'Invalid device data',
#                 'details': e.errors()
#             }), 400
        
#         # Call ML service
#         result = ml_service.predict_maintenance(device_info.dict())
#         print(f"✅ [Maintenance] ML result: {result}")
        
#         # Save to ml_predictions table
#         try:
#             supabase = get_supabase()
            
#             prediction = {
#                 'device_id': device_id,
#                 'prediction_type': 'maintenance',
#                 'needs_maintenance': result.get('needs_maintenance', False),
#                 'maintenance_confidence': result.get('probability', 0),
#                 'maintenance_priority': result.get('priority', 'low'),
#                 'days_until_maintenance': result.get('days_until', None)
#             }
            
#             print(f"💾 [Maintenance] Saving to DB: {prediction}")
#             db_result = supabase.table('ml_predictions').insert(prediction).execute()
#             print(f"✅ [Maintenance] Saved to DB successfully!")
            
#         except Exception as db_error:
#             print(f"❌ [Maintenance] Database save failed: {db_error}")
#             import traceback
#             traceback.print_exc()
        
#         # Return response
#         return jsonify({
#             'maintenance_needed': result.get('needs_maintenance', False),
#             'probability': float(result.get('probability', 0)),
#             'priority': result.get('priority', 'low'),
#             'days_until': result.get('days_until', 0),
#             'recommendations': result.get('recommendations', {}),
#             'message': result.get('message', ''),
#             'timestamp': int(time.time() * 1000)
#         }), 200
        
#     except RuntimeError as e:
#         return jsonify({'error': str(e)}), 503
#     except Exception as e:
#         print(f"❌ [Maintenance] Error: {e}")
#         import traceback
#         traceback.print_exc()
#         return jsonify({'error': f'Maintenance prediction failed: {str(e)}'}), 500


# # ========== OBJECT/OBSTACLE DETECTION ==========

# @ml_bp.route('/detect/object', methods=['POST'])
# @device_token_required  # ✅ CHANGED - RPi uses device token
# def detect_object():
#     """Detect and classify objects/obstacles"""
#     try:
#         device_id = request.current_device['id']  # ✅ CHANGED
#         data = request.get_json()
#         print(f"🔍 [Object Detection] Received data: {data}")
        
#         if not data:
#             return jsonify({'error': 'Missing detection data'}), 400
        
#         # ✅ CHANGED - Use device_id from auth context
#         data['device_id'] = device_id
        
#         # Validate input
#         try:
#             detection_request = ObjectDetectionRequest(**data)
#         except ValidationError as e:
#             return jsonify({
#                 'error': 'Invalid detection data',
#                 'details': e.errors()
#             }), 400
        
#         # Call ML service
#         result = ml_service.detect_object(detection_request.dict())
#         print(f"✅ [Object Detection] Result: {result}")
        
#         # Save to database
#         try:
#             supabase = get_supabase()
            
#             prediction = {
#                 'device_id': device_id,
#                 'prediction_type': 'object_detection',
#                 'object_detected': result.get('object_detected'),
#                 'distance_cm': result.get('distance_cm'),
#                 'danger_level': result.get('danger_level'),
#                 'detection_confidence': result.get('detection_confidence'),
#                 'is_anomaly': result.get('danger_level') in ['High', 'Critical']
#             }
            
#             print(f"💾 [Object Detection] Saving to DB: {prediction}")
#             db_result = supabase.table('ml_predictions').insert(prediction).execute()
#             print(f"✅ [Object Detection] Saved successfully!")
            
#         except Exception as db_error:
#             print(f"❌ [Object Detection] Database save failed: {db_error}")
#             import traceback
#             traceback.print_exc()
        
#         # Return response
#         return jsonify({
#             'object_detected': result.get('object_detected'),
#             'distance_cm': result.get('distance_cm'),
#             'danger_level': result.get('danger_level'),
#             'detection_confidence': result.get('detection_confidence'),
#             'message': result.get('message'),
#             'timestamp': int(time.time() * 1000)
#         }), 200
        
#     except Exception as e:
#         print(f"❌ [Object Detection] Error: {e}")
#         import traceback
#         traceback.print_exc()
#         return jsonify({'error': 'Object detection failed'}), 500


# # ========== DANGER PREDICTION (NEW) ==========

# @ml_bp.route('/predict/danger', methods=['POST'])
# @device_token_required  # ✅ CHANGED - RPi uses device token
# def predict_danger():
#     """Predict danger level and recommend action"""
#     try:
#         device_id = request.current_device['id']  # ✅ CHANGED
#         data = request.get_json()
#         print(f"🔍 [Danger Prediction] Received data: {data}")
        
#         if not data:
#             return jsonify({'error': 'Missing danger data'}), 400
        
#         # ✅ CHANGED - Use device_id from auth context
#         data['device_id'] = device_id
        
#         # Validate input
#         try:
#             danger_request = DangerPredictionRequest(**data)
#         except ValidationError as e:
#             return jsonify({
#                 'error': 'Invalid danger data',
#                 'details': e.errors()
#             }), 400
        
#         # Call ML service
#         result = ml_service.predict_danger(danger_request.dict())
#         print(f"✅ [Danger Prediction] Result: {result}")
        
#         # Save to database
#         try:
#             supabase = get_supabase()
            
#             prediction = {
#                 'device_id': device_id,
#                 'prediction_type': 'danger_prediction',
#                 'danger_score': result.get('danger_score'),
#                 'recommended_action': result.get('recommended_action'),
#                 'time_to_collision': result.get('time_to_collision'),
#                 'is_anomaly': result.get('danger_score', 0) > 70
#             }
            
#             print(f"💾 [Danger Prediction] Saving to DB: {prediction}")
#             db_result = supabase.table('ml_predictions').insert(prediction).execute()
#             print(f"✅ [Danger Prediction] Saved successfully!")
            
#         except Exception as db_error:
#             print(f"❌ [Danger Prediction] Database save failed: {db_error}")
#             import traceback
#             traceback.print_exc()
        
#         # Return response
#         return jsonify({
#             'danger_score': result.get('danger_score'),
#             'recommended_action': result.get('recommended_action'),
#             'time_to_collision': result.get('time_to_collision'),
#             'confidence': result.get('confidence'),
#             'message': result.get('message'),
#             'timestamp': int(time.time() * 1000)
#         }), 200
        
#     except Exception as e:
#         print(f"❌ [Danger Prediction] Error: {e}")
#         import traceback
#         traceback.print_exc()
#         return jsonify({'error': 'Danger prediction failed'}), 500


# # ========== ENVIRONMENT CLASSIFICATION (NEW) ==========

# @ml_bp.route('/classify/environment', methods=['POST'])
# @device_token_required  # ✅ CHANGED - RPi uses device token
# def classify_environment():
#     """Classify environment type based on sensor patterns"""
#     try:
#         device_id = request.current_device['id']  # ✅ CHANGED
#         data = request.get_json()
#         print(f"🔍 [Environment] Received data: {data}")
        
#         if not data:
#             return jsonify({'error': 'Missing environment data'}), 400
        
#         # ✅ CHANGED - Use device_id from auth context
#         data['device_id'] = device_id
        
#         # Validate input
#         try:
#             env_request = EnvironmentClassificationRequest(**data)
#         except ValidationError as e:
#             return jsonify({
#                 'error': 'Invalid environment data',
#                 'details': e.errors()
#             }), 400
        
#         # Call ML service
#         result = ml_service.classify_environment(env_request.dict())
#         print(f"✅ [Environment] Result: {result}")
        
#         # Save to database
#         try:
#             supabase = get_supabase()
            
#             prediction = {
#                 'device_id': device_id,
#                 'prediction_type': 'environment_classification',
#                 'environment_type': result.get('environment_type'),
#                 'lighting_condition': result.get('lighting_condition'),
#                 'complexity_level': result.get('complexity_level'),
#                 'is_anomaly': False
#             }
            
#             print(f"💾 [Environment] Saving to DB: {prediction}")
#             db_result = supabase.table('ml_predictions').insert(prediction).execute()
#             print(f"✅ [Environment] Saved successfully!")
            
#         except Exception as db_error:
#             print(f"❌ [Environment] Database save failed: {db_error}")
#             import traceback
#             traceback.print_exc()
        
#         # Return response
#         return jsonify({
#             'environment_type': result.get('environment_type'),
#             'lighting_condition': result.get('lighting_condition'),
#             'complexity_level': result.get('complexity_level'),
#             'confidence': result.get('confidence'),
#             'message': result.get('message'),
#             'timestamp': int(time.time() * 1000)
#         }), 200
        
#     except Exception as e:
#         print(f"❌ [Environment] Error: {e}")
#         import traceback
#         traceback.print_exc()
#         return jsonify({'error': 'Environment classification failed'}), 500


# # ========== Aliases for frontend compatibility ==========
# # NOTE: These use @token_required because they're called by the dashboard, not RPi

# from app.middleware.auth import token_required

# @ml_bp.route('/anomaly-detection', methods=['POST'])
# @token_required  # ✅ Dashboard uses user token
# def detect_anomaly_alias():
#     """Alias for /detect/anomaly to match frontend"""
#     return detect_anomaly()


# @ml_bp.route('/maintenance-prediction', methods=['POST'])
# @token_required  # ✅ Dashboard uses user token
# def predict_maintenance_alias():
#     """Alias for /predict/maintenance to match frontend"""
#     return predict_maintenance()