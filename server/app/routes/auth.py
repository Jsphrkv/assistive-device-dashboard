from flask import Blueprint, current_app, request, jsonify
from app.utils.tokens import generate_email_token, verify_email_token
from app.services.supabase_client import get_supabase
from app.services.email_service import (
    send_verification_email,
    send_password_reset_email
)
from app.utils.jwt_handler import generate_token
from app.middleware.auth import token_required
import bcrypt
import traceback
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# ============================================
# EXISTING ROUTES (Keep these)
# ============================================

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

@auth_bp.route('/me', methods=['GET', 'OPTIONS'])
@token_required
def get_current_user():
    """Get current user info"""
    if request.method == 'OPTIONS':
        return '', 200  # Handle preflight
    try:
        user_id = request.current_user['user_id']
        
        supabase = get_supabase()
        response = supabase.table('users').select('id, username, role, email, email_verified').eq('id', user_id).execute()
        
        if not response.data:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({'user': response.data[0]}), 200
        
    except Exception as e:
        print(f"Get user error: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': 'Failed to get user info'}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """User logout endpoint (JWT-based)"""
    try:
        auth_header = request.headers.get('Authorization')
        user_id = None
        username = None

        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

            import jwt
            try:
                payload = jwt.decode(
                    token,
                    current_app.config['JWT_SECRET_KEY'],
                    algorithms=[current_app.config['JWT_ALGORITHM']],
                    options={'verify_exp': False}  # allow expired tokens
                )
                user_id = payload.get('user_id')
                username = payload.get('username')
            except jwt.InvalidTokenError:
                pass  # Token invalid → still allow logout

        # Optional: log logout activity
        if user_id and username:
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
        return jsonify({'message': 'Logged out successfully'}), 200

# ============================================
# UPDATED REGISTRATION WITH EMAIL VERIFICATION
# ============================================

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register new user"""
    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip()
        username = data.get('username', '').strip()
        password = data.get('password')
        
        # Validation
        if not all([email, username, password]):
            return jsonify({'error': 'All fields are required'}), 400
        
        if len(password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters'}), 400
        
        # Check if user exists
        supabase = get_supabase()
        existing = supabase.table('users').select('email').eq('email', email).execute()
        
        if existing.data:
            return jsonify({'error': 'Email already registered'}), 400
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Generate verification token
        verification_token = generate_email_token(email, salt='email-verification')
        
        # Create user
        user_data = {
            'email': email,
            'username': username,
            'password_hash': password_hash,
            'role': 'user',
            'email_verified': False,
            'verification_token': verification_token,
            'created_at': datetime.utcnow().isoformat()
        }
        
        response = supabase.table('users').insert(user_data).execute()
        
        if not response.data:
            return jsonify({'error': 'Registration failed'}), 500
        
        # ✅ Send verification email with proper context
        from flask import current_app
        import threading
        
        app = current_app._get_current_object()
        
        def send_email_background(app_instance):
            with app_instance.app_context():
                try:
                    send_verification_email(email, username, verification_token)
                    print(f"✅ Verification email sent to {email}")
                except Exception as e:
                    print(f"❌ Email sending failed: {str(e)}")
        
        thread = threading.Thread(target=send_email_background, args=(app,))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'message': 'Registration successful! Please check your email to verify your account.'
        }), 201
        
    except Exception as e:
        print(f"Registration error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Registration failed'}), 500

# ============================================
# EMAIL VERIFICATION
# ============================================

@auth_bp.route('/verify-email', methods=['POST'])
def verify_email():
    """Verify email with token"""
    try:
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({'error': 'Verification token is required'}), 400
        
        # Verify token (24 hour expiry)
        email = verify_email_token(token, salt='email-verification', max_age=86400)
        
        if not email:
            return jsonify({'error': 'Invalid or expired verification link'}), 400
        
        # Update user
        supabase = get_supabase()
        response = supabase.table('users')\
            .update({
                'email_verified': True,
                'verification_token': None
            })\
            .eq('email', email)\
            .execute()
        
        if not response.data:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({'message': 'Email verified successfully! You can now login.'}), 200
        
    except Exception as e:
        print(f"Email verification error: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': 'Verification failed'}), 500

@auth_bp.route('/resend-verification', methods=['POST'])
def resend_verification():
    """Resend verification email"""
    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip()
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        supabase = get_supabase()
        user = supabase.table('users').select('*').eq('email', email).execute()
        
        if not user.data:
            return jsonify({'message': 'If the email exists, a verification link has been sent'}), 200
        
        user_data = user.data[0]
        
        if user_data.get('email_verified', False):
            return jsonify({'error': 'Email already verified'}), 400
        
        # Generate new token
        verification_token = generate_email_token(email, salt='email-verification')
        
        # Update token
        supabase.table('users')\
            .update({'verification_token': verification_token})\
            .eq('email', email)\
            .execute()
        
        # ✅ Send email with proper context
        from flask import current_app
        import threading
        
        app = current_app._get_current_object()
        
        def send_email_background(app_instance):
            with app_instance.app_context():
                try:
                    send_verification_email(email, user_data['username'], verification_token)
                    print(f"✅ Verification email sent to {email}")
                except Exception as e:
                    print(f"❌ Email sending failed: {str(e)}")
        
        thread = threading.Thread(target=send_email_background, args=(app,))
        thread.daemon = True
        thread.start()
        
        return jsonify({'message': 'Verification email sent! Please check your inbox.'}), 200
        
    except Exception as e:
        print(f"Resend verification error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to resend verification email'}), 500

# ============================================
# UPDATED LOGIN (requires email verification)
# ============================================

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint (requires verified email)"""
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
        
        # Check if email is verified ✅
        if not user.get('email_verified', False):
            return jsonify({
                'error': 'Email not verified',
                'message': 'Please verify your email before logging in',
                'email': user.get('email'),
                'needsVerification': True
            }), 403
        
        # Verify password with bcrypt
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
            'description': f"User {user['username']} loggedad in"
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

# ============================================
# PASSWORD RESET
# ============================================

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Request password reset"""
    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip()
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        supabase = get_supabase()
        user = supabase.table('users').select('*').eq('email', email).execute()
        
        # Always return success to prevent email enumeration
        if not user.data:
            print(f"⚠️ No user found with email: {email}")
            return jsonify({
                'message': 'If the email exists, a password reset link has been sent'
            }), 200
        
        user_data = user.data[0]
        
        # Generate reset token (24 hours expiry)
        reset_token = generate_email_token(email, salt='password-reset')
        
        print(f"="*60)
        print(f"PASSWORD RESET REQUESTED")
        print(f"Email: {email}")
        print(f"Username: {user_data['username']}")
        print(f"Token generated: {reset_token[:50]}...")
        print(f"="*60)
        
        # ✅ Send email SYNCHRONOUSLY (not in background thread)
        try:
            print("📧 Attempting to send password reset email...")
            send_password_reset_email(email, user_data['username'], reset_token)
            print(f"✅ Email sent successfully!")
        except Exception as email_error:
            print(f"="*60)
            print(f"❌ EMAIL SENDING FAILED!")
            print(f"Error: {str(email_error)}")
            import traceback
            traceback.print_exc()
            print(f"="*60)
            # Still return success to user (security - don't reveal if email exists)
        
        return jsonify({
            'message': 'If the email exists, a password reset link has been sent'
        }), 200
        
    except Exception as e:
        print(f"❌ Forgot password error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'Unable to process request. Please try again later.'
        }), 500
        
    except Exception as e:
        print(f"Forgot password error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'Unable to process request. Please try again later.'
        }), 500

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset user password with token"""
    try:
        data = request.get_json()
        token = data.get('token')
        new_password = data.get('new_password') or data.get('password') 
        
        print(f"============================================================")
        print(f"PASSWORD RESET ATTEMPT")
        print(f"Token received: {token[:50]}..." if token else "No token")
        print(f"============================================================")
        
        if not token or not new_password:
            return jsonify({'error': 'Token and new password are required'}), 400
        
        # Validate password length
        if len(new_password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters'}), 400
        
        # Verify token using the same function as email verification
        email = verify_email_token(token, salt='password-reset', max_age=3600)
        
        if not email:
            print("❌ Invalid or expired token")
            return jsonify({'error': 'Reset link has expired or is invalid. Please request a new one.'}), 400
        
        print(f"✅ Token verified for email: {email}")
        
        # Find user by email in Supabase
        supabase = get_supabase()
        user_response = supabase.table('users').select('*').eq('email', email).execute()
        
        if not user_response.data:
            print(f"❌ User not found for email: {email}")
            return jsonify({'error': 'User not found'}), 404
        
        user = user_response.data[0]
        
        # Hash new password with bcrypt
        new_password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Update password in Supabase
        update_response = supabase.table('users')\
            .update({'password_hash': new_password_hash})\
            .eq('email', email)\
            .execute()
        
        if not update_response.data:
            print(f"❌ Failed to update password for {email}")
            return jsonify({'error': 'Failed to reset password'}), 500
        
        print(f"✅ Password reset successful for {email} (username: {user['username']})")
        
        return jsonify({
            'message': 'Password reset successful! You can now login with your new password.'
        }), 200
        
    except Exception as e:
        print(f"❌ Password reset error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to reset password'}), 500


# Optional: Add a verify-reset-token endpoint if you want to check token validity before showing the form
@auth_bp.route('/verify-reset-token/<token>', methods=['GET'])
def verify_reset_token_endpoint(token):
    """Verify if a reset token is valid (optional endpoint)"""
    try:
        # Verify token using the same function as email verification
        email = verify_email_token(token, salt='password-reset', max_age=3600)
        
        if not email:
            return jsonify({'valid': False, 'error': 'Invalid or expired token'}), 400
        
        # Check if user exists in Supabase
        supabase = get_supabase()
        user_response = supabase.table('users').select('*').eq('email', email).execute()
        
        if not user_response.data:
            return jsonify({'valid': False, 'error': 'User not found'}), 404
        
        return jsonify({
            'valid': True,
            'email': email
        }), 200
            
    except Exception as e:
        print(f"Token verification error: {e}")
        return jsonify({'valid': False, 'error': 'Verification failed'}), 500