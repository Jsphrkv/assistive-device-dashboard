import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production-12345')
    
    # Supabase
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
    
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
    JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
    JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', 24))

      # Email Configuration ✅ NEW
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')  # ← Must be set in .env
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')  # ← Must be set in .env
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', os.getenv('MAIL_USERNAME'))
    MAIL_DISPLAY_NAME = os.getenv('MAIL_DISPLAY_NAME', 'Assistive Device Dashboard')
    
    # Frontend URL ✅ NEW
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'https://assistive-device-dashboard.vercel.app')
    
    # Device
    DEVICE_API_KEY = os.getenv('DEVICE_API_KEY', 'device-api-key')
    
    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'https://assistive-device-dashboard.vercel.app').split(',')
    
    # Upload
    MAX_UPLOAD_SIZE = int(os.getenv('MAX_UPLOAD_SIZE', 10485760))
    ALLOWED_EXTENSIONS = set(os.getenv('ALLOWED_EXTENSIONS', 'jpg,jpeg,png').split(','))
    
    # ML
    MODEL_PATH = os.getenv('MODEL_PATH', './models/model.tflite')
    CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', 0.5))
    DISTANCE_THRESHOLD_CM = int(os.getenv('DISTANCE_THRESHOLD_CM', 100))

    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}