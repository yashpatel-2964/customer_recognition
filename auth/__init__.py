# File: D:\customer_recognition\auth\__init__.py
from flask import Blueprint

# Create a blueprint for authentication routes
auth_bp = Blueprint('auth', __name__)

# Import routes to register them with the blueprint
from auth.routes import *   