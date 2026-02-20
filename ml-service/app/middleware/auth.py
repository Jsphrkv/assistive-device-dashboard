from functools import wraps
from flask import request, jsonify
from app.services.supabase_client import get_supabase


def device_token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('X-Device-Token')

        if not token:
            return jsonify({'error': 'Device token required'}), 401

        try:
            supabase = get_supabase()
            response = supabase.table('user_devices') \
                .select('id, device_name, status, user_id') \
                .eq('device_token', token) \
                .eq('status', 'active') \
                .limit(1) \
                .execute()

            if not response.data:
                return jsonify({'error': 'Invalid or inactive device token'}), 401

            device = response.data[0]
            request.current_device = {
                'id':          device['id'],
                'device_name': device['device_name'],
                'user_id':     device['user_id']
            }
            return f(*args, **kwargs)

        except Exception as e:
            print(f"Auth error: {e}")
            return jsonify({'error': 'Authentication failed'}), 401

    return decorated