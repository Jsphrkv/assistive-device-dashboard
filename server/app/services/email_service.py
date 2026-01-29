import os
from flask import current_app
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
import traceback

# Load environment variables at module level
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'verzosaj08@gmail.com')
MAIL_DISPLAY_NAME = os.getenv('MAIL_DISPLAY_NAME', 'Assistive Device Dashboard')
FRONTEND_URL = os.getenv('FRONTEND_URL', 'https://assistive-device-dashboard.vercel.app')

def send_verification_email(email, username, token):
    """Send email verification link via SendGrid"""
    try:
        # Verify API key is present
        if not SENDGRID_API_KEY:
            print("❌ SENDGRID_API_KEY not found in environment variables!")
            return False
        
        verify_url = f"{FRONTEND_URL}/verify-email?token={token}"
        
        print(f"📧 Attempting to send verification email to {email}...")
        print(f"📧 Using SendGrid from: {SENDGRID_FROM_EMAIL}")
        
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
        
        message = Mail(
            from_email=Email(SENDGRID_FROM_EMAIL, SENDGRID_DISPLAY_NAME),
            to_emails=To(email),
            subject='Verify Your Email - Assistive Device Dashboard',
            html_content=Content("text/html", html_body)
        )
        
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        
        print(f"✅ Verification email sent to {email} (Status: {response.status_code})")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send verification email: {e}")
        traceback.print_exc()
        return False

def send_password_reset_email(email, username, token):
    """Send password reset link via SendGrid"""
    try:
        # Verify API key is present
        if not SENDGRID_API_KEY:
            print("❌ SENDGRID_API_KEY not found in environment variables!")
            return False
        
        reset_url = f"{FRONTEND_URL}/reset-password?token={token}"
        
        print(f"📧 Attempting to send password reset email to {email}...")
        print(f"📧 Using SendGrid from: {SENDGRID_FROM_EMAIL}")
        
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
        
        message = Mail(
            from_email=Email(SENDGRID_FROM_EMAIL, SENDGRID_DISPLAY_NAME),
            to_emails=To(email),
            subject='Reset Your Password - Assistive Device Dashboard',
            html_content=Content("text/html", html_body)
        )
        
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        
        print(f"✅ Password reset email sent to {email} (Status: {response.status_code})")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send password reset email: {e}")
        traceback.print_exc()
        return False