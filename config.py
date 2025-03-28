# File: D:\customer_recognition\config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-for-jwt'
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb://localhost:27017/face_recognition_db'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'your-jwt-secret-key'
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour
    
    # Google OAuth configuration
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    GOOGLE_CALLBACK_URL = "https://localhost:5001/api/auth/google/callback"
    
    # Employee ID range - ADDING THESE TO FIX THE ERROR
    EMPLOYEE_ID_MIN = 1001
    EMPLOYEE_ID_MAX = 1050

# Base directory of the project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# MongoDB configuration
MONGO_URI = os.getenv('MONGO_URI')

# Flask app configuration
DEBUG = True
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')

# Face recognition settings
RECOGNITION_THRESHOLD = 0.6  # Lower is stricter
CAMERA_INDEX = 0  # Camera device index
DETECTION_COOLDOWN = 10  # Seconds between detecting same customer

# API Endpoints
API_ENDPOINT = 'https://127.0.0.1:5001/identify_customer'

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
DASHBOARD_REFRESH_INTERVAL = 30  # seconds