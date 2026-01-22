from flask import Blueprint, request, jsonify
from app.services.supabase_client import get_supabase
from app.middleware.auth import token_required
from app.middleware.rbac import admin_required
from app.utils.jwt_handler import generate_device_token
import secrets

devices_bp = Blueprint('devices', __name__)

@devices_bp.route('/', methods=['GET'])
@token_required
def get_user_devices():
    """Get all devices for current user"""
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
        
        return jsonify({'data': response.data}), 200
        
    except Exception as e:
        print(f"Get devices error: {e}")
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
        
        # Check device limit (optional - e.g., max 5 devices per user)
        existing = supabase.table('user_devices')\
            .select('*', count='exact')\
            .eq('user_id', user_id)\
            .execute()
        
        if existing.count >= 5:
            return jsonify({'error': 'Maximum 5 devices per user'}), 400
        
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
        
        # Check ownership (users can only update their own devices)
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