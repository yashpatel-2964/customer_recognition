from flask import Flask, render_template, request, jsonify, redirect, url_for, session, Response
import os
import json
import datetime
import shutil
import requests
import uuid
import ssl
import time
import functools
import gzip
import threading
from db_connection import get_database
from auth import auth_bp
from auth.utils import token_required
from config import Config, BASE_DIR

# Create Flask application with properly configured static folder
app = Flask(__name__, 
            static_folder='static',
            static_url_path='/static')
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

# Path constants
AUTO_CAPTURED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'auto_captured')
STATIC_IMAGES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'images')
CERT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cert')

# Create directories if they don't exist
os.makedirs(AUTO_CAPTURED_DIR, exist_ok=True)
os.makedirs(STATIC_IMAGES_DIR, exist_ok=True)
os.makedirs(CERT_DIR, exist_ok=True)
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'css'), exist_ok=True)

# Global variables
latest_detections = {}  # Dictionary to store latest customer detections
customer_cooldowns = {}  # Dictionary to track customer detection cooldowns
DETECTION_COOLDOWN = 120  # 2 minutes cooldown
model = None  # Lazy-loaded model

# Create a cached database connection function
@functools.lru_cache(maxsize=1)
def get_cached_database():
    """Get a cached database connection"""
    return get_database()

def setup_db_indexes():
    """Create database indexes for faster queries"""
    try:
        db = get_cached_database()
        # Create indexes on frequently queried fields
        db['customers'].create_index('customer_id')
        db['employees'].create_index('employee_id')
        # Add index for timestamp sorting
        db['customers'].create_index('last_seen_date')
        print("Database indexes created successfully")
    except Exception as e:
        print(f"Error creating database indexes: {e}")

def run_in_thread(fn):
    """Run a function in a separate thread to avoid blocking"""
    def run(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
        return thread
    return run

# Helper functions
def get_model():
    """Lazy load the model only when needed"""
    global model
    if model is None:
        try:
            from train_model import BillingModel
            model = BillingModel()
            if not model.load_model():
                print("Training new model...")
                model.train()
            print("Model loaded successfully")
        except Exception as e:
            print(f"Error loading model: {e}")
            return None
    return model

def cleanup_cooldowns():
    """Remove expired cooldown entries"""
    current_time = datetime.datetime.now()
    expired_keys = [
        customer_id for customer_id, timestamp in customer_cooldowns.items()
        if (current_time - timestamp).total_seconds() > DETECTION_COOLDOWN
    ]
    
    for key in expired_keys:
        del customer_cooldowns[key]
    
    if expired_keys:
        print(f"Cleaned up {len(expired_keys)} expired cooldowns")

def copy_captured_images():
    """Optimized image copying with tracking"""
    if not os.path.exists(AUTO_CAPTURED_DIR):
        return
        
    # Track processed files to avoid redundant copying
    processed_marker = os.path.join(STATIC_IMAGES_DIR, '.processed_images')
    processed_files = set()
    
    if os.path.exists(processed_marker):
        try:
            with open(processed_marker, 'r') as f:
                processed_files = set(line.strip() for line in f)
        except:
            pass
    
    # Only process new files
    new_files = []
    start_time = time.time()
    
    for filename in os.listdir(AUTO_CAPTURED_DIR):
        if filename.endswith(('.jpg', '.jpeg', '.png')) and filename not in processed_files:
            src_path = os.path.join(AUTO_CAPTURED_DIR, filename)
            dst_path = os.path.join(STATIC_IMAGES_DIR, filename)
            
            if not os.path.exists(dst_path):
                try:
                    shutil.copy2(src_path, dst_path)
                    new_files.append(filename)
                    processed_files.add(filename)
                except Exception as e:
                    print(f"Error copying {filename}: {e}")
    
    # Update processed files
    if new_files:
        with open(processed_marker, 'w') as f:
            for filename in processed_files:
                f.write(f"{filename}\n")
        
        elapsed = time.time() - start_time
        print(f"Copied {len(new_files)} new images in {elapsed:.3f}s")

# Enable response compression and add caching
@app.after_request
def add_compression_and_caching(response):
    # Only compress text responses
    if response.mimetype.startswith(('text/', 'application/json', 'application/javascript')):
        accept_encoding = request.headers.get('Accept-Encoding', '')
        if 'gzip' in accept_encoding:
            response.data = gzip.compress(response.data)
            response.headers['Content-Encoding'] = 'gzip'
            response.headers['Content-Length'] = len(response.data)
    
    # Cache static files
    if request.path.startswith('/static/'):
        response.headers['Cache-Control'] = 'public, max-age=86400'  # 1 day
    
    # Add CORS headers to allow requests from approved origins
    if request.method == 'OPTIONS':
        # Handle preflight requests
        origin = request.headers.get('Origin', '')
        if origin in Config.CORS_ALLOWED_ORIGINS:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            response.headers['Access-Control-Max-Age'] = '3600'  # Cache preflight response for 1 hour
    elif request.headers.get('Origin') in Config.CORS_ALLOWED_ORIGINS:
        # Handle actual requests
        response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin')
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    
    return response

# Security headers for HTTPS
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'  # HSTS for 1 year
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' https://cdn.jsdelivr.net; style-src 'self' https://cdn.jsdelivr.net https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com"
    return response

# Register authentication blueprint
app.register_blueprint(auth_bp, url_prefix='/auth')

# Routes
@app.route('/')
def root():
    """Check login status and redirect accordingly"""
    if 'token' not in request.cookies and 'token' not in session:
        # No token in cookies or session, redirect to login
        return redirect(url_for('auth.login_page'))
    
    # User has a token, redirect to dashboard
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
@token_required
def dashboard(current_user):
    """Main dashboard page - requires authentication"""
    # Get recent customer detections (last 10)
    customers = list(latest_detections.values())
    customers.sort(key=lambda x: x['timestamp'], reverse=True)
    recent_customers = customers[:10]
    
    # Get most recent customer
    latest_customer = recent_customers[0] if recent_customers else None
    
    return render_template('index.html', 
                           latest_customer=latest_customer,
                           recent_customers=recent_customers,
                           current_user=current_user)

@app.route('/customer/<customer_id>')
@token_required
def customer_details(current_user, customer_id):
    """Customer details page - requires authentication"""
    db = get_cached_database()
    customer = db['customers'].find_one({"customer_id": customer_id})
    
    if not customer:
        return "Customer not found", 404
    
    # Get latest detection
    detection = latest_detections.get(customer_id, None)
    
    # Get purchase history from model data
    purchases = []
    model_instance = get_model()
    if model_instance and hasattr(model_instance, 'customer_data'):
        customer_data = model_instance.customer_data.get(customer_id, {})
        purchases = customer_data.get('purchases', [])
    
    # Get prediction
    predicted_bill = model_instance.predict(customer_id) if model_instance else 0.0
    
    return render_template('customer.html',
                          customer=customer,
                          purchases=purchases,
                          detection=detection,
                          predicted_bill=predicted_bill,
                          current_user=current_user)

@app.route('/api/customer_detected', methods=['POST', 'OPTIONS'])
def customer_detected():
    """API endpoint for when a customer is detected - with CORS support"""
    # Handle OPTIONS request for CORS preflight
    if request.method == 'OPTIONS':
        return '', 204
        
    data = request.json
    customer_id = data.get('customer_id')
    
    if not customer_id:
        return jsonify({"error": "No customer ID provided"}), 400
    
    # Process the detection immediately for faster response
    current_time = datetime.datetime.now()
    customer_cooldowns[customer_id] = current_time
    
    # Start background processing
    process_customer_detection(customer_id)
    
    # Return immediately with success
    return jsonify({
        "status": "success",
        "message": f"Processing detection for customer {customer_id}"
    })

@run_in_thread
def process_customer_detection(customer_id):
    """Process customer detection in a background thread"""
    try:
        current_time = datetime.datetime.now()
        
        # Get customer info from database
        db = get_cached_database()
        customer = db['customers'].find_one({"customer_id": customer_id})
        
        # Database operations - only perform what's absolutely necessary
        if not customer:
            # Simplified customer creation
            db['customers'].insert_one({
                "customer_id": customer_id,
                "registration_date": current_time,
                "last_seen_date": current_time,
                "visit_count": 1
            })
            visit_count = 1
        else:
            # More efficient update
            db['customers'].update_one(
                {"customer_id": customer_id},
                {"$set": {"last_seen_date": current_time},
                 "$inc": {"visit_count": 1}}
            )
            visit_count = customer.get('visit_count', 0) + 1
        
        # Find image path - simplified version
        image_path = None
        image_url = None
        
        for filename in os.listdir(AUTO_CAPTURED_DIR):
            if filename.startswith(customer_id) and filename.endswith(('.jpg', '.jpeg', '.png')):
                image_path = os.path.join(AUTO_CAPTURED_DIR, filename)
                image_url = f"/static/images/{os.path.basename(image_path)}"
                break
        
        # Only copy if needed
        if image_path and not os.path.exists(os.path.join(STATIC_IMAGES_DIR, os.path.basename(image_path))):
            try:
                shutil.copy2(image_path, os.path.join(STATIC_IMAGES_DIR, os.path.basename(image_path)))
            except Exception as e:
                print(f"Error copying image: {e}")
        
        # Get prediction lazily
        model_instance = get_model()
        predicted_bill = model_instance.predict(customer_id) if model_instance else 0.0
        
        # Update latest detections
        detection = {
            'customer_id': customer_id,
            'timestamp': current_time.isoformat(),
            'image_url': image_url,
            'predicted_bill': predicted_bill,
            'detection_time': current_time.strftime("%Y-%m-%d %H:%M:%S"),
            'visit_count': visit_count
        }
        
        latest_detections[customer_id] = detection
        print(f"Processed detection for customer {customer_id}")
    except Exception as e:
        print(f"Error processing customer detection: {e}")
        import traceback
        traceback.print_exc()

@app.route('/api/update_bill', methods=['POST'])
def api_update_bill():
    """API endpoint for updating bill amounts"""
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
        
    customer_id = data.get('customer_id')
    try:
        actual_bill = float(data.get('actual_bill', 0))
    except ValueError:
        return jsonify({"error": "Invalid bill amount"}), 400
    
    if not customer_id:
        return jsonify({"error": "Customer ID is required"}), 400
    
    # Update model with new bill
    success = False
    model_instance = get_model()
    if model_instance:
        success = model_instance.update_with_new_purchase(customer_id, actual_bill)
    
    if success:
        # Remove customer from latest_detections
        if customer_id in latest_detections:
            del latest_detections[customer_id]
        
        return jsonify({
            "status": "success",
            "message": f"Bill for {customer_id} updated to ${actual_bill:.2f}",
            "removed": True
        })
    else:
        return jsonify({
            "status": "error",
            "message": "Failed to update bill amount"
        }), 500

@app.route('/manual_lookup', methods=['POST'])
@token_required
def manual_lookup(current_user):
    """Handle manual customer lookup - requires authentication"""
    customer_id = request.form.get('customer_id')
    
    if not customer_id:
        return redirect(url_for('dashboard'))
    
    # Use cache for database lookup
    db = get_cached_database()
    customer = db['customers'].find_one({"customer_id": customer_id})
    
    # Lazily load model
    model_instance = get_model()
    
    # Get prediction
    predicted_bill = model_instance.predict(customer_id) if model_instance else 0.0
    
    # For manual lookups, always set actual_bill to None to ensure empty fields
    actual_bill = None
    
    # Find most recent image path - optimized to limit database scans
    image_path = None
    image_url = None
    if customer and 'face_images' in customer and customer['face_images']:
        try:
            # Get the most recent image (just take the last one to avoid sorting every time)
            recent_image = customer['face_images'][-1]
            image_path = recent_image.get('image_path')
            
            # Copy to static folder if needed
            if image_path and os.path.exists(image_path):
                dest_path = os.path.join(STATIC_IMAGES_DIR, os.path.basename(image_path))
                if not os.path.exists(dest_path):
                    shutil.copy2(image_path, dest_path)
                image_url = f"/static/images/{os.path.basename(image_path)}"
        except (KeyError, IndexError, TypeError) as e:
            print(f"Error getting recent image: {e}")
    
    # Create result object
    result = {
        "customer_id": customer_id,
        "predicted_bill": predicted_bill,
        "actual_bill": actual_bill,  # Always None for manual lookups
        "visit_count": customer.get('visit_count', 0) if customer else 0,
        "image_url": image_url
    }
    
    # Get recent customers for the sidebar
    customers = list(latest_detections.values())
    customers.sort(key=lambda x: x['timestamp'], reverse=True)
    recent_customers = customers[:10]
    
    # Pass to template as manual_lookup_result
    return render_template('index.html', 
                          manual_lookup_result=result,
                          recent_customers=recent_customers,
                          current_user=current_user)

@app.route('/history')
@token_required
def history(current_user):
    """Customer purchase history page - requires authentication"""
    customer_id = request.args.get('customer_id')
    
    # Get all customer IDs for dropdown - with lazy loading
    customer_ids = []
    model_instance = get_model()
    if model_instance and hasattr(model_instance, 'customer_data'):
        customer_ids = list(model_instance.customer_data.keys())
    
    if customer_id:
        # Get purchase history for selected customer
        customer_data = {}
        purchase_history = []
        
        if model_instance and hasattr(model_instance, 'customer_data'):
            customer_data = model_instance.customer_data.get(customer_id, {})
            purchase_history = customer_data.get('purchases', [])
        
        # Prepare data for chart
        dates = [p['date'] for p in purchase_history]
        amounts = [p['amount'] for p in purchase_history]
        
        chart_data = {
            "labels": dates,
            "amounts": amounts
        }
        
        # Calculate stats
        stats = {
            "avg_bill": customer_data.get('avg_bill', 0),
            "visit_count": customer_data.get('visit_count', 0),
            "next_prediction": model_instance.predict(customer_id) if model_instance else 0.0
        }
        
        return render_template('history.html',
                              customer_ids=customer_ids,
                              selected_customer=customer_id,
                              purchase_history=purchase_history,
                              chart_data=chart_data,
                              stats=stats,
                              current_user=current_user)
    else:
        return render_template('history.html',
                              customer_ids=customer_ids,
                              selected_customer=None,
                              current_user=current_user)

@app.route('/api/latest_customer', methods=['GET'])
def get_latest_customer():
    """API endpoint to get latest customer for dashboard updates"""
    try:
        # Get most recent detection
        customers = list(latest_detections.values())
        if not customers:
            return jsonify({
                "status": "no_customers",
                "message": "No customers detected yet"
            })
            
        # Sort by timestamp in descending order
        customers.sort(key=lambda x: x['timestamp'], reverse=True)
        latest_customer = customers[0]
        
        return jsonify({
            "status": "success", 
            "customer": latest_customer
        })
    except Exception as e:
        print(f"Error in get_latest_customer: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": "Error retrieving latest customer"
        }), 500
        
@app.route('/api/recent_customers', methods=['GET'])
def get_recent_customers():
    """API endpoint to get recent customers"""
    try:
        customers = list(latest_detections.values())
        customers.sort(key=lambda x: x['timestamp'], reverse=True)
        recent_customers = customers[:10]
        
        return jsonify({
            "status": "success",
            "customers": recent_customers
        })
    except Exception as e:
        print(f"Error in get_recent_customers: {e}")
        return jsonify({
            "status": "error",
            "message": "Error retrieving recent customers"
        }), 500

@app.route('/api/test_detection', methods=['POST'])
def test_detection():
    """Simple endpoint for testing detection without authentication"""
    data = request.json
    customer_id = data.get('customer_id', 'C1001')  # Default test ID
    
    current_time = datetime.datetime.now()
    detection = {
        'customer_id': customer_id,
        'timestamp': current_time.isoformat(),
        'image_url': '/static/images/test_image.jpg',
        'predicted_bill': 50.00,
        'detection_time': current_time.strftime("%Y-%m-%d %H:%M:%S"),
        'visit_count': 1
    }
    
    latest_detections[customer_id] = detection
    
    return jsonify({
        "status": "success",
        "message": f"Test detection added for {customer_id}"
    })

@app.route('/identify_customer', methods=['POST', 'OPTIONS'])
def identify_customer():
    """Endpoint for the face recognition script to send customer IDs"""
    # Handle OPTIONS request for CORS preflight
    if request.method == 'OPTIONS':
        return '', 204
        
    return customer_detected()

@app.route('/api/check_token', methods=['GET'])
def check_token():
    """API endpoint to check token validity"""
    if 'token' not in request.cookies and 'token' not in session:
        return jsonify({"valid": False, "message": "No token found"}), 401
        
    token = request.cookies.get('token') or session.get('token')
    
    try:
        import jwt
        # Decode the token
        jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        return jsonify({"valid": True})
    except jwt.ExpiredSignatureError:
        return jsonify({"valid": False, "message": "Token expired. Please log in again."}), 401
    except:
        return jsonify({"valid": False, "message": "Invalid token"}), 401

# Serve CSS file directly
@app.route('/static/css/style.css')
def serve_css():
    """Direct route to serve CSS file"""
    css_path = os.path.join(app.static_folder, 'css', 'style.css')
    if os.path.exists(css_path):
        with open(css_path, 'r') as f:
            css_content = f.read()
        return Response(css_content, mimetype='text/css')
    else:
        return "CSS file not found", 404

if __name__ == '__main__':
    from threading import Timer
    import ssl
    
    # Setup database indexes for better performance
    setup_db_indexes()
    
    # Schedule cooldown cleanup
    def schedule_cleanup():
        cleanup_cooldowns()
        Timer(60, schedule_cleanup).start()  # Run every minute
    
    Timer(60, schedule_cleanup).start()
    
    # Print all registered routes
    print("\nRegistered Routes:")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint} -> {rule.rule} [{', '.join(rule.methods)}]")
        
    # Copy captured images to static folder
    copy_captured_images()
    
    # Check if CSS file exists and is readable
    css_path = os.path.join(app.static_folder, 'css', 'style.css')
    if os.path.exists(css_path):
        print(f"CSS file exists at: {css_path}")
        try:
            with open(css_path, 'r') as f:
                css_size = len(f.read())
            print(f"CSS file size: {css_size} bytes")
        except Exception as e:
            print(f"Error reading CSS file: {e}")
    else:
        print(f"WARNING: CSS file does not exist at {css_path}")
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(css_path), exist_ok=True)
        print(f"Created CSS directory: {os.path.dirname(css_path)}")
    
    # Make sure we have some data
    if not os.path.exists('data/customer_data.json'):
        try:
            from generate_data import generate_customer_data
            print("Generating synthetic customer data...")
            generate_customer_data()
        except Exception as e:
            print(f"Error generating data: {e}")
            
    # Create some default employee accounts if they don't exist
    try:
        from auth.models import Employee
        from auth.utils import is_valid_employee_id
        
        db = get_cached_database()
        
        # Check if we need to create default employees
        if db['employees'].count_documents({}) == 0:
            print("Creating default employee accounts...")
            for emp_num in range(Config.EMPLOYEE_ID_MIN, Config.EMPLOYEE_ID_MAX + 1):
                employee_id = f"emp{emp_num}"
                password = f"Emp@{emp_num}"
                
                if is_valid_employee_id(employee_id):
                    Employee.create_employee(
                        employee_id=employee_id,
                        password=password,
                        name=f"Employee {emp_num}",
                        email=f"employee{emp_num}@example.com"
                    )
                    print(f"Created employee: {employee_id}")
            
            # Create an admin user
            Employee.create_employee(
                employee_id="admin1001",
                password="Admin@1001",
                name="Administrator",
                email="admin@example.com",
                role="admin"
            )
            print("Created admin user: admin1001")
    except Exception as e:
        print(f"Error creating default employees: {e}")
    
    # Check if we're in development or production mode
    if Config.DEBUG:
        # Development mode - no SSL
        print("Starting Flask application in DEVELOPMENT mode on http://127.0.0.1:5001")
        app.run(debug=True, port=5001, host='127.0.0.1', threaded=True)
    else:
        # Production mode with SSL
        print("Starting Flask application in PRODUCTION mode on https://127.0.0.1:5001")
        
        # Check for SSL certificates
        cert_path = os.path.join(CERT_DIR, 'cert.pem')
        key_path = os.path.join(CERT_DIR, 'key.pem')
        
        if not os.path.exists(cert_path) or not os.path.exists(key_path):
            print("SSL certificates not found. Generating self-signed certificates...")
            try:
                from OpenSSL import crypto
                
                # Create a key pair
                k = crypto.PKey()
                k.generate_key(crypto.TYPE_RSA, 2048)
                
                # Create a self-signed cert
                cert = crypto.X509()
                cert.get_subject().C = "US"
                cert.get_subject().ST = "State"
                cert.get_subject().L = "City"
                cert.get_subject().O = "Organization"
                cert.get_subject().OU = "Organizational Unit"
                cert.get_subject().CN = "localhost"
                cert.set_serial_number(1000)
                cert.gmtime_adj_notBefore(0)
                cert.gmtime_adj_notAfter(10*365*24*60*60)  # 10 years
                cert.set_issuer(cert.get_subject())
                cert.set_pubkey(k)
                cert.sign(k, 'sha256')
                
                # Write certificate and key to files
                with open(cert_path, "wb") as f:
                    f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
                with open(key_path, "wb") as f:
                    f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))
                    
                print("Self-signed certificates generated successfully.")
            except Exception as e:
                print(f"Error generating certificates: {e}")
                print("Running without SSL instead.")
                app.run(debug=False, port=5001, host='127.0.0.1', threaded=True)
                import sys
                sys.exit(1)
        
        # Create SSL context
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert_path, key_path)
        
        # Run with gunicorn if available (recommended for production)
        try:
            from gunicorn.app.base import BaseApplication
            
            class StandaloneApplication(BaseApplication):
                def __init__(self, app, options=None):
                    self.options = options or {}
                    self.application = app
                    super().__init__()
                
                def load_config(self):
                    for key, value in self.options.items():
                        if key in self.cfg.settings and value is not None:
                            self.cfg.set(key.lower(), value)
                
                def load(self):
                    return self.application
            
            options = {
                'bind': '127.0.0.1:5001',
                'workers': 4,
                'certfile': cert_path,
                'keyfile': key_path,
                'accesslog': '-',
                'errorlog': '-',
                'timeout': 120,
                'worker_class': 'gthread',
                'threads': 4
            }
            
            StandaloneApplication(app, options).run()
        except ImportError:
            # Fall back to Werkzeug server if gunicorn is not available
            print("Gunicorn not available, using Werkzeug server instead.")
            app.run(debug=False, port=5001, host='127.0.0.1', threaded=True, ssl_context=context)