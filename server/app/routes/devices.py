from flask import Blueprint, request, jsonify
from app.services.supabase_client import get_supabase
from app.middleware.auth import token_required, device_token_required, admin_required, check_permission
from app.utils.jwt_handler import generate_device_token
import secrets
import string
from datetime import datetime, timedelta, timezone

devices_bp = Blueprint('devices', __name__, url_prefix='/api/devices')

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
        
        # Generate unique device token AND pairing code
        device_token = generate_device_token(f"{user_id}-{device_name}")
        pairing_code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        
        supabase = get_supabase()
        
        # Check device limit (max 1 device per user)
        existing = supabase.table('user_devices')\
            .select('*', count='exact')\
            .eq('user_id', user_id)\
            .execute()
        
        if existing.count >= 1:
            return jsonify({
                'error': 'You can only register one device per account. Please delete your existing device first.'
            }), 400
        
        # Create device with pairing code
        new_device = {
            'user_id': user_id,
            'device_name': device_name,
            'device_model': device_model,
            'device_token': device_token,
            'pairing_code': pairing_code,  # ← ADD THIS
            'pairing_expires_at': (datetime.utcnow() + timedelta(hours=1)).isoformat(),  # ← ADD THIS
            'status': 'pending'  # Will become 'active' after pairing
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
        
        # Return pairing code (NOT the full token)
        return jsonify({
            'message': 'Device registered successfully',
            'device': {
                'id': device['id'],
                'name': device['device_name'],
                'model': device['device_model'],
                'pairing_code': pairing_code,  # ← CHANGED: Return code instead of token
                'expires_in': '1 hour',
                'status': device['status']
            }
        }), 201
        
    except Exception as e:
        print(f"Register device error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to register device'}), 500
    
@devices_bp.route('/complete-pairing', methods=['POST'])
def complete_pairing():
    """User enters pairing code to activate device (dashboard verification)"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        pairing_code = data.get('pairingCode')
        device_id = data.get('deviceId')
        
        print(f"Complete pairing request: deviceId={device_id}, code={pairing_code}")
        
        if not pairing_code:
            return jsonify({'error': 'Pairing code required'}), 400
        
        if not device_id:
            return jsonify({'error': 'Device ID required'}), 400
        
        supabase = get_supabase()
        
        # Find device with this ID
        device_response = supabase.table('user_devices').select('*').eq('id', device_id).execute()
        
        if not device_response.data or len(device_response.data) == 0:
            return jsonify({'error': 'Device not found'}), 404
        
        device = device_response.data[0]
        
        # Verify pairing code matches
        if not device.get('pairing_code'):
            return jsonify({'error': 'No pairing code set for this device'}), 400
        
        if device['pairing_code'].upper() != pairing_code.upper():
            return jsonify({'error': 'Invalid pairing code'}), 400
        
        # Check if code expired (1 hour)
        try:
            created_at_str = device['created_at']
            # Handle different datetime formats
            if created_at_str.endswith('Z'):
                created_at_str = created_at_str.replace('Z', '+00:00')
            created_at = datetime.fromisoformat(created_at_str)
            
            # Make sure created_at is timezone-aware
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            
            time_diff = datetime.now(timezone.utc) - created_at
            
            if time_diff > timedelta(hours=1):
                return jsonify({'error': 'Pairing code expired. Please register a new device.'}), 400
        except Exception as date_error:
            print(f"Date parsing error: {date_error}")
            # Don't fail on date parsing - just warn
            print("Warning: Could not verify code expiration")
        
        # Update device timestamp (don't change status - Pi will do that when it connects)
        supabase.table('user_devices').update({
            'updated_at': datetime.now(timezone.utc).isoformat()
        }).eq('id', device_id).execute()
        
        print(f"✅ Pairing code verified for device {device_id}")
        
        return jsonify({
            'success': True,
            'message': 'Code verified! Your Pi can now connect.'
        }), 200
        
    except Exception as e:
        print(f"❌ Complete pairing error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to complete pairing: {str(e)}'}), 500
    
@devices_bp.route('/pair-status-by-code/<pairing_code>', methods=['GET'])
def check_pair_status_by_code(pairing_code):
    """Polling endpoint - check if pairing code exists and device is ready"""
    try:
        pairing_code = pairing_code.upper().strip()
        
        if not pairing_code or len(pairing_code) != 6:
            return jsonify({'error': 'Invalid pairing code format'}), 400
        
        supabase = get_supabase()
        
        # Find device by pairing code
        response = supabase.table('user_devices')\
            .select('id, device_name, status, pairing_code, pairing_expires_at, created_at')\
            .eq('pairing_code', pairing_code)\
            .execute()
        
        if not response.data or len(response.data) == 0:
            return jsonify({
                'exists': False,
                'message': 'Pairing code not found'
            }), 200
        
        device = response.data[0]
        
        # Check if expired
        try:
            expires_at = datetime.fromisoformat(device['pairing_expires_at'].replace('Z', '+00:00'))
            if datetime.utcnow() > expires_at.replace(tzinfo=None):
                return jsonify({
                    'exists': True,
                    'expired': True,
                    'message': 'Pairing code expired'
                }), 200
        except:
            pass  # If expiration check fails, continue
        
        # Return device info
        return jsonify({
            'exists': True,
            'expired': False,
            'device_id': device['id'],
            'device_name': device['device_name'],
            'pairing_code': device['pairing_code'],
            'status': device['status'],
            'message': 'Pairing code is valid'
        }), 200
        
    except Exception as e:
        print(f"Pair status check error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to check pairing status'}), 500

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

@devices_bp.route('/pending-for-serial/<serial_number>', methods=['GET'])
def get_pending_for_serial(serial_number):
    """Check if there's a pending pairing code (for automatic pairing)"""
    try:
        supabase = get_supabase()
        
        # Find the MOST RECENT pending device (not yet paired to this serial)
        # We look for devices where status='pending' and serial_number is NULL
        response = supabase.table('user_devices')\
            .select('id, device_name, pairing_code, pairing_expires_at')\
            .eq('status', 'pending')\
            .is_('serial_number', 'null')\
            .order('created_at', desc=True)\
            .limit(1)\
            .execute()
        
        if not response.data or len(response.data) == 0:
            return jsonify({
                'has_pending': False,
                'message': 'No pending pairing codes available'
            }), 404
        
        device = response.data[0]
        
        # Check if expired
        try:
            expires_at = datetime.fromisoformat(device['pairing_expires_at'].replace('Z', '+00:00'))
            if datetime.utcnow() > expires_at.replace(tzinfo=None):
                return jsonify({
                    'has_pending': False,
                    'message': 'Pairing code expired'
                }), 404
        except:
            pass
        
        # Return the pending pairing code
        return jsonify({
            'has_pending': True,
            'pairing_code': device['pairing_code'],
            'device_name': device['device_name'],
            'device_id': device['id']
        }), 200
        
    except Exception as e:
        print(f"Get pending error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to check pending devices'}), 500
    
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
            return jsonify({
                'error': 'No active device found',
                'hasDevice': False
            }), 200  # Changed from 404 to 200 with error flag
        
        device_id = device.data[0]['id']
        
        # Get system info for this device
        response = supabase.table('system_info')\
            .select('*')\
            .eq('device_id', device_id)\
            .limit(1)\
            .execute()
        
        if not response.data:
            return jsonify({
                'error': 'No system info available yet',
                'hasDevice': True,
                'deviceId': device_id
            }), 200  # Changed from 404 to 200 with error flag
        
        info = response.data[0]
        
        return jsonify({
            'hasDevice': True,
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
    
@devices_bp.route('/system-info', methods=['POST'])
@device_token_required
def update_system_info():
    """Update system information (called by Raspberry Pi on first boot)"""
    try:
        device_id = request.current_device['id']
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        supabase = get_supabase()
        
        # Prepare system info data
        system_data = {
            'device_id': device_id,
            'raspberry_pi_model': data.get('raspberryPiModel'),
            'software_version': data.get('softwareVersion'),
            'cpu_model': data.get('cpuModel'),
            'ram_size': data.get('ramSize'),
            'storage_size': data.get('storageSize'),
            'os_version': data.get('osVersion'),
            'cpu_temperature': data.get('cpuTemperature'),
            'last_reboot_time': data.get('lastRebootTime'),
            'updated_at': 'now()'
        }
        
        # Check if system info already exists
        existing = supabase.table('system_info')\
            .select('id')\
            .eq('device_id', device_id)\
            .limit(1)\
            .execute()
        
        if existing.data and len(existing.data) > 0:
            # Update existing
            response = supabase.table('system_info')\
                .update(system_data)\
                .eq('device_id', device_id)\
                .execute()
        else:
            # Insert new
            response = supabase.table('system_info').insert(system_data).execute()
        
        # Update device status to 'active' since it's now connected
        supabase.table('user_devices')\
            .update({'status': 'active', 'last_seen': 'now()'})\
            .eq('id', device_id)\
            .execute()
        
        return jsonify({
            'message': 'System info updated successfully',
            'data': response.data
        }), 200
        
    except Exception as e:
        print(f"Update system info error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to update system info'}), 500
    
# ============================================
# IMPROVEMENT 1 & 2: Secure Two-Step Pairing
# ============================================

def check_rate_limit(ip_address, serial_number=None):
    """Check if IP or serial has exceeded pairing attempts (5 per minute)"""
    supabase = get_supabase()
    one_minute_ago = (datetime.utcnow() - timedelta(minutes=1)).isoformat()
    
    # Check IP-based rate limit
    ip_attempts = supabase.table('pairing_attempts')\
        .select('*', count='exact')\
        .eq('ip_address', ip_address)\
        .gte('attempted_at', one_minute_ago)\
        .execute()
    
    if ip_attempts.count >= 5:
        return False, "Too many pairing attempts from this IP. Try again in 1 minute."
    
    # Check serial-based rate limit if provided
    if serial_number:
        serial_attempts = supabase.table('pairing_attempts')\
            .select('*', count='exact')\
            .eq('serial_number', serial_number)\
            .gte('attempted_at', one_minute_ago)\
            .execute()
        
        if serial_attempts.count >= 5:
            return False, "Too many pairing attempts for this device. Try again in 1 minute."
    
    return True, None

def log_pairing_attempt(ip_address, serial_number=None, success=False):
    """Log pairing attempt for rate limiting"""
    try:
        supabase = get_supabase()
        supabase.table('pairing_attempts').insert({
            'ip_address': ip_address,
            'serial_number': serial_number,
            'attempted_at': datetime.utcnow().isoformat(),
            'success': success
        }).execute()
    except:
        pass  # Don't fail if logging fails

@devices_bp.route('/pair', methods=['POST'])
def pair_device():
    """STEP 1: RPi sends pairing code + serial → Get session token"""
    try:
        data = request.get_json()
        pairing_code = data.get('pairing_code', '').upper().strip()
        serial_number = data.get('serial_number', '').strip()
        
        if not pairing_code:
            return jsonify({'error': 'Pairing code required'}), 400
        
        if not serial_number:
            return jsonify({'error': 'Device serial number required'}), 400
        
        # Get client IP
        ip_address = request.remote_addr
        
        # IMPROVEMENT 5: Rate limiting
        allowed, error_msg = check_rate_limit(ip_address, serial_number)
        if not allowed:
            log_pairing_attempt(ip_address, serial_number, False)
            return jsonify({'error': error_msg}), 429
        
        supabase = get_supabase()
        
        # IMPROVEMENT 3: Check if serial already paired
        existing_device = supabase.table('user_devices')\
            .select('*')\
            .eq('serial_number', serial_number)\
            .eq('status', 'active')\
            .execute()
        
        if existing_device.data and len(existing_device.data) > 0:
            log_pairing_attempt(ip_address, serial_number, False)
            return jsonify({'error': 'This device is already paired to an account'}), 400
        
        # Find device by pairing code
        response = supabase.table('user_devices')\
            .select('*')\
            .eq('pairing_code', pairing_code)\
            .eq('status', 'pending')\
            .execute()
        
        if not response.data or len(response.data) == 0:
            log_pairing_attempt(ip_address, serial_number, False)
            return jsonify({'error': 'Invalid pairing code'}), 404
        
        device = response.data[0]
        
        # Check if pairing code expired
        expires_at = datetime.fromisoformat(device['pairing_expires_at'].replace('Z', '+00:00'))
        if datetime.utcnow() > expires_at.replace(tzinfo=None):
            log_pairing_attempt(ip_address, serial_number, False)
            return jsonify({'error': 'Pairing code expired'}), 400
        
        # IMPROVEMENT 1: Generate temporary session token (15 min expiry)
        session_token = secrets.token_urlsafe(32)
        session_expires = datetime.utcnow() + timedelta(minutes=15)
        
        # Update device with session token and serial
        supabase.table('user_devices').update({
            'pairing_session_token': session_token,
            'session_expires_at': session_expires.isoformat(),
            'serial_number': serial_number,
            'pairing_attempts': device.get('pairing_attempts', 0) + 1,
            'last_pairing_attempt': datetime.utcnow().isoformat()
        }).eq('id', device['id']).execute()
        
        log_pairing_attempt(ip_address, serial_number, True)
        
        # IMPROVEMENT 1: Return ONLY session token (not device token)
        return jsonify({
            'success': True,
            'session_token': session_token,
            'expires_in': 900,  # 15 minutes in seconds
            'device_name': device['device_name']
        }), 200
        
    except Exception as e:
        print(f"Pairing error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Pairing failed'}), 500

@devices_bp.route('/activate', methods=['POST'])
def activate_device():
    """STEP 2: RPi exchanges session token → Get permanent device token"""
    try:
        data = request.get_json()
        session_token = data.get('session_token', '').strip()
        serial_number = data.get('serial_number', '').strip()
        
        if not session_token:
            return jsonify({'error': 'Session token required'}), 400
        
        if not serial_number:
            return jsonify({'error': 'Serial number required'}), 400
        
        supabase = get_supabase()
        
        # Find device by session token and serial
        response = supabase.table('user_devices')\
            .select('*')\
            .eq('pairing_session_token', session_token)\
            .eq('serial_number', serial_number)\
            .eq('status', 'pending')\
            .execute()
        
        if not response.data or len(response.data) == 0:
            return jsonify({'error': 'Invalid session'}), 404
        
        device = response.data[0]
        
        # Check if session expired
        session_expires = datetime.fromisoformat(device['session_expires_at'].replace('Z', '+00:00'))
        if datetime.utcnow() > session_expires.replace(tzinfo=None):
            return jsonify({'error': 'Session expired. Start pairing again.'}), 400
        
        # IMPROVEMENT 4: Clear pairing code and session token
        # IMPROVEMENT 8: Activate device (separate from system-info)
        supabase.table('user_devices').update({
            'status': 'active',
            'paired_at': datetime.utcnow().isoformat(),
            'last_seen': datetime.utcnow().isoformat(),
            'pairing_code': None,  # Clear pairing code
            'pairing_session_token': None,  # Clear session token
            'session_expires_at': None
        }).eq('id', device['id']).execute()
        
        print(f"✅ Device activated: {device['device_name']} (Serial: {serial_number})")
        
        # Return permanent device token
        return jsonify({
            'success': True,
            'device_id': device['id'],
            'device_token': device['device_token'],
            'device_name': device['device_name']
        }), 200
        
    except Exception as e:
        print(f"Activation error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Activation failed'}), 500

@devices_bp.route('/pair-status/<serial_number>', methods=['GET'])
def check_pair_status(serial_number):
    """IMPROVEMENT 2: Polling endpoint - check if device has been paired"""
    try:
        supabase = get_supabase()
        
        # Find device by serial
        response = supabase.table('user_devices')\
            .select('id, device_name, status, paired_at')\
            .eq('serial_number', serial_number)\
            .execute()
        
        if not response.data or len(response.data) == 0:
            return jsonify({
                'paired': False,
                'status': 'waiting',
                'message': 'Waiting for pairing code...'
            }), 200
        
        device = response.data[0]
        
        if device['status'] == 'active':
            return jsonify({
                'paired': True,
                'status': 'active',
                'device_name': device['device_name'],
                'paired_at': device['paired_at']
            }), 200
        else:
            return jsonify({
                'paired': False,
                'status': 'pending',
                'message': 'Pairing in progress...'
            }), 200
        
    except Exception as e:
        print(f"Pair status error: {e}")
        return jsonify({'error': 'Failed to check status'}), 500
    
