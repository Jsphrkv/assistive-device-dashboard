from functools import wraps
from flask import request, jsonify

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