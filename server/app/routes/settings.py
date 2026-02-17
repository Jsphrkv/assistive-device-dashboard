from flask import Blueprint, request, jsonify
from app.services.supabase_client import get_supabase
from app.middleware.auth import token_required, admin_required

settings_bp = Blueprint('settings', __name__, url_prefix='/api/settings')

@settings_bp.route('', methods=['GET'])   
@token_required
def get_settings():
    """Get user settings"""
    try:
        user_id = request.current_user['user_id']
        
        supabase = get_supabase()
        response = supabase.table('settings')\
            .select('*')\
            .eq('user_id', user_id)\
            .execute()
        
        if not response.data:
            default_settings = {
                'user_id': user_id,
                'sensitivity': 75,
                'distance_threshold': 100,
                'alert_mode': 'both',
                'ultrasonic_enabled': True,
                'camera_enabled': True,
                'updated_by': user_id
            }
            insert_response = supabase.table('settings').insert(default_settings).execute()
            if not insert_response.data:
                return jsonify({'error': 'Failed to create settings'}), 500
            settings = insert_response.data[0]
        else:
            settings = response.data[0]
        
        return jsonify({
            'data': {
                'sensitivity': settings['sensitivity'],
                'distanceThreshold': settings['distance_threshold'],
                'alertMode': settings['alert_mode'],
                'ultrasonicEnabled': settings['ultrasonic_enabled'],
                'cameraEnabled': settings['camera_enabled']
            }
        }), 200
        
    except Exception as e:
        print(f"Get settings error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to get settings'}), 500


@settings_bp.route('', methods=['PUT'])  
@token_required
def update_settings():
    """Update user settings - all users can update all settings"""
    try:
        user_id = request.current_user['user_id']
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        supabase = get_supabase()
        
        # ✅ All users can update all settings
        update_data = {'updated_by': user_id}
        
        if 'sensitivity' in data:
            update_data['sensitivity'] = data['sensitivity']
        if 'distanceThreshold' in data:
            update_data['distance_threshold'] = data['distanceThreshold']
        if 'alertMode' in data:
            update_data['alert_mode'] = data['alertMode']
        if 'ultrasonicEnabled' in data:
            update_data['ultrasonic_enabled'] = data['ultrasonicEnabled']
        if 'cameraEnabled' in data:
            update_data['camera_enabled'] = data['cameraEnabled']
        
        response = supabase.table('settings')\
            .update(update_data)\
            .eq('user_id', user_id)\
            .execute()
        
        try:
            supabase.table('activity_logs').insert({
                'user_id': user_id,
                'action': 'Settings Updated',
                'description': f"User {request.current_user['username']} updated settings"
            }).execute()
        except Exception as log_error:
            print(f"Warning: Could not log activity: {log_error}")
        
        return jsonify({
            'message': 'Settings updated successfully',
            'data': response.data
        }), 200
        
    except Exception as e:
        print(f"Update settings error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to update settings'}), 500


@settings_bp.route('/reset', methods=['POST'])
@token_required
def reset_settings():
    """Reset settings to default"""
    try:
        user_id = request.current_user['user_id']
        
        supabase = get_supabase()
        
        default_settings = {
            'sensitivity': 75,
            'distance_threshold': 100,
            'alert_mode': 'both',
            'ultrasonic_enabled': True,
            'camera_enabled': True,
            'updated_by': user_id
        }
        
        response = supabase.table('settings')\
            .update(default_settings)\
            .eq('user_id', user_id)\
            .execute()
        
        return jsonify({
            'message': 'Settings reset to default',
            'data': response.data
        }), 200
        
    except Exception as e:
        print(f"Reset settings error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to reset settings'}), 500


@settings_bp.route('/global', methods=['GET'])
@token_required
@admin_required
def get_global_settings():
    """Get all users' settings (admin only)"""
    try:
        supabase = get_supabase()
        response = supabase.table('settings')\
            .select('*, users(username, role)')\
            .execute()
        
        return jsonify({'data': response.data}), 200
        
    except Exception as e:
        print(f"Get global settings error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to get global settings'}), 500


# ✅ NEW: Device token endpoint for Pi to fetch settings
@settings_bp.route('/device', methods=['GET'])
def get_device_settings():
    """Get settings for Pi device (uses device token auth)"""
    try:
        from app.middleware.auth import device_token_required
        
        # Manual device token check
        device_token = request.headers.get('X-Device-Token')
        if not device_token:
            return jsonify({'error': 'Device token required'}), 401
        
        supabase = get_supabase()
        
        # Find device by token
        device_response = supabase.table('user_devices')\
            .select('user_id')\
            .eq('device_token', device_token)\
            .limit(1)\
            .execute()
        
        if not device_response.data:
            return jsonify({'error': 'Invalid device token'}), 401
        
        user_id = device_response.data[0]['user_id']
        
        # Get settings for this user
        settings_response = supabase.table('settings')\
            .select('*')\
            .eq('user_id', user_id)\
            .limit(1)\
            .execute()
        
        if not settings_response.data:
            # Return defaults
            return jsonify({
                'data': {
                    'sensitivity': 75,
                    'distanceThreshold': 100,
                    'alertMode': 'both',
                    'ultrasonicEnabled': True,
                    'cameraEnabled': True
                }
            }), 200
        
        settings = settings_response.data[0]
        
        return jsonify({
            'data': {
                'sensitivity': settings['sensitivity'],
                'distanceThreshold': settings['distance_threshold'],
                'alertMode': settings['alert_mode'],
                'ultrasonicEnabled': settings['ultrasonic_enabled'],
                'cameraEnabled': settings['camera_enabled']
            }
        }), 200
        
    except Exception as e:
        print(f"Get device settings error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to get device settings'}), 500