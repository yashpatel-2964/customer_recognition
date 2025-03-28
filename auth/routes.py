# File: D:\customer_recognition\auth\routes.py

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, make_response, session
from auth.models import Employee
from auth.utils import generate_token, token_required, admin_required
import requests
from config import Config
from urllib.parse import urlencode

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET'])
def login_page():
    """Render the login page"""
    # If user is already logged in, redirect to dashboard
    if 'token' in request.cookies:
        return redirect(url_for('dashboard'))
        
    return render_template('login.html')

@auth_bp.route('/login', methods=['POST'])
def login():
    """Handle employee login"""
    data = request.form
    
    # Get credentials from form
    employee_id = data.get('employee_id', '').lower()
    password = data.get('password', '')
    
    # Authenticate the employee
    employee = Employee.authenticate(employee_id, password)
    
    if not employee:
        return render_template('login.html', error="Invalid Employee ID or Password")
    
    # Generate token
    token = generate_token(employee['employee_id'], employee['role'])
    
    # Set cookie with token
    response = make_response(redirect(url_for('dashboard')))
    response.set_cookie('token', token, httponly=True, secure=True)
    
    return response

@auth_bp.route('/logout')
def logout():
    """Handle employee logout"""
    response = make_response(redirect(url_for('auth.login_page')))
    response.delete_cookie('token')
    return response

@auth_bp.route('/register', methods=['GET'])
def register_page():
    """Render the registration page"""
    return render_template('register.html')

@auth_bp.route('/register', methods=['POST'])
def register():
    """Handle employee registration"""
    data = request.form
    
    # Get registration data
    employee_id = data.get('employee_id', '').lower()
    password = data.get('password', '')
    confirm_password = data.get('confirm_password', '')
    name = data.get('name', '')
    email = data.get('email', '')
    
    # Validate password match
    if password != confirm_password:
        return render_template('register.html', error="Passwords do not match")
    
    # Create the employee
    result = Employee.create_employee(employee_id, password, name, email)
    
    if not result['success']:
        return render_template('register.html', error=result['message'])
    
    # Redirect to login page
    return redirect(url_for('auth.login_page', message="Registration successful! Please log in."))

@auth_bp.route('/google/login')
def google_login():
    """Initiate Google OAuth login"""
    if not Config.GOOGLE_CLIENT_ID or not Config.GOOGLE_CLIENT_SECRET:
        return render_template('login.html', error="Google login is not configured")
    
    # Build the authorization URL
    auth_params = {
        'client_id': Config.GOOGLE_CLIENT_ID,
        'redirect_uri': Config.GOOGLE_CALLBACK_URL,
        'scope': 'email profile',
        'response_type': 'code',
        'access_type': 'offline'
    }
    
    auth_url = f"https://accounts.google.com/o/oauth2/auth?{urlencode(auth_params)}"
    
    return redirect(auth_url)

@auth_bp.route('/api/auth/google/callback')
def google_callback():
    """Handle Google OAuth callback"""
    code = request.args.get('code')
    
    if not code:
        return redirect(url_for('auth.login_page', error="Google authentication failed"))
    
    # Exchange code for tokens
    token_params = {
        'client_id': Config.GOOGLE_CLIENT_ID,
        'client_secret': Config.GOOGLE_CLIENT_SECRET,
        'code': code,
        'redirect_uri': Config.GOOGLE_CALLBACK_URL,
        'grant_type': 'authorization_code'
    }
    
    token_response = requests.post('https://oauth2.googleapis.com/token', data=token_params)
    
    if token_response.status_code != 200:
        return redirect(url_for('auth.login_page', error="Failed to get access token"))
    
    token_data = token_response.json()
    access_token = token_data.get('access_token')
    
    # Get user info
    user_info_response = requests.get(
        'https://www.googleapis.com/oauth2/v2/userinfo',
        headers={'Authorization': f'Bearer {access_token}'}
    )
    
    if user_info_response.status_code != 200:
        return redirect(url_for('auth.login_page', error="Failed to get user info"))
    
    user_info = user_info_response.json()
    
    # Create or update user with Google account
    employee = Employee.create_google_user(
        email=user_info.get('email'),
        name=user_info.get('name'),
        google_id=user_info.get('id')
    )
    
    # Generate token
    token = generate_token(employee['employee_id'], employee['role'])
    
    # Set cookie with token
    response = make_response(redirect(url_for('dashboard')))
    response.set_cookie('token', token, httponly=True, secure=True)
    
    return response

@auth_bp.route('/profile')
@token_required
def profile(current_user):
    """View employee profile"""
    employee = Employee.get_by_id(current_user)
    
    if not employee:
        response = make_response(redirect(url_for('auth.login_page')))
        response.delete_cookie('token')
        return response
    
    return render_template('profile.html', employee=employee)

@auth_bp.route('/api/validate-token', methods=['GET'])
def validate_token():
    """API endpoint to validate token"""
    token = None
    
    # Check if token is in headers
    if 'Authorization' in request.headers:
        auth_header = request.headers['Authorization']
        try:
            token = auth_header.split(" ")[1]
        except IndexError:
            return jsonify({'valid': False, 'message': 'Invalid token format'}), 401
    
    # Check if token is in cookies
    if not token and request.cookies.get('token'):
        token = request.cookies.get('token')
        
    if not token:
        return jsonify({'valid': False, 'message': 'Token is missing'}), 401
        
    from auth.utils import decode_token
    data = decode_token(token)
    
    if 'error' in data:
        return jsonify({'valid': False, 'message': data['error']}), 401
        
    employee = Employee.get_by_id(data['sub'])
    if not employee:
        return jsonify({'valid': False, 'message': 'User not found'}), 401
        
    return jsonify({
        'valid': True,
        'user': {
            'employee_id': employee['employee_id'],
            'name': employee['name'],
            'role': employee['role'],
            'email': employee['email']
        }
    })