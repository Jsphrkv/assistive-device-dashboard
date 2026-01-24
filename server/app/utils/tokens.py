"""
Token generation and verification utilities
"""
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import os

# Get SECRET_KEY from environment or use a default for development
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production-12345')

def generate_email_token(email, salt='email-verification'):
    """
    Generate a secure token for email verification or password reset
    
    Args:
        email: User's email address
        salt: Salt for token generation (different salts for different purposes)
    
    Returns:
        str: Secure token
    """
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    return serializer.dumps(email, salt=salt)


def verify_email_token(token, salt='email-verification', max_age=3600):
    """
    Verify a token and return the email if valid
    
    Args:
        token: Token to verify
        salt: Salt used during generation (must match)
        max_age: Maximum age in seconds (default 1 hour)
    
    Returns:
        str: Email if token is valid, None otherwise
    """
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    try:
        email = serializer.loads(
            token,
            salt=salt,
            max_age=max_age
        )
        print(f"✅ Token verified successfully for: {email}")
        return email
    except SignatureExpired:
        print(f"❌ Token expired (max_age: {max_age} seconds)")
        return None
    except BadSignature:
        print("❌ Invalid token signature")
        return None
    except Exception as e:
        print(f"❌ Token verification error: {str(e)}")
        return None