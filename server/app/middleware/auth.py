from functools import wraps
from flask import request, jsonify
from app.utils.jwt_handler import decode_token

def token_required(f):
    """Decorator to require valid JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        # Decode token
        payload = decode_token(token)
        
        if not payload:
            return jsonify({'error': 'Token is invalid or expired'}), 401
        
        # Add user info to request context
        request.current_user = payload
        
        return f(*args, **kwargs)
    
    return decorated

def device_token_required(f):
    """Decorator to require valid device token (for Raspberry Pi)"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from header
        if 'X-Device-Token' in request.headers:
            token = request.headers['X-Device-Token']
        elif 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]
            except IndexError:
                return jsonify({'error': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'error': 'Device token is missing'}), 401
        
        # Verify token exists in database
        from app.services.supabase_client import get_supabase
        supabase = get_supabase()
        
        device = supabase.table('user_devices')\
            .select('*')\
            .eq('device_token', token)\
            .eq('is_active', True)\
            .single()\
            .execute()
        
        if not device.data:
            return jsonify({'error': 'Invalid or inactive device token'}), 401
        
        # Update last_seen timestamp
        supabase.table('user_devices')\
            .update({
                'last_seen': 'now()',
                'status': 'active'
            })\
            .eq('id', device.data['id'])\
            .execute()
        
        # Add device info to request context
        request.current_device = device.data
        
        return f(*args, **kwargs)
    
    return decorated