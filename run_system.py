# run_system.py
import os
import subprocess
import time
import webbrowser
import sys

def check_and_install_dependencies():
    """Check and install required dependencies"""
    try:
        import sklearn
        import flask
        import pymongo
        import numpy
        print("All required packages are installed.")
    except ImportError as e:
        print(f"Missing dependency: {e}")
        choice = input("Do you want to install missing dependencies? (y/n): ")
        if choice.lower() == 'y':
            subprocess.run([sys.executable, "-m", "pip", "install", "scikit-learn", "flask", "pymongo", "numpy", "python-dotenv"])
            print("Dependencies installed.")
        else:
            print("Please install the missing dependencies manually.")
            sys.exit(1)

def setup_directories():
    """Create required directories"""
    dirs = ['data', 'models', 'static/css', 'static/js', 'templates', 'auto_captured']
    for dir_name in dirs:
        os.makedirs(dir_name, exist_ok=True)
        print(f"Created directory: {dir_name}")

def generate_data():
    """Generate synthetic customer data"""
    if not os.path.exists('data/customer_data.json'):
        print("Generating customer data...")
        from generate_data import generate_customer_data
        generate_customer_data()
    else:
        print("Customer data already exists.")

def train_model():
    """Train the billing prediction model"""
    if not os.path.exists('models/billing_model.pkl'):
        print("Training model...")
        from train_model import BillingModel
        model = BillingModel()
        model.train()
    else:
        print("Model already trained.")

def run_flask_app():
    """Run the Flask web application"""
    print("Starting Flask application...")
    flask_process = subprocess.Popen([sys.executable, "app.py"])
    print("Flask app started!")
    return flask_process

def main():
    """Run the complete setup and launch process"""
    print("Setting up Customer Recognition System...")
    
    # Check dependencies
    check_and_install_dependencies()
    
    # Setup directories
    setup_directories()
    
    # Generate data
    generate_data()
    
    # Train model
    train_model()
    
    # Run Flask app
    flask_process = run_flask_app()
    
    # Open browser
    time.sleep(2)  # Wait for Flask to start
    print("Opening browser...")
    webbrowser.open("https://127.0.0.1:5001/")
    
    print("\nSystem is now running!")
    print("Press Ctrl+C to stop.")
    
    try:
        # Keep running until interrupted
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping the system...")
        flask_process.terminate()
        print("System stopped.")

if __name__ == "__main__":
    main()