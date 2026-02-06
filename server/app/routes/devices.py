from flask import Blueprint, request, jsonify
from app.services.supabase_client import get_supabase
from app.middleware.auth import token_required, device_token_required, admin_required, check_permission
from app.utils.jwt_handler import generate_device_token
import secrets

devices_bp = Blueprint('devices', __name__, url_prefix='/api/devices')

# ============================================
# DEVICE MANAGEMENT (User-facing)
# ============================================

@devices_bp.route('/', methods=['GET'])
@token_required
def get_user_devices():
    """Get all devices for current user with their status"""
    try:
        user_id = request.current_user['user_id']
        user_role = request.current_user['role']
        
        supabase = get_supabase()
        
        # Admins can see all devices, users only see their own
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
        
        # Enrich with current status from device_status table
        devices = response.data
        for device in devices:
            # Get latest status for this device if it's active
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

@devices_bp.route('/', methods=['POST'])
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
        
        # Generate unique device token
        device_token = generate_device_token(f"{user_id}-{device_name}")
        
        supabase = get_supabase()
        
        # Check device limit (max 5 devices per user)
        existing = supabase.table('user_devices')\
            .select('*', count='exact')\
            .eq('user_id', user_id)\
            .execute()
        
        if existing.count >= 1:
            return jsonify({
                'error': 'You can only register one device per account. Please delete your existing device first.'
            }), 400
        
        # Create device
        new_device = {
            'user_id': user_id,
            'device_name': device_name,
            'device_model': device_model,
            'device_token': device_token,
            'status': 'pending'  # Waiting for Pi to connect
        }
        
        response = supabase.table('user_devices').insert(new_device).execute()
        
        if not response.data:
            return jsonify({'error': 'Failed to register device'}), 500
        
        device = response.data[0]
        
        # Log activity
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

@devices_bp.route('/<device_id>', methods=['PUT'])
@token_required
def update_device(device_id):
    """Update device details"""
    try:
        user_id = request.current_user['user_id']
        user_role = request.current_user['role']
        data = request.get_json()
        
        supabase = get_supabase()
        
        # Check ownership
        device = supabase.table('user_devices')\
            .select('*')\
            .eq('id', device_id)\
            .single()\
            .execute()
        
        if not device.data:
            return jsonify({'error': 'Device not found'}), 404
        
        if device.data['user_id'] != user_id and user_role != 'admin':
            return jsonify({'error': 'Permission denied'}), 403
        
        # Update device
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

@devices_bp.route('/<device_id>', methods=['DELETE'])
@token_required
def delete_device(device_id):
    """Delete/unregister a device"""
    try:
        user_id = request.current_user['user_id']
        user_role = request.current_user['role']
        
        supabase = get_supabase()
        
        # Check ownership
        device = supabase.table('user_devices')\
            .select('*')\
            .eq('id', device_id)\
            .single()\
            .execute()
        
        if not device.data:
            return jsonify({'error': 'Device not found'}), 404
        
        if device.data['user_id'] != user_id and user_role != 'admin':
            return jsonify({'error': 'Permission denied'}), 403
        
        # Delete device
        supabase.table('user_devices').delete().eq('id', device_id).execute()
        
        # Log activity
        supabase.table('activity_logs').insert({
            'user_id': user_id,
            'action': 'Device Deleted',
            'description': f'Deleted device: {device.data["device_name"]}'
        }).execute()
        
        return jsonify({'message': 'Device deleted successfully'}), 200
        
    except Exception as e:
        print(f"Delete device error: {e}")
        return jsonify({'error': 'Failed to delete device'}), 500

@devices_bp.route('/<device_id>/regenerate-token', methods=['POST'])
@token_required
def regenerate_device_token(device_id):
    """Regenerate device token (if compromised)"""
    try:
        user_id = request.current_user['user_id']
        user_role = request.current_user['role']
        
        supabase = get_supabase()
        
        # Check ownership
        device = supabase.table('user_devices')\
            .select('*')\
            .eq('id', device_id)\
            .single()\
            .execute()
        
        if not device.data:
            return jsonify({'error': 'Device not found'}), 404
        
        if device.data['user_id'] != user_id and user_role != 'admin':
            return jsonify({'error': 'Permission denied'}), 403
        
        # Generate new token
        new_token = generate_device_token(f"{user_id}-{device.data['device_name']}-{secrets.token_hex(4)}")
        
        # Update device
        response = supabase.table('user_devices')\
            .update({
                'device_token': new_token,
                'status': 'pending',  # Reset to pending
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

@devices_bp.route('/status', methods=['GET'])
@token_required
@check_permission('device', 'read')
def get_device_status():
    """Get current device status (for dashboard)"""
    try:
        user_id = request.current_user['user_id']
        supabase = get_supabase()
        
        # Get user's active device
        device = supabase.table('user_devices')\
            .select('*')\
            .eq('user_id', user_id)\
            .eq('status', 'active')\
            .limit(1)\
            .execute()
        
        if not device.data:
            # Return default empty status instead of 404
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
        
        # Get latest status
        response = supabase.table('device_status')\
            .select('*')\
            .eq('device_id', device_id)\
            .order('updated_at', desc=True)\
            .limit(1)\
            .execute()
        
        if not response.data:
            # Return default status for registered device without status data
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
        
        # Prepare update data
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
        
        # Check if a status row exists for this device
        existing = supabase.table('device_status')\
            .select('id')\
            .eq('device_id', device_id)\
            .limit(1)\
            .execute()
        
        if existing.data and len(existing.data) > 0:
            # Update existing row
            status_id = existing.data[0]['id']
            response = supabase.table('device_status')\
                .update(update_data)\
                .eq('id', status_id)\
                .execute()
        else:
            # Insert new row
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
@check_permission('system', 'read')
def get_system_info():
    """Get system information for user's device"""
    try:
        user_id = request.current_user['user_id']
        supabase = get_supabase()
        
        # Get user's active device
        device = supabase.table('user_devices')\
            .select('*')\
            .eq('user_id', user_id)\
            .eq('status', 'active')\
            .limit(1)\
            .execute()
        
        if not device.data:
            return jsonify({'error': 'No active device found'}), 404
        
        device_id = device.data[0]['id']
        
        # Get system info for this device
        response = supabase.table('system_info')\
            .select('*')\
            .eq('device_id', device_id)\
            .limit(1)\
            .execute()
        
        if not response.data:
            return jsonify({'error': 'No system info found'}), 404
        
        info = response.data[0]
        
        return jsonify({
            'raspberryPiModel': info['raspberry_pi_model'],
            'softwareVersion': info['software_version'],
            'lastRebootTime': info['last_reboot_time'],
            'cpuTemperature': info['cpu_temperature'],
            'cpuModel': info['cpu_model'],
            'ramSize': info['ram_size'],
            'storageSize': info['storage_size'],
            'osVersion': info['os_version']
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