from flask import Blueprint, request, jsonify
from app.services.supabase_client import get_supabase
from app.services.ml_service import ml_service
from datetime import datetime, timezone

device_bp = Blueprint('device', __name__, url_prefix='/api/device')

print("✅ device_routes.py loaded successfully!")

@device_bp.route('/telemetry', methods=['POST'])
def receive_telemetry():
    """
    Receive telemetry data from IoT devices
    This endpoint is called BY DEVICES, not the frontend
    
    Expected data:
    {
        "device_id": "device_123",
        "temperature": 37.5,
        "heart_rate": 75,
        "battery_level": 80,
        "signal_strength": -50,
        "usage_hours": 8,
        "accel_x": 0.1,
        "accel_y": 0.2,
        "accel_z": 0.3,
        "gyro_x": 0.05,
        "gyro_y": 0.02,
        "gyro_z": 0.01
    }
    """
    try:
        data = request.get_json()
        print(f"\n📡 [TELEMETRY] Received data from device")
        print(f"   Device ID: {data.get('device_id')}")
        print(f"   Data: {data}")
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        device_id = data.get('device_id')
        if not device_id:
            return jsonify({'error': 'device_id is required'}), 400
        
        supabase = get_supabase()
        results = {}
        
        # ========== 1. ANOMALY DETECTION ==========
        print(f"\n🔍 [ANOMALY] Running anomaly detection...")
        try:
            telemetry = {
                'temperature': data.get('temperature', 37.0),
                'heart_rate': data.get('heart_rate', 75.0),
                'battery_level': data.get('battery_level', 80.0),
                'signal_strength': data.get('signal_strength', -50.0),
                'usage_hours': data.get('usage_hours', 8.0)
            }
            
            anomaly_result = ml_service.detect_anomaly(telemetry)
            results['anomaly'] = anomaly_result
            
            print(f"   Result: {anomaly_result}")
            
            # Save to database
            prediction = {
                'device_id': device_id,
                'prediction_type': 'anomaly',
                'is_anomaly': anomaly_result.get('is_anomaly', False),
                'anomaly_score': anomaly_result.get('anomaly_score', 0),
                'anomaly_severity': anomaly_result.get('severity', 'low'),
                'anomaly_message': anomaly_result.get('message', ''),
                'telemetry_data': telemetry,
                'model_version': 'v1.0'
            }
            
            print(f"💾 [ANOMALY] Saving to database...")
            db_result = supabase.table('ml_predictions').insert(prediction).execute()
            
            if db_result.data:
                print(f"✅ [ANOMALY] Saved! ID: {db_result.data[0].get('id')}")
            else:
                print(f"⚠️ [ANOMALY] No data returned from insert")
                
        except Exception as e:
            print(f"❌ [ANOMALY] Error: {e}")
            import traceback
            traceback.print_exc()
            results['anomaly'] = {'error': str(e)}
        
        # ========== 2. ACTIVITY RECOGNITION ==========
        print(f"\n🏃 [ACTIVITY] Running activity recognition...")
        try:
            sensor_data = {
                'accelerometer_x': data.get('accel_x', 0.0),
                'accelerometer_y': data.get('accel_y', 0.0),
                'accelerometer_z': data.get('accel_z', 0.0),
                'gyroscope_x': data.get('gyro_x', 0.0),
                'gyroscope_y': data.get('gyro_y', 0.0),
                'gyroscope_z': data.get('gyro_z', 0.0)
            }
            
            activity_result = ml_service.recognize_activity(sensor_data)
            results['activity'] = activity_result
            
            print(f"   Result: {activity_result}")
            
            # Save to database
            prediction = {
                'device_id': device_id,
                'prediction_type': 'activity',
                'detected_activity': activity_result.get('activity', ''),
                'activity_confidence': activity_result.get('confidence', 0),
                'activity_intensity': activity_result.get('intensity', 'low'),
                'activity_probabilities': activity_result.get('probabilities', {}),
                'sensor_data': sensor_data,
                'model_version': 'v1.0'
            }
            
            print(f"💾 [ACTIVITY] Saving to database...")
            db_result = supabase.table('ml_predictions').insert(prediction).execute()
            
            if db_result.data:
                print(f"✅ [ACTIVITY] Saved! ID: {db_result.data[0].get('id')}")
            else:
                print(f"⚠️ [ACTIVITY] No data returned from insert")
                
        except Exception as e:
            print(f"❌ [ACTIVITY] Error: {e}")
            import traceback
            traceback.print_exc()
            results['activity'] = {'error': str(e)}
        
        # ========== 3. MAINTENANCE PREDICTION ==========
        # Only check maintenance periodically (not every telemetry)
        should_check_maintenance = data.get('check_maintenance', False)
        
        if should_check_maintenance:
            print(f"\n🔧 [MAINTENANCE] Running maintenance prediction...")
            try:
                device_info = {
                    'battery_health': data.get('battery_health', 80.0),
                    'charge_cycles': data.get('charge_cycles', 100),
                    'temperature_avg': data.get('temperature', 37.0),
                    'error_count': data.get('error_count', 0),
                    'uptime_days': data.get('uptime_days', 30)
                }
                
                maintenance_result = ml_service.predict_maintenance(device_info)
                results['maintenance'] = maintenance_result
                
                print(f"   Result: {maintenance_result}")
                
                # Save to database
                prediction = {
                    'device_id': device_id,
                    'prediction_type': 'maintenance',
                    'needs_maintenance': maintenance_result.get('needs_maintenance', False),
                    'maintenance_confidence': maintenance_result.get('probability', 0),
                    'maintenance_priority': maintenance_result.get('priority', 'low'),
                    'maintenance_recommendations': maintenance_result.get('recommendations', {}),
                    'telemetry_data': device_info,
                    'model_version': 'v1.0'
                }
                
                print(f"💾 [MAINTENANCE] Saving to database...")
                db_result = supabase.table('ml_predictions').insert(prediction).execute()
                
                if db_result.data:
                    print(f"✅ [MAINTENANCE] Saved! ID: {db_result.data[0].get('id')}")
                else:
                    print(f"⚠️ [MAINTENANCE] No data returned from insert")
                    
            except Exception as e:
                print(f"❌ [MAINTENANCE] Error: {e}")
                import traceback
                traceback.print_exc()
                results['maintenance'] = {'error': str(e)}
        
        print(f"\n✅ Telemetry processed successfully for device {device_id}\n")
        
        return jsonify({
            'success': True,
            'message': 'Telemetry received and processed',
            'device_id': device_id,
            'predictions': results,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 200
        
    except Exception as e:
        print(f"\n❌ [TELEMETRY] Error processing telemetry: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': 'Failed to process telemetry',
            'details': str(e)
        }), 500


@device_bp.route('/ping', methods=['GET'])
def ping():
    """Simple endpoint to check if device API is working"""
    return jsonify({
        'success': True,
        'message': 'Device API is working',
        'timestamp': datetime.now(timezone.utc).isoformat()
    }), 200