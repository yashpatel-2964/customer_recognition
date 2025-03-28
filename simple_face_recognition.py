import cv2
import numpy as np
import face_recognition
import time
import os
import requests
from datetime import datetime
import uuid
from db_connection import get_database
import traceback
import logging
from config import Config, API_CUSTOMER_DETECTION

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('face_recognition.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('face_recognition')

# Database connection
try:
    db = get_database()
    customers_collection = db['customers']
    logger.info("Successfully connected to MongoDB")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    raise

# API endpoint for sending customer ID
API_ENDPOINT = API_CUSTOMER_DETECTION

# Face comparison distance threshold
RECOGNITION_THRESHOLD = Config.RECOGNITION_THRESHOLD

def get_all_customer_embeddings():
    """Fetch all customer face embeddings from database"""
    try:
        customers = list(customers_collection.find({}))
        
        known_face_encodings = []
        known_face_ids = []
        
        for customer in customers:
            try:
                if "face_embedding" in customer and customer["face_embedding"]:
                    known_face_encodings.append(np.array(customer["face_embedding"]))
                    known_face_ids.append(customer["customer_id"])
            except Exception as e:
                logger.error(f"Error processing customer {customer.get('customer_id', 'unknown')}: {e}")
        
        logger.info(f"Loaded {len(known_face_ids)} customers with face embeddings from database")
        return known_face_encodings, known_face_ids
    except Exception as e:
        logger.error(f"Failed to get customer embeddings: {e}")
        return [], []

def send_customer_id_to_api(customer_id, max_retries=3):
    """Send customer ID to the API endpoint with retry mechanism"""
    for attempt in range(max_retries):
        try:
            # Use a short timeout to prevent hanging
            verify_ssl = not API_ENDPOINT.startswith('http://localhost')
            response = requests.post(
                API_ENDPOINT,
                json={"customer_id": customer_id},
                timeout=3,
                headers={"Content-Type": "application/json"},
                verify=verify_ssl
            )
            if response.status_code == 200:
                logger.info(f"API Response: {response.status_code}")
                return True
            else:
                logger.warning(f"API returned status code {response.status_code}: {response.text}")
        except requests.exceptions.Timeout:
            logger.warning(f"API request timed out (attempt {attempt+1}/{max_retries})")
        except requests.exceptions.ConnectionError:
            logger.warning(f"Connection error (attempt {attempt+1}/{max_retries}). Make sure the Flask app is running at {API_ENDPOINT}")
        except requests.exceptions.SSLError:
            logger.warning("SSL verification failed. Using insecure connection for localhost.")
            return send_customer_id_to_api_insecure(customer_id)
        except Exception as e:
            logger.error(f"Failed to send data to API: {e}")
        
        # Wait before retrying with exponential backoff
        if attempt < max_retries - 1:
            time.sleep(1 * (2 ** attempt))
    
    return False

def send_customer_id_to_api_insecure(customer_id):
    """Alternative method for localhost connections without SSL verification"""
    try:
        response = requests.post(
            API_ENDPOINT,
            json={"customer_id": customer_id},
            timeout=3,
            headers={"Content-Type": "application/json"},
            verify=False
        )
        logger.info(f"API Response (insecure): {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Failed to send data to API (insecure): {e}")
        return False

def register_new_customer(face_img, face_encoding):
    """Register a new customer with face image and encoding"""
    try:
        os.makedirs("auto_captured", exist_ok=True)
        
        new_id = f"C{int(time.time())}"
        img_path = f"auto_captured/{new_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
        
        cv2.imwrite(img_path, face_img)
        
        customers_collection.insert_one({
            "customer_id": new_id,
            "face_embedding": face_encoding.tolist(),
            "registration_date": datetime.now(),
            "last_seen_date": datetime.now(),
            "visit_count": 1,
            "face_images": [{
                "image_id": str(uuid.uuid4()),
                "capture_date": datetime.now(),
                "image_path": img_path
            }]
        })
        logger.info(f"Registered new customer: {new_id}")
        return new_id
    except Exception as e:
        logger.error(f"Error registering new customer: {e}")
        traceback.print_exc()
        return None

def update_customer(customer_id, face_img):
    """Update customer with new face image"""
    try:
        os.makedirs("auto_captured", exist_ok=True)
        
        img_path = f"auto_captured/{customer_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
        cv2.imwrite(img_path, face_img)
        
        customers_collection.update_one(
            {"customer_id": customer_id},
            {
                "$set": {"last_seen_date": datetime.now()},
                "$inc": {"visit_count": 1},
                "$push": {
                    "face_images": {
                        "image_id": str(uuid.uuid4()),
                        "capture_date": datetime.now(),
                        "image_path": img_path
                    }
                }
            }
        )
        logger.info(f"Updated customer: {customer_id}")
        return True
    except Exception as e:
        logger.error(f"Error updating customer {customer_id}: {e}")
        traceback.print_exc()
        return False

def run_face_recognition():
    logger.info("Starting face recognition system...")
    
    # Try different camera indices
    camera_indices = [0, 1]  # Try these camera indices
    camera = None
    
    for index in camera_indices:
        try:
            camera = cv2.VideoCapture(index)
            if camera.isOpened():
                logger.info(f"Camera initialized successfully with index {index}!")
                break
        except Exception as e:
            logger.error(f"Failed to open camera with index {index}: {e}")
    
    if camera is None or not camera.isOpened():
        logger.error("Error: Could not open any camera. Please check your webcam connection.")
        return
    
    try:
        known_face_encodings, known_face_ids = get_all_customer_embeddings()
    except Exception as e:
        logger.error(f"Error loading face embeddings: {e}")
        traceback.print_exc()
        known_face_encodings, known_face_ids = [], []
    
    last_detection = {}
    cooldown_time = Config.DETECTION_COOLDOWN  # seconds between detections of same person
    api_failure_count = 0  # Track API failures
    max_api_failures = 5  # Maximum consecutive API failures before pausing API calls
    last_api_reset = time.time()
    
    # For performance optimization
    process_this_frame = True
    
    while True:
        ret, frame = camera.read()
        if not ret:
            logger.warning("Failed to capture frame")
            time.sleep(0.1)  # Short delay before retrying
            continue
        
        # Only process every other frame to save CPU
        if process_this_frame:
            # Resize frame for faster processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            # Find faces
            face_locations = face_recognition.face_locations(rgb_small_frame)
            
            # Only compute encodings if faces are found (optimization)
            if face_locations:
                face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
                
                # Process each face
                for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                    # Scale back up face coordinates
                    top *= 4
                    right *= 4
                    bottom *= 4
                    left *= 4
                    
                    # Extract face image
                    face_img = frame[top:bottom, left:right].copy()
                    
                    # Check for match with known faces
                    best_match_index = None
                    best_match_distance = 1.0
                    
                    if known_face_encodings:
                        try:
                            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                            best_match_index = np.argmin(face_distances)
                            best_match_distance = face_distances[best_match_index]
                        except Exception as e:
                            logger.error(f"Error computing face distances: {e}")
                            continue
                    
                    current_time = time.time()
                    
                    # Reset API failure count periodically
                    if current_time - last_api_reset > 30:
                        api_failure_count = 0
                        last_api_reset = current_time
                    
                    # If match found
                    if best_match_index is not None and best_match_distance < RECOGNITION_THRESHOLD:
                        customer_id = known_face_ids[best_match_index]
                        
                        # Check if we haven't detected this person recently
                        if customer_id not in last_detection or (current_time - last_detection[customer_id]) > cooldown_time:
                            # Update last detection time
                            last_detection[customer_id] = current_time
                            
                            # Update customer data
                            update_customer(customer_id, face_img)
                            
                            # Send to API if API is responding
                            if api_failure_count < max_api_failures:
                                api_success = send_customer_id_to_api(customer_id)
                                if not api_success:
                                    api_failure_count += 1
                                    if api_failure_count >= max_api_failures:
                                        logger.warning(f"API failed {max_api_failures} times in a row. Pausing API calls.")
                                else:
                                    api_failure_count = 0  # Reset on success
                        
                        # Draw green box for known customer
                        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                        cv2.putText(frame, f"ID: {customer_id}", (left, top - 10), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)
                    else:
                        # New customer
                        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                        cv2.putText(frame, "New Customer", (left, top - 10), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)
                        
                        # Register new customer
                        new_id = register_new_customer(face_img, face_encoding)
                        
                        if new_id:
                            # Send to API if API is responding
                            if api_failure_count < max_api_failures:
                                api_success = send_customer_id_to_api(new_id)
                                if not api_success:
                                    api_failure_count += 1
                                else:
                                    api_failure_count = 0  # Reset on success
                            
                            # Add to known faces
                            known_face_encodings.append(face_encoding)
                            known_face_ids.append(new_id)
                            
                            # Update last detection time
                            last_detection[new_id] = current_time
        
        process_this_frame = not process_this_frame
        
        # Display the resulting frame with customer ID
        cv2.imshow('Customer Recognition System', frame)
        
        # Hit 'q' to exit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Release the camera and close windows
    camera.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    try:
        run_face_recognition()
    except KeyboardInterrupt:
        logger.info("Face recognition stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        traceback.print_exc()