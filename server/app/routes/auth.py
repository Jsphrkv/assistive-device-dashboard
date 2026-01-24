from flask import Blueprint, request, jsonify
from app.services.supabase_client import get_supabase
from app.utils.jwt_handler import generate_token
from app.middleware.auth import token_required
import bcrypt
import traceback

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/test-db', methods=['GET'])
def test_db():
    """Test database connection"""
    try:
        supabase = get_supabase()
        print("Testing Supabase connection...")
        response = supabase.table('users').select('*').execute()
        print(f"Response: {response}")
        return jsonify({
            'success': True,
            'users_count': len(response.data),
            'users': response.data
        }), 200
    except Exception as e:
        print(f"Test DB error: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Username and password are required'}), 400
        
        username = data['username']
        password = data['password']
        
        # Get user from database
        supabase = get_supabase()
        response = supabase.table('users').select('*').eq('username', username).execute()
        
        if not response.data or len(response.data) == 0:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        user = response.data[0]
        
        # ✅ Verify password with bcrypt
        if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Update last login
        supabase.table('users').update({
            'last_login': 'now()'
        }).eq('id', user['id']).execute()
        
        # Generate JWT token
        token = generate_token(user['id'], user['username'], user['role'])
        
        # Log activity
        supabase.table('activity_logs').insert({
            'user_id': user['id'],
            'action': 'login',
            'description': f"User {user['username']} logged in"
        }).execute()
        
        return jsonify({
            'token': token,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'role': user['role'],
                'email': user.get('email')
            }
        }), 200
        
    except Exception as e:
        print(f"Login error: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': 'Login failed'}), 500

@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user():
    """Get current user info"""
    try:
        user_id = request.current_user['user_id']
        
        supabase = get_supabase()
        response = supabase.table('users').select('id, username, role, email').eq('id', user_id).execute()
        
        if not response.data:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({'user': response.data[0]}), 200
        
    except Exception as e:
        print(f"Get user error: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': 'Failed to get user info'}), 500

@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout():
    """User logout endpoint"""
    try:
        user_id = request.current_user['user_id']
        username = request.current_user['username']
        
        # Log activity
        supabase = get_supabase()
        supabase.table('activity_logs').insert({
            'user_id': user_id,
            'action': 'logout',
            'description': f"User {username} logged out"
        }).execute()
        
        return jsonify({'message': 'Logged out successfully'}), 200
        
    except Exception as e:
        print(f"Logout error: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': 'Logout failed'}), 500
    
@auth_bp.route('/register', methods=['POST'])
def register():
    """User registration endpoint"""
    try:
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Username, email, and password are required'}), 400
        
        username = data['username']
        email = data['email']
        password = data['password']
        
        # Validate password strength
        if len(password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters'}), 400
        
        # Check if user already exists
        supabase = get_supabase()
        existing_user = supabase.table('users').select('*').eq('username', username).execute()
        
        if existing_user.data and len(existing_user.data) > 0:
            return jsonify({'error': 'Username already exists'}), 409
        
        # Check if email already exists
        existing_email = supabase.table('users').select('*').eq('email', email).execute()
        
        if existing_email.data and len(existing_email.data) > 0:
            return jsonify({'error': 'Email already exists'}), 409
        
        # ✅ Hash password with bcrypt
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create new user (default role is 'user')
        new_user = supabase.table('users').insert({
            'username': username,
            'email': email,
            'password_hash': password_hash,  # ✅ Now hashed!
            'role': 'user',
            'created_at': 'now()'
        }).execute()
        
        return jsonify({'message': 'Registration successful'}), 201
        
    except Exception as e:
        print(f"Registration error: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': 'Registration failed'}), 500