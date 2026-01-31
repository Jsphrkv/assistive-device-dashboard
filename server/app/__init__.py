# from flask import Flask, app, request
# from flask_cors import CORS
# from app.config import config
# import os
# from app.ml_models.model_loader import model_loader

# def create_app(config_name=None):
#     """Application factory pattern"""
#     if config_name is None:
#         config_name = os.getenv('FLASK_ENV', 'development')
    
#     app = Flask(__name__)

#     app.config.from_object('app.config.Config')
    
#     # Initialize CORS
#     CORS(app, 
#          origins=[
#              "https://assistive-device-dashboard.vercel.app",
#              "http://localhost:3000",
#              "http://localhost:5173"
#          ],
#          methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
#          allow_headers=["Content-Type", "Authorization", "X-Device-Token"],
#          supports_credentials=True,
#          max_age=3600)

#     # # Initialize Flask-Mail ✅ NEW
#     # init_mail(app)

#     print("="*60)
#     print("📧 SENDGRID CONFIGURATION:")
#     print(f"API KEY: {'✅ SET' if app.config.get('SENDGRID_API_KEY') else '❌ NOT SET'}")
#     print(f"FROM EMAIL: {app.config.get('MAIL_DEFAULT_SENDER')}")
#     print(f"FRONTEND URL: {app.config.get('FRONTEND_URL')}")
#     print("="*60)

#      # Try to load ML models (don't crash if fails)
#     try:
#         from app.ml_models.model_loader import model_loader
#         print("ML models initialization attempted")
#     except Exception as e:
#         print(f"⚠ ML models not loaded: {e}")
#         print("  API will use fallback predictions")
    
#     # Register blueprints
#     from app.routes.auth import auth_bp
#     from app.routes.devices import devices_bp     
#     from app.routes.device_routes import device_bp
#     from app.routes.detections import detections_bp
#     from app.routes.ml_routes import ml_bp
#     from app.routes.statistics import statistics_bp
#     from app.routes.settings import settings_bp
    
    
#     app.register_blueprint(auth_bp, url_prefix='/api/auth')
#     app.register_blueprint(devices_bp, url_prefix='/api/devices') 
#     app.register_blueprint(device_bp, url_prefix='/api/device')
#     app.register_blueprint(detections_bp, url_prefix='/api/detections')
#     app.register_blueprint(ml_bp, url_prefix='/api/ml')
#     app.register_blueprint(statistics_bp, url_prefix='/api/statistics')
#     app.register_blueprint(settings_bp, url_prefix='/api/settings')

#     @app.before_request
#     def handle_preflight():
#         if request.method == "OPTIONS":
#             response = app.make_default_options_response()
#             response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
#             response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
#             response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Device-Token'
#             response.headers['Access-Control-Allow-Credentials'] = 'true'
#             return response

#     @app.after_request
#     def after_request(response):
#         origin = request.headers.get('Origin')
#         if origin in [
#             "https://assistive-device-dashboard.vercel.app",
#             "http://localhost:3000",
#             "http://localhost:5173"
#         ]:
#             response.headers['Access-Control-Allow-Origin'] = origin
#             response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
#             response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Device-Token'
#             response.headers['Access-Control-Allow-Credentials'] = 'true'
#         return response

#     # Health check endpoint
#     @app.route('/health')
#     def health_check():
#         return {'status': 'healthy', 'message': 'Assistive Device API is running'}, 200
    
#     # Error handlers
#     @app.errorhandler(404)
#     def not_found(error):
#         return {'error': 'Not found'}, 404
    
#     @app.errorhandler(500)
#     def internal_error(error):
#         return {'error': 'Internal server error'}, 500
    
#     return app

# app = create_app()

# if __name__ == '__main__':
#     app.run(debug=True, host='0.0.0.0', port=5000)

from flask import Blueprint, request, jsonify
from app.services.supabase_client import get_supabase
from app.middleware.auth import token_required, device_token_required, admin_required, check_permission
from app.utils.jwt_handler import generate_device_token
import secrets

devices_bp = Blueprint('devices', __name__, url_prefix='/api/devices')

# ============================================
# DEVICE MANAGEMENT (User-facing)
# ============================================

@devices_bp.route('', methods=['GET'])  # ✅ Removed trailing slash
@token_required
def get_user_devices():
    """Get all devices for current user with their status"""
    try:
        user_id = request.current_user['user_id']
        user_role = request.current_user['role']

        supabase = get_supabase()

        if user_role == 'admin':
            response = supabase.table('user_devices')\
                .select('*, users(username, email)')\
                .order('created_at', desc=True)\
                .execute()
        else:
            response = supabase.table('user_devices')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .execute()

        devices = response.data
        for device in devices:
            if device.get('status') == 'active':
                status_response = supabase.table('device_status')\
                    .select('*')\
                    .eq('device_id', device['id'])\
                    .order('updated_at', desc=True)\
                    .limit(1)\
                    .execute()
                if status_response.data:
                    device['current_status'] = status_response.data[0]

        return jsonify({'data': devices}), 200

    except Exception as e:
        print(f"Get devices error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to get devices'}), 500


@devices_bp.route('', methods=['POST'])  # ✅ Removed trailing slash
@token_required
def register_device():
    """Register a new device for user"""
    try:
        user_id = request.current_user['user_id']
        data = request.get_json()

        if not data or not data.get('deviceName'):
            return jsonify({'error': 'Device name is required'}), 400

        device_name = data['deviceName']
        device_model = data.get('deviceModel', 'Raspberry Pi')

        device_token = generate_device_token(f"{user_id}-{device_name}")

        supabase = get_supabase()

        existing = supabase.table('user_devices')\
            .select('*', count='exact')\
            .eq('user_id', user_id)\
            .execute()

        if existing.count >= 1:
            return jsonify({
                'error': 'You can only register one device per account. Please delete your existing device first.'
            }), 400

        new_device = {
            'user_id': user_id,
            'device_name': device_name,
            'device_model': device_model,
            'device_token': device_token,
            'status': 'pending'
        }

        response = supabase.table('user_devices').insert(new_device).execute()

        if not response.data:
            return jsonify({'error': 'Failed to register device'}), 500

        device = response.data[0]

        supabase.table('activity_logs').insert({
            'user_id': user_id,
            'action': 'Device Registered',
            'description': f'Registered device: {device_name}'
        }).execute()

        return jsonify({
            'message': 'Device registered successfully',
            'device': {
                'id': device['id'],
                'name': device['device_name'],
                'model': device['device_model'],
                'token': device['device_token'],
                'status': device['status']
            }
        }), 201

    except Exception as e:
        print(f"Register device error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to register device'}), 500


@devices_bp.route('/<device_id>', methods=['PUT'])  # ✅ Fixed route
@token_required
def update_device(device_id):
    """Update device details"""
    try:
        user_id = request.current_user['user_id']
        user_role = request.current_user['role']
        data = request.get_json()

        supabase = get_supabase()

        device = supabase.table('user_devices')\
            .select('*')\
            .eq('id', device_id)\
            .execute()

        if not device.data:
            return jsonify({'error': 'Device not found'}), 404

        if device.data[0]['user_id'] != user_id and user_role != 'admin':
            return jsonify({'error': 'Permission denied'}), 403

        update_data = {'updated_at': 'now()'}
        if 'deviceName' in data:
            update_data['device_name'] = data['deviceName']
        if 'deviceModel' in data:
            update_data['device_model'] = data['deviceModel']
        if 'isActive' in data:
            update_data['is_active'] = data['isActive']

        response = supabase.table('user_devices')\
            .update(update_data)\
            .eq('id', device_id)\
            .execute()

        return jsonify({
            'message': 'Device updated successfully',
            'data': response.data
        }), 200

    except Exception as e:
        print(f"Update device error: {e}")
        return jsonify({'error': 'Failed to update device'}), 500


@devices_bp.route('/<device_id>', methods=['DELETE'])  # ✅ Fixed route
@token_required
def delete_device(device_id):
    """Delete/unregister a device"""
    try:
        user_id = request.current_user['user_id']
        user_role = request.current_user['role']

        supabase = get_supabase()

        device = supabase.table('user_devices')\
            .select('*')\
            .eq('id', device_id)\
            .execute()

        if not device.data:
            return jsonify({'error': 'Device not found'}), 404

        if device.data[0]['user_id'] != user_id and user_role != 'admin':
            return jsonify({'error': 'Permission denied'}), 403

        supabase.table('user_devices').delete().eq('id', device_id).execute()

        supabase.table('activity_logs').insert({
            'user_id': user_id,
            'action': 'Device Deleted',
            'description': f'Deleted device: {device.data[0]["device_name"]}'
        }).execute()

        return jsonify({'message': 'Device deleted successfully'}), 200

    except Exception as e:
        print(f"Delete device error: {e}")
        return jsonify({'error': 'Failed to delete device'}), 500


@devices_bp.route('/<device_id>/regenerate-token', methods=['POST'])  # ✅ Fixed route
@token_required
def regenerate_device_token(device_id):
    """Regenerate device token (if compromised)"""
    try:
        user_id = request.current_user['user_id']
        user_role = request.current_user['role']

        supabase = get_supabase()

        device = supabase.table('user_devices')\
            .select('*')\
            .eq('id', device_id)\
            .execute()

        if not device.data:
            return jsonify({'error': 'Device not found'}), 404

        if device.data[0]['user_id'] != user_id and user_role != 'admin':
            return jsonify({'error': 'Permission denied'}), 403

        new_token = generate_device_token(f"{user_id}-{device.data[0]['device_name']}-{secrets.token_hex(4)}")

        response = supabase.table('user_devices')\
            .update({
                'device_token': new_token,
                'status': 'pending',
                'updated_at': 'now()'
            })\
            .eq('id', device_id)\
            .execute()

        return jsonify({
            'message': 'Token regenerated successfully',
            'token': new_token
        }), 200

    except Exception as e:
        print(f"Regenerate token error: {e}")
        return jsonify({'error': 'Failed to regenerate token'}), 500


# ============================================
# DEVICE STATUS (Runtime data)
# ============================================

@devices_bp.route('/status', methods=['GET'])  # ✅ No trailing slash
@token_required
def get_device_status():
    """Get current device status (for dashboard)"""
    try:
        user_id = request.current_user['user_id']
        supabase = get_supabase()

        device = supabase.table('user_devices')\
            .select('*')\
            .eq('user_id', user_id)\
            .eq('status', 'active')\
            .limit(1)\
            .execute()

        if not device.data:
            return jsonify({
                'deviceOnline': False,
                'cameraStatus': 'offline',
                'batteryLevel': 0,
                'lastObstacle': None,
                'lastDetectionTime': None,
                'hasDevice': False,
                'message': 'No active device registered'
            }), 200

        device_id = device.data[0]['id']

        response = supabase.table('device_status')\
            .select('*')\
            .eq('device_id', device_id)\
            .order('updated_at', desc=True)\
            .limit(1)\
            .execute()

        if not response.data:
            return jsonify({
                'deviceOnline': False,
                'cameraStatus': 'offline',
                'batteryLevel': 0,
                'lastObstacle': None,
                'lastDetectionTime': None,
                'hasDevice': True,
                'message': 'Device registered but no status data yet'
            }), 200

        status = response.data[0]

        return jsonify({
            'deviceOnline': status.get('device_online', False),
            'cameraStatus': status.get('camera_status', 'offline'),
            'batteryLevel': status.get('battery_level', 0),
            'lastObstacle': status.get('last_obstacle'),
            'lastDetectionTime': status.get('last_detection_time'),
            'hasDevice': True
        }), 200

    except Exception as e:
        print(f"Get device status error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to get device status'}), 500


@devices_bp.route('/status', methods=['POST'])
@device_token_required
def update_device_status():
    """Update device status (called by Raspberry Pi)"""
    try:
        device_id = request.current_device['id']
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        supabase = get_supabase()

        update_data = {
            'device_id': device_id,
            'updated_at': 'now()'
        }

        if 'deviceOnline' in data:
            update_data['device_online'] = data['deviceOnline']
        if 'cameraStatus' in data:
            update_data['camera_status'] = data['cameraStatus']
        if 'batteryLevel' in data:
            update_data['battery_level'] = data['batteryLevel']
        if 'lastObstacle' in data:
            update_data['last_obstacle'] = data['lastObstacle']
        if 'lastDetectionTime' in data:
            update_data['last_detection_time'] = data['lastDetectionTime']

        existing = supabase.table('device_status')\
            .select('id')\
            .eq('device_id', device_id)\
            .limit(1)\
            .execute()

        if existing.data and len(existing.data) > 0:
            status_id = existing.data[0]['id']
            response = supabase.table('device_status')\
                .update(update_data)\
                .eq('id', status_id)\
                .execute()
        else:
            response = supabase.table('device_status').insert(update_data).execute()

        return jsonify({'message': 'Device status updated', 'data': response.data}), 200

    except Exception as e:
        print(f"Update device status error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to update device status'}), 500


# ============================================
# SYSTEM INFO (Hardware details)
# ============================================

@devices_bp.route('/system-info', methods=['GET'])
@token_required
def get_system_info():
    """Get system information for user's device"""
    try:
        user_id = request.current_user['user_id']
        supabase = get_supabase()

        device = supabase.table('user_devices')\
            .select('*')\
            .eq('user_id', user_id)\
            .eq('status', 'active')\
            .limit(1)\
            .execute()

        if not device.data:
            return jsonify({'error': 'No active device found'}), 404

        device_id = device.data[0]['id']

        response = supabase.table('system_info')\
            .select('*')\
            .eq('device_id', device_id)\
            .limit(1)\
            .execute()

        if not response.data:
            return jsonify({'error': 'No system info found'}), 404

        info = response.data[0]

        return jsonify({
            'raspberryPiModel': info.get('raspberry_pi_model'),
            'softwareVersion': info.get('software_version'),
            'lastRebootTime': info.get('last_reboot_time'),
            'cpuTemperature': info.get('cpu_temperature'),
            'cpuModel': info.get('cpu_model'),
            'ramSize': info.get('ram_size'),
            'storageSize': info.get('storage_size'),
            'osVersion': info.get('os_version')
        }), 200

    except Exception as e:
        print(f"Get system info error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to get system info'}), 500


@devices_bp.route('/system-info/temperature', methods=['POST'])
@device_token_required
def update_temperature():
    """Update CPU temperature (called by Raspberry Pi)"""
    try:
        device_id = request.current_device['id']
        data = request.get_json()

        if not data or 'temperature' not in data:
            return jsonify({'error': 'Temperature is required'}), 400

        supabase = get_supabase()

        response = supabase.table('system_info')\
            .update({
                'cpu_temperature': data['temperature'],
                'updated_at': 'now()'
            })\
            .eq('device_id', device_id)\
            .execute()

        return jsonify({'message': 'Temperature updated'}), 200

    except Exception as e:
        print(f"Update temperature error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to update temperature'}), 500