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
        print("\n" + "="*60)
        print("DEVICE TOKEN CHECK")
        print("="*60)
        
        token = None
        
        # Get token from header
        if 'X-Device-Token' in request.headers:
            token = request.headers['X-Device-Token']
            print(f"✓ Found X-Device-Token header")
            print(f"  Token: {token[:50]}...")
        elif 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            print(f"✓ Found Authorization header: {auth_header[:30]}...")
            try:
                token = auth_header.split(' ')[1]
            except IndexError:
                print("✗ Invalid Authorization format")
                return jsonify({'error': 'Invalid token format'}), 401
        else:
            print("✗ No token header found")
            print(f"  Available headers: {list(request.headers.keys())}")
        
        if not token:
            print("✗ Token is empty")
            return jsonify({'error': 'Device token is missing'}), 401
        
        # Decode token
        print(f"Attempting to decode token...")
        payload = decode_token(token)
        
        print(f"Decoded payload: {payload}")
        
        if not payload:
            print("✗ Token decode failed (expired or invalid)")
            return jsonify({'error': 'Token is invalid or expired'}), 401
        
        if payload.get('type') != 'device':
            print(f"✗ Wrong token type: {payload.get('type')}")
            return jsonify({'error': 'Invalid device token'}), 401
        
        print("✓ Token validated successfully")
        print("="*60 + "\n")
        
        # Add device info to request context
        request.current_device = payload
        
        return f(*args, **kwargs)
    
    return decorated