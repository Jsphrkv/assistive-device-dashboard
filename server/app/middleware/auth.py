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
    """
    Middleware to verify device token from X-Device-Token header
    IMPROVED VERSION WITH EXTENSIVE LOGGING
    """
    from functools import wraps
    from flask import request, jsonify
    from app.services.supabase_client import get_supabase
    
    @wraps(f)
    def decorated(*args, **kwargs):
        print(f"\n{'='*60}")
        print(f"[DEVICE AUTH] Authenticating request to {request.path}")
        print(f"{'='*60}")
        
        # Check for token in header
        auth_header = request.headers.get('X-Device-Token', '')
        print(f"📋 Headers received:")
        for key, value in request.headers:
            if key.lower() in ['x-device-token', 'authorization', 'content-type']:
                if 'token' in key.lower():
                    print(f"   {key}: {value[:20]}..." if len(value) > 20 else f"   {key}: {value}")
                else:
                    print(f"   {key}: {value}")
        
        if not auth_header:
            print(f"❌ [DEVICE AUTH] No X-Device-Token header found!")
            return jsonify({'error': 'Device token required'}), 401
        
        device_token = auth_header.replace('Bearer ', '').strip()
        print(f"🔑 [DEVICE AUTH] Token received: {device_token[:20]}...")
        
        try:
            # Look up device by token
            supabase = get_supabase()
            print(f"🔍 [DEVICE AUTH] Querying database for device with this token...")
            
            response = supabase.table('user_devices')\
                .select('*')\
                .eq('device_token', device_token)\
                .execute()
            
            print(f"📊 [DEVICE AUTH] Query result: {len(response.data) if response.data else 0} devices found")
            
            if not response.data or len(response.data) == 0:
                print(f"❌ [DEVICE AUTH] No device found with this token!")
                print(f"   Possible reasons:")
                print(f"   - Token is invalid or expired")
                print(f"   - Device was deleted from database")
                print(f"   - Token doesn't match any device_token in user_devices table")
                return jsonify({'error': 'Invalid device token'}), 401
            
            device = response.data[0]
            print(f"✅ [DEVICE AUTH] Device found!")
            print(f"   Device ID: {device['id']}")
            print(f"   Device Name: {device.get('device_name', 'Unknown')}")
            print(f"   Status: {device.get('status', 'Unknown')}")
            print(f"   User ID: {device.get('user_id', 'Unknown')}")
            
            # Check if device is active
            if device.get('status') != 'active':
                print(f"⚠️  [DEVICE AUTH] Device is not active (status: {device.get('status')})")
                print(f"   Allowing anyway, but device should be activated")
            
            # Set device in request context
            request.current_device = device
            print(f"✅ [DEVICE AUTH] Authentication successful!")
            print(f"   request.current_device set to: {device['id']}")
            print(f"{'='*60}\n")
            
            # Call the actual route handler
            return f(*args, **kwargs)
            
        except Exception as e:
            print(f"❌ [DEVICE AUTH] Error during authentication!")
            print(f"   Error type: {type(e).__name__}")
            print(f"   Error message: {str(e)}")
            import traceback
            traceback.print_exc()
            print(f"{'='*60}\n")
            return jsonify({'error': 'Authentication failed'}), 500
    
    return decorated

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(request, 'current_user'):
            return jsonify({'error': 'Authentication required'}), 401
        
        if request.current_user.get('role') != 'admin':
            return jsonify({
                'error': 'Admin access required',
                'message': 'This action requires administrator privileges'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated
 
def user_or_admin_required(f):
    """Decorator to require user or admin role"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(request, 'current_user'):
            return jsonify({'error': 'Authentication required'}), 401
        
        role = request.current_user.get('role')
        if role not in ['user', 'admin']:
            return jsonify({'error': 'Access denied'}), 403
        
        return f(*args, **kwargs)
    
    return decorated

def check_permission(resource, action):
    """
    Check if current user has permission for specific resource and action
    
    Permissions matrix:
    - admin: can do everything
    - user: can read most things, limited write access
    - device: can only write sensor data
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(request, 'current_user'):
                return jsonify({'error': 'Authentication required'}), 401
            
            role = request.current_user.get('role')
            
            # Admin can do everything
            if role == 'admin':
                return f(*args, **kwargs)
            
            # Define permission rules
            permissions = {
                'user': {
                    'detections': ['read'],
                    'statistics': ['read'],
                    'settings': ['read', 'update_limited'],
                    'device': ['read'],
                    'system': ['read']
                },
                'device': {
                    'detections': ['create'],
                    'device_status': ['update']
                }
            }
            
            # Check if user has permission
            if role in permissions and resource in permissions[role]:
                if action in permissions[role][resource]:
                    return f(*args, **kwargs)
            
            return jsonify({
                'error': f'Permission denied',
                'message': f'Your role ({role}) cannot perform {action} on {resource}'
            }), 403
        
        return decorated
    return decorator