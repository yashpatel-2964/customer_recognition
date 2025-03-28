from flask import Flask, request, jsonify
import requests
import json
import os
from datetime import datetime

app = Flask(__name__)

# Keep track of detected customers to avoid duplicates
detected_customers = set()

@app.route('/identify_customer', methods=['POST'])
def identify_customer():
    data = request.json
    customer_id = data.get("customer_id")
    print(f"Customer {customer_id} identified!")
    
    # Track this detection
    is_new = customer_id not in detected_customers
    detected_customers.add(customer_id)
    
    # Forward this to your main app
    try:
        # Send to the main Flask app on port 5001
        response = requests.post(
            "http://127.0.0.1:5001/api/customer_detected",
            json={"customer_id": customer_id},
            timeout=5
        )
        print(f"Forwarded to main app: {response.status_code}")
        
        # Log the entire response for debugging
        print(f"Response content: {response.text}")
    except Exception as e:
        print(f"Failed to forward to main app: {e}")
    
    # Send a mock response
    mock_bill = {"C100001": 125.50, "C100002": 87.25}.get(customer_id, 50.00)
    
    return jsonify({
        "status": "success",
        "customer_id": customer_id,
        "predicted_bill": f"${mock_bill:.2f}",
        "is_new_detection": is_new
    })

# Simple endpoint to test if server is running
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "server": "face detection mock api"})
    
if __name__ == '__main__':
    print("Starting mock API server on http://127.0.0.1:5000")
    app.run(debug=True, port=5000)