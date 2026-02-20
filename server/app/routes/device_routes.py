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
        "usage_hours": 8
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
        
        # ========== ANOMALY DETECTION ==========
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