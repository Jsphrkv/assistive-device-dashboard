"""
Direct test of token generation and verification
"""
import sys
import os

# Add the app directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.utils.tokens import generate_email_token, verify_email_token

# Test email
test_email = "test@example.com"

print("="*60)
print("TESTING TOKEN FUNCTIONS")
print("="*60)

# Generate token
print(f"\n1. Generating token for: {test_email}")
token = generate_email_token(test_email, salt='password-reset')
print(f"   Generated token: {token[:50]}...")
print(f"   Token length: {len(token)}")

# Verify immediately (should work)
print(f"\n2. Verifying token immediately...")
verified_email = verify_email_token(token, salt='password-reset', max_age=86400)

if verified_email:
    print(f"   ✅ SUCCESS: Token verified for {verified_email}")
else:
    print(f"   ❌ FAILED: Token verification failed")

# Try with wrong salt (should fail)
print(f"\n3. Testing with wrong salt (should fail)...")
wrong_salt = verify_email_token(token, salt='wrong-salt', max_age=86400)
if wrong_salt:
    print(f"   ❌ ERROR: This shouldn't work!")
else:
    print(f"   ✅ CORRECT: Failed as expected with wrong salt")

print("\n" + "="*60)