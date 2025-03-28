# File: D:\customer_recognition\config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable is required")
        
    MONGO_URI = os.environ.get('MONGO_URI')
    if not MONGO_URI:
        raise ValueError("MONGO_URI environment variable is required")
        
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    if not JWT_SECRET_KEY:
        raise ValueError("JWT_SECRET_KEY environment variable is required")
        
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour
    
    # Google OAuth configuration - optional
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    GOOGLE_CALLBACK_URL = os.environ.get('GOOGLE_CALLBACK_URL', "https://localhost:5001/api/auth/google/callback")
    
    # Employee ID range
    EMPLOYEE_ID_MIN = int(os.environ.get('EMPLOYEE_ID_MIN', 1001))
    EMPLOYEE_ID_MAX = int(os.environ.get('EMPLOYEE_ID_MAX', 1050))
    
    # Flask configuration
    DEBUG = os.environ.get('FLASK_ENV') == 'development'

# Base directory of the project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Face recognition settings
RECOGNITION_THRESHOLD = float(os.environ.get('RECOGNITION_THRESHOLD', 0.6))  # Lower is stricter
CAMERA_INDEX = int(os.environ.get('CAMERA_INDEX', 0))  # Camera device index
DETECTION_COOLDOWN = int(os.environ.get('DETECTION_COOLDOWN', 10))  # Seconds between detecting same customer

# API Endpoints
API_ENDPOINT = os.environ.get('API_ENDPOINT', 'https://127.0.0.1:5001/identify_customer')
API_CUSTOMER_DETECTION = os.environ.get('API_CUSTOMER_DETECTION', 'https://127.0.0.1:5001/api/customer_detected')

# Path settings
FACE_DATA_DIR = os.path.join(BASE_DIR, 'face_data', 'persons')
AUTO_CAPTURE_DIR = os.path.join(BASE_DIR, 'auto_captured')
STATIC_DIR = os.path.join(BASE_DIR, 'static')
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
MODEL_DIR = os.path.join(BASE_DIR, 'models')
DATA_DIR = os.path.join(BASE_DIR, 'data')

# Ensure required directories exist
for directory in [AUTO_CAPTURE_DIR, STATIC_DIR, TEMPLATES_DIR, MODEL_DIR, DATA_DIR]:
    os.makedirs(directory, exist_ok=True)

# Model settings
MODEL_PATH = os.path.join(MODEL_DIR, 'billing_model.pkl')
CUSTOMER_DATA_PATH = os.path.join(DATA_DIR, 'customer_data.json')

# Auto-refresh settings for dashboard
DASHBOARD_REFRESH_INTERVAL = int(os.environ.get('DASHBOARD_REFRESH_INTERVAL', 30))  # seconds

# Security settings
CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', 'http://localhost:5001,https://localhost:5001').split(',')
SESSION_COOKIE_SECURE = True  # Only send cookies over HTTPS
SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access to cookies
SESSION_COOKIE_SAMESITE = 'Lax'  # Restrict cookie sending to same-site requests