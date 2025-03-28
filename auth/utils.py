# File: D:\customer_recognition\auth\utils.py

import jwt
import datetime
import re
from functools import wraps
from flask import request, jsonify, current_app, redirect, url_for, session
from config import Config
import bcrypt

def generate_password_hash(password):
    """Hash passwords using bcrypt with salt"""
    # Generate a random salt and hash the password
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode(), salt)
    return hashed.decode('utf-8')

def check_password_hash(hashed_password, password):
    """Check if a password matches its hash using bcrypt"""
    return bcrypt.checkpw(password.encode(), hashed_password.encode())

def generate_token(employee_id, role, expiration=3600):
    """Generate JWT token for authentication"""
    payload = {
        'sub': employee_id,
        'role': role,
        'exp': datetime.datetime.utcnow() + datetime.datetime.timedelta(seconds=expiration),
        'iat': datetime.datetime.utcnow()
    }
    
    return jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm='HS256')

def decode_token(token):
    """Decode JWT token and return payload"""
    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None, "Token expired. Please log in again."
    except jwt.InvalidTokenError:
        return None, "Invalid token. Please log in again."

def token_required(f):
    """Decorator to protect routes that require authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check if token exists in various locations
        if 'Authorization' in request.headers:
            try:
                auth_header = request.headers['Authorization']
                token = auth_header.split(" ")[1]  # Extract the token from "Bearer <token>"
            except IndexError:
                return redirect(url_for('auth.login_page', error="Invalid authorization header"))
        elif 'token' in session:
            token = session['token']
        elif 'token' in request.cookies:
            token = request.cookies.get('token')
            
        if not token:
            return redirect(url_for('auth.login_page'))
        
        try:
            payload = decode_token(token)
            if not payload or isinstance(payload, tuple):
                return redirect(url_for('auth.login_page', error=payload[1] if isinstance(payload, tuple) else "Invalid token"))
                
            # Get employee from database
            from db_connection import get_database
            db = get_database()
            current_user = db['employees'].find_one({"employee_id": payload['sub']})
            
            if not current_user:
                return redirect(url_for('auth.login_page', error="User not found"))
                
            return f(current_user, *args, **kwargs)
        except Exception as e:
            return redirect(url_for('auth.login_page', error="Authentication error"))
            
    return decorated

def admin_required(f):
    """Decorator to protect routes that require admin privileges"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check if token exists in various locations
        if 'Authorization' in request.headers:
            try:
                auth_header = request.headers['Authorization']
                token = auth_header.split(" ")[1]
            except IndexError:
                return redirect(url_for('auth.login_page', error="Invalid authorization header"))
        elif 'token' in session:
            token = session['token']
        elif 'token' in request.cookies:
            token = request.cookies.get('token')
            
        if not token:
            return redirect(url_for('auth.login_page'))
        
        try:
            payload = decode_token(token)
            if not payload or isinstance(payload, tuple):
                return redirect(url_for('auth.login_page', error=payload[1] if isinstance(payload, tuple) else "Invalid token"))
                
            # Check if role is admin
            if payload['role'] != 'admin':
                return redirect(url_for('dashboard', error="Admin privileges required"))
                
            # Get employee from database
            from db_connection import get_database
            db = get_database()
            current_user = db['employees'].find_one({"employee_id": payload['sub']})
            
            if not current_user:
                return redirect(url_for('auth.login_page', error="User not found"))
                
            return f(current_user, *args, **kwargs)
        except Exception as e:
            return redirect(url_for('auth.login_page', error="Authentication error"))
            
    return decorated

def validate_password(password):
    """
    Validate password meets requirements:
    - At least 8 characters long
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one digit
    - Contains at least one special character
    """
    if len(password) < 8:
        return False
        
    # Check for uppercase letter
    if not re.search(r'[A-Z]', password):
        return False
        
    # Check for lowercase letter
    if not re.search(r'[a-z]', password):
        return False
        
    # Check for digit
    if not re.search(r'\d', password):
        return False
        
    # Check for special character
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
        
    return True

def is_valid_employee_id(employee_id):
    """Check if employee ID is valid format"""
    # Simple validation - employee ID should start with 'emp' or 'admin' followed by numbers
    return bool(re.match(r'^(emp|admin)\d{4,6}$', employee_id))