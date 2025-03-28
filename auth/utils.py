# File: D:\customer_recognition\auth\utils.py

import jwt
import datetime
import re
from functools import wraps
from flask import request, jsonify, current_app
from config import Config

def generate_password_hash(password):
    """Simple function to hash passwords - in production use a proper library like bcrypt"""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

def check_password_hash(hashed_password, password):
    """Check if a password matches its hash"""
    import hashlib
    return hashed_password == hashlib.sha256(password.encode()).hexdigest()

def generate_token(user_id, role='employee'):
    """Generate JWT token for authentication"""
    payload = {
        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=Config.JWT_ACCESS_TOKEN_EXPIRES),
        'iat': datetime.datetime.utcnow(),
        'sub': user_id,
        'role': role
    }
    return jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm='HS256')

def decode_token(token):
    """Decode JWT token"""
    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return {'error': 'Token expired. Please log in again.'}
    except jwt.InvalidTokenError:
        return {'error': 'Invalid token. Please log in again.'}

def token_required(f):
    """Decorator to protect routes that require authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check if token is in headers
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'message': 'Token is missing or invalid'}), 401
        
        # Check if token is in cookies
        if not token and request.cookies.get('token'):
            token = request.cookies.get('token')
        
        # Check if token is in session
        if not token and 'token' in request.cookies:
            token = request.cookies.get('token')
            
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
            
        try:
            data = decode_token(token)
            if 'error' in data:
                return jsonify({'message': data['error']}), 401
            current_user = data['sub']
        except:
            return jsonify({'message': 'Token is invalid'}), 401
            
        return f(current_user, *args, **kwargs)
    return decorated

def admin_required(f):
    """Decorator to protect routes that require admin privileges"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check if token is in headers
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'message': 'Token is missing or invalid'}), 401
        
        # Check if token is in cookies
        if not token and request.cookies.get('token'):
            token = request.cookies.get('token')
            
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
            
        try:
            data = decode_token(token)
            if 'error' in data:
                return jsonify({'message': data['error']}), 401
                
            if data['role'] != 'admin':
                return jsonify({'message': 'Admin privileges required'}), 403
                
            current_user = data['sub']
        except:
            return jsonify({'message': 'Token is invalid'}), 401
            
        return f(current_user, *args, **kwargs)
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
    
    # Check for uppercase
    if not re.search(r'[A-Z]', password):
        return False
    
    # Check for lowercase
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
    """Check if the employee ID is within the valid range"""
    # Check the format is empXXXX
    if not employee_id.startswith('emp'):
        return False
    
    try:
        emp_num = int(employee_id[3:])
        return Config.EMPLOYEE_ID_MIN <= emp_num <= Config.EMPLOYEE_ID_MAX
    except ValueError:
        return False