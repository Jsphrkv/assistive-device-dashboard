from sendgrid import SendGridAPIClient
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv('SENDGRID_API_KEY')
print(f"API Key present: {bool(api_key)}")
print(f"API Key starts with SG.: {api_key.startswith('SG.') if api_key else False}")

try:
    sg = SendGridAPIClient(api_key)
    print("✅ SendGrid client initialized successfully")
except Exception as e:
    print(f"❌ Error: {e}")