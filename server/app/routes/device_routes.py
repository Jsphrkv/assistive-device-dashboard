from flask import Blueprint, current_app, request, jsonify
from app.services.supabase_client import get_supabase
from datetime import datetime
from app.utils.timezone_helper import now_ph, now_ph_iso, PH_TIMEZONE

device_bp = Blueprint('device', __name__, url_prefix='/api/device')

print("✅ device_routes.py loaded successfully!")


def _detect_anomaly_rules(telemetry: dict) -> dict:
    """
    Lightweight rule-based anomaly detection.
    Replaces the ML model until HuggingFace inference is integrated.
    """
    temperature     = telemetry.get('temperature', 37.0)
    heart_rate      = telemetry.get('heart_rate', 75.0)
    battery_level   = telemetry.get('battery_level', 80.0)
    signal_strength = telemetry.get('signal_strength', -50.0)
    usage_hours     = telemetry.get('usage_hours', 8.0)

    flags = []

    if temperature < 35.0 or temperature > 39.5:
        flags.append(f"temperature out of range ({temperature}°C)")
    if heart_rate < 40 or heart_rate > 140:
        flags.append(f"heart rate out of range ({heart_rate} bpm)")
    if battery_level < 10:
        flags.append(f"battery critically low ({battery_level}%)")
    if signal_strength < -90:
        flags.append(f"weak signal ({signal_strength} dBm)")
    if usage_hours > 20:
        flags.append(f"excessive usage hours ({usage_hours}h)")

    is_anomaly    = len(flags) > 0
    anomaly_score = min(1.0, len(flags) * 0.25)

    if anomaly_score > 0.6:
        severity = 'high'
    elif anomaly_score > 0.3:
        severity = 'medium'
    else:
        severity = 'low'

    message = (
        f"Anomaly detected: {'; '.join(flags)}"
        if is_anomaly
        else "Normal operation"
    )
    device_health_score = round(100 * (1 - anomaly_score), 1)

    return {
        'is_anomaly':          is_anomaly,
        'anomaly_score':       anomaly_score,
        'confidence':          anomaly_score if is_anomaly else round(1 - anomaly_score, 2),
        'severity':            severity,
        'device_health_score': device_health_score,
        'message':             message
    }


@device_bp.route('/telemetry', methods=['POST'])
def receive_telemetry():
    """
    Receive telemetry data from IoT devices.
    Called BY DEVICES, not the frontend.

    Expected payload:
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
        print(f"\n🔍 [ANOMALY] Running rule-based anomaly detection...")
        try:
            telemetry = {
                'temperature':      data.get('temperature', 37.0),
                'heart_rate':       data.get('heart_rate', 75.0),
                'battery_level':    data.get('battery_level', 80.0),
                'signal_strength':  data.get('signal_strength', -50.0),
                'usage_hours':      data.get('usage_hours', 8.0)
            }

            anomaly_result = _detect_anomaly_rules(telemetry)
            results['anomaly'] = anomaly_result

            print(f"   Result: {anomaly_result}")

            prediction = {
                'device_id':        device_id,
                'prediction_type':  'anomaly',
                'is_anomaly':       anomaly_result.get('is_anomaly', False),
                'anomaly_score':    anomaly_result.get('anomaly_score', 0),
                'anomaly_severity': anomaly_result.get('severity', 'low'),
                'anomaly_message':  anomaly_result.get('message', ''),
                'telemetry_data':   telemetry,
                'model_version':    'rules-v1.0'
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

        # ✅ FIXED: Use Philippine time
        return jsonify({
            'success':     True,
            'message':     'Telemetry received and processed',
            'device_id':   device_id,
            'predictions': results,
            'timestamp':   now_ph_iso()
        }), 200

    except Exception as e:
        print(f"\n❌ [TELEMETRY] Error processing telemetry: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error':   'Failed to process telemetry',
            'details': str(e)
        }), 500


@device_bp.route('/ping', methods=['GET'])
def ping():
    """Simple endpoint to check if device API is working"""
    # ✅ FIXED: Use Philippine time
    return jsonify({
        'success':   True,
        'message':   'Device API is working',
        'timestamp': now_ph_iso()
    }), 200