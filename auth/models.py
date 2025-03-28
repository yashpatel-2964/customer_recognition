# File: D:\customer_recognition\auth\models.py

from datetime import datetime
from db_connection import get_database
from auth.utils import generate_password_hash, check_password_hash, validate_password, is_valid_employee_id
from config import Config

class Employee:
    """Employee model for handling employee authentication"""
    
    @staticmethod
    def create_employee(employee_id, password, name, email, role='employee'):
        """Create a new employee"""
        if not is_valid_employee_id(employee_id):
            return {"success": False, "message": "Invalid employee ID format"}
        
        if not validate_password(password):
            return {"success": False, "message": "Password doesn't meet security requirements"}
        
        db = get_database()
        
        # Check if employee already exists
        existing_employee = db['employees'].find_one({"employee_id": employee_id})
        if existing_employee:
            return {"success": False, "message": "Employee ID already exists"}
        
        # Check if email already exists
        existing_email = db['employees'].find_one({"email": email})
        if existing_email:
            return {"success": False, "message": "Email already in use"}
        
        # Create new employee document
        new_employee = {
            "employee_id": employee_id,
            "password_hash": generate_password_hash(password),
            "name": name,
            "email": email,
            "role": role,
            "created_at": datetime.utcnow(),
            "last_login": None
        }
        
        # Insert into database
        db['employees'].insert_one(new_employee)
        
        return {"success": True, "message": "Employee created successfully"}
    
    @staticmethod
    def authenticate(employee_id, password):
        """Authenticate an employee with ID and password"""
        db = get_database()
        
        # Find employee by ID
        employee = db['employees'].find_one({"employee_id": employee_id})
        
        if not employee:
            return None
        
        # Check password
        if check_password_hash(employee['password_hash'], password):
            # Update last login time
            db['employees'].update_one(
                {"employee_id": employee_id},
                {"$set": {"last_login": datetime.utcnow()}}
            )
            
            # Return employee info (excluding password hash)
            return {
                "employee_id": employee['employee_id'],
                "name": employee['name'],
                "email": employee['email'],
                "role": employee['role']
            }
        
        return None

    @staticmethod
    def get_by_id(employee_id):
        """Get employee by ID"""
        db = get_database()
        employee = db['employees'].find_one({"employee_id": employee_id})
        
        if not employee:
            return None
        
        # Return employee info (excluding password hash)
        return {
            "employee_id": employee['employee_id'],
            "name": employee['name'],
            "email": employee['email'],
            "role": employee['role'],
            "created_at": employee['created_at'],
            "last_login": employee['last_login']
        }

    @staticmethod
    def get_by_email(email):
        """Get employee by email"""
        db = get_database()
        employee = db['employees'].find_one({"email": email})
        
        if not employee:
            return None
        
        # Return employee info (excluding password hash)
        return {
            "employee_id": employee['employee_id'],
            "name": employee['name'],
            "email": employee['email'],
            "role": employee['role']
        }
        
    @staticmethod
    def create_google_user(email, name, google_id):
        """Create or update a user with Google account"""
        db = get_database()
        
        # Check if user exists with this email
        existing_user = db['employees'].find_one({"email": email})
        
        if existing_user:
            # Update existing user with Google ID
            db['employees'].update_one(
                {"email": email},
                {"$set": {
                    "google_id": google_id,
                    "last_login": datetime.utcnow()
                }}
            )
            return existing_user
        
        # Create a new employee with a special employee ID for Google users
        # Use emp50XX format for Google users to distinguish them
        count = db['employees'].count_documents({"employee_id": {"$regex": "^emp50"}})
        new_employee_id = f"emp50{count + 1:02}"
        
        new_employee = {
            "employee_id": new_employee_id,
            "password_hash": None,  # No password for Google users
            "google_id": google_id,
            "name": name,
            "email": email,
            "role": "employee",  # Default role
            "created_at": datetime.utcnow(),
            "last_login": datetime.utcnow()
        }
        
        db['employees'].insert_one(new_employee)
        
        return {
            "employee_id": new_employee_id,
            "name": name,
            "email": email,
            "role": "employee"
        }