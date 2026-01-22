from flask import Blueprint, request, jsonify
from app.services.supabase_client import get_supabase
from app.middleware.auth import token_required, device_token_required
from app.middleware.rbac import check_permission

device_bp = Blueprint('device', __name__)

@device_bp.route('/status', methods=['GET'])
@token_required
@check_permission('device', 'read')
def get_device_status():
    """Get current device status"""
    try:
        supabase = get_supabase()
        response = supabase.table('device_status').select('*').order('updated_at', desc=True).limit(1).execute()
        
        if not response.data:
            return jsonify({'error': 'No device status found'}), 404
        
        status = response.data[0]
        
        return jsonify({
            'deviceOnline': status['device_online'],
            'cameraStatus': status['camera_status'],
            'batteryLevel': status['battery_level'],
            'lastObstacle': status['last_obstacle'],
            'lastDetectionTime': status['last_detection_time']
        }), 200
        
    except Exception as e:
        print(f"Get device status error: {str(e)}")
        return jsonify({'error': 'Failed to get device status'}), 500

@device_bp.route('/status', methods=['POST'])
@device_token_required
def update_device_status():
    """Update device status (called by Raspberry Pi)"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        supabase = get_supabase()
        
        # Prepare update data
        update_data = {}
        
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
        
        update_data['updated_at'] = 'now()'
        
        # Check if a row exists
        existing = supabase.table('device_status').select('id').limit(1).execute()
        
        if existing.data and len(existing.data) > 0:
            # Update existing row
            status_id = existing.data[0]['id']
            response = supabase.table('device_status').update(update_data).eq('id', status_id).execute()
        else:
            # Insert new row
            response = supabase.table('device_status').insert(update_data).execute()
        
        return jsonify({'message': 'Device status updated', 'data': response.data}), 200
        
    except Exception as e:
        print(f"Update device status error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to update device status'}), 500

@device_bp.route('/system-info', methods=['GET'])
@token_required
@check_permission('system', 'read')
def get_system_info():
    """Get system information"""
    try:
        supabase = get_supabase()
        response = supabase.table('system_info').select('*').limit(1).execute()
        
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
        return jsonify({'error': 'Failed to get system info'}), 500

@device_bp.route('/system-info/temperature', methods=['POST'])
@device_token_required
def update_temperature():
    """Update CPU temperature (called by Raspberry Pi)"""
    try:
        data = request.get_json()
        
        if not data or 'temperature' not in data:
            return jsonify({'error': 'Temperature is required'}), 400
        
        supabase = get_supabase()
        response = supabase.table('system_info').update({
            'cpu_temperature': data['temperature'],
            'updated_at': 'now()'
        }).execute()
        
        return jsonify({'message': 'Temperature updated'}), 200
        
    except Exception as e:
        print(f"Update temperature error: {str(e)}")
        return jsonify({'error': 'Failed to update temperature'}), 500