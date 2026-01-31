from flask import Blueprint, request, jsonify
from app.services.supabase_client import get_supabase
from app.middleware.auth import token_required, admin_required

settings_bp = Blueprint('settings', __name__, url_prefix='/api/settings')

@settings_bp.route('', methods=['GET'])  # ✅ No trailing slash
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
            # Create default settings for new user
            default_settings = {
                'user_id': user_id,
                'sensitivity': 75,
                'distance_threshold': 100,
                'alert_mode': 'both',
                'ultrasonic_enabled': True,
                'camera_enabled': True,
                'created_at': 'now()',
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


@settings_bp.route('', methods=['PUT'])  # ✅ No trailing slash
@token_required
def update_settings():
    """Update user settings"""
    try:
        user_id = request.current_user['user_id']
        user_role = request.current_user['role']
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # RBAC: Check if user is trying to modify admin-only fields
        admin_only_fields = ['distanceThreshold', 'ultrasonicEnabled', 'cameraEnabled']
        
        if user_role == 'user':
            attempted_admin_fields = [field for field in admin_only_fields if field in data]
            
            if attempted_admin_fields:
                return jsonify({
                    'error': 'Permission denied',
                    'message': f'Users cannot modify: {", ".join(attempted_admin_fields)}. Only admins can change these settings.'
                }), 403
        
        supabase = get_supabase()
        
        # Prepare update data based on role
        update_data = {'updated_at': 'now()', 'updated_by': user_id}
        
        # Users can only update sensitivity and alert mode
        if user_role == 'user':
            if 'sensitivity' in data:
                update_data['sensitivity'] = data['sensitivity']
            if 'alertMode' in data:
                update_data['alert_mode'] = data['alertMode']
        
        # Admins can update everything
        elif user_role == 'admin':
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
        
        # Update settings
        response = supabase.table('settings')\
            .update(update_data)\
            .eq('user_id', user_id)\
            .execute()
        
        # Log activity
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
        user_role = request.current_user['role']
        
        supabase = get_supabase()
        
        # Default settings
        default_settings = {
            'sensitivity': 75,
            'alert_mode': 'both',
            'updated_at': 'now()',
            'updated_by': user_id
        }
        
        # Only admins can reset ALL settings including device controls
        if user_role == 'admin':
            default_settings['distance_threshold'] = 100
            default_settings['ultrasonic_enabled'] = True
            default_settings['camera_enabled'] = True
        
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