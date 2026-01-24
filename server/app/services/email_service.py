from flask import current_app, render_template_string
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
import traceback

mail = Mail()

def init_mail(app):
    """Initialize Flask-Mail with app"""
    mail.init_app(app)

def generate_token(email, salt='email-verification'):
    """Generate a time-sensitive token"""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=salt)

def verify_token(token, salt='email-verification', max_age=3600):
    """Verify token (default expires in 1 hour)"""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt=salt, max_age=max_age)
        return email
    except Exception as e:
        print(f"Token verification error: {e}")
        return None

def send_verification_email(email, username, token):
    """Send email verification link"""
    try:
        verify_url = f"{current_app.config['FRONTEND_URL']}/verify-email?token={token}"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                           color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; background: #667eea; color: white !important; 
                          padding: 12px 30px; text-decoration: none; border-radius: 5px; 
                          margin: 20px 0; font-weight: bold; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to Assistive Device Dashboard!</h1>
                </div>
                <div class="content">
                    <h2>Hi {username},</h2>
                    <p>Thanks for signing up! Please verify your email address to activate your account.</p>
                    <p>Click the button below to verify your email:</p>
                    <center>
                        <a href="{verify_url}" class="button">Verify Email Address</a>
                    </center>
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="color: #667eea; word-break: break-all;">{verify_url}</p>
                    <p><strong>This link will expire in 24 hours.</strong></p>
                    <p>If you didn't create an account, please ignore this email.</p>
                </div>
                <div class="footer">
                    <p>© 2026 Assistive Device Dashboard. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg = Message(
            subject="Verify Your Email - Assistive Device Dashboard",
            recipients=[email],
            html=html_body,
            sender=(current_app.config['MAIL_DISPLAY_NAME'], current_app.config['MAIL_DEFAULT_SENDER'])
        )
        
        mail.send(msg)
        print(f"✓ Verification email sent to {email}")
        return True
        
    except Exception as e:
        print(f"✗ Failed to send verification email: {e}")
        traceback.print_exc()
        return False

def send_password_reset_email(email, username, token):
    """Send password reset link"""
    try:
        reset_url = f"{current_app.config['FRONTEND_URL']}/reset-password?token={token}"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                           color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; background: #f5576c; color: white !important; 
                          padding: 12px 30px; text-decoration: none; border-radius: 5px; 
                          margin: 20px 0; font-weight: bold; }}
                .warning {{ background: #fef3c7; border-left: 4px solid #f59e0b; 
                           padding: 15px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Password Reset Request</h1>
                </div>
                <div class="content">
                    <h2>Hi {username},</h2>
                    <p>We received a request to reset your password for your Assistive Device Dashboard account.</p>
                    <p>Click the button below to reset your password:</p>
                    <center>
                        <a href="{reset_url}" class="button">Reset Password</a>
                    </center>
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="color: #f5576c; word-break: break-all;">{reset_url}</p>
                    <p><strong>This link will expire in 1 hour.</strong></p>
                    <div class="warning">
                        <strong>⚠️ Security Notice:</strong>
                        <p>If you didn't request a password reset, please ignore this email. Your password will remain unchanged.</p>
                    </div>
                </div>
                <div class="footer">
                    <p>© 2026 Assistive Device Dashboard. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg = Message(
            subject="Reset Your Password - Assistive Device Dashboard",
            recipients=[email],
            html=html_body,
            sender=(current_app.config['MAIL_DISPLAY_NAME'], current_app.config['MAIL_DEFAULT_SENDER'])
        )
        
        mail.send(msg)
        print(f"✓ Password reset email sent to {email}")
        return True
        
    except Exception as e:
        print(f"✗ Failed to send password reset email: {e}")
        traceback.print_exc()
        return False