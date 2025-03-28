import face_recognition
import os
import cv2
import numpy as np
from db_connection import get_database
from datetime import datetime
import uuid

def extract_face_embeddings():
    db = get_database()
    customers_collection = db['customers']
    
    # Path to the folder containing person folders
    base_dir = 'face_data/persons'
    person_folders = os.listdir(base_dir)
    
    print(f"Found {len(person_folders)} customer folders")
    
    for person_folder in person_folders:
        person_path = os.path.join(base_dir, person_folder)
        
        # Skip if not a directory
        if not os.path.isdir(person_path):
            continue
        
        print(f"Processing {person_folder}...")
        person_id = person_folder  # Using folder name as person ID
        
        # Check if customer already exists in database
        existing_customer = customers_collection.find_one({"customer_id": person_id})
        if existing_customer:
            print(f"Customer {person_id} already exists in database, skipping...")
            continue
        
        # List to store all embeddings for this person
        all_embeddings = []
        face_images = []
        
        # Process each image in the person's folder
        for img_file in os.listdir(person_path):
            img_path = os.path.join(person_path, img_file)
            
            # Skip if not an image
            if not img_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue
                
            try:
                print(f"  Processing image: {img_path}")
                
                # Load image using face_recognition
                image = face_recognition.load_image_file(img_path)
                
                # Find all faces in the image
                face_locations = face_recognition.face_locations(image)
                
                # If no face found, skip this image
                if not face_locations:
                    print(f"  No face found in {img_path}, skipping...")
                    continue
                
                # Get face encodings (embeddings)
                face_encodings = face_recognition.face_encodings(image, face_locations)
                
                # Use only the first face if multiple faces are detected
                if face_encodings:
                    # Convert numpy array to list for MongoDB storage
                    embedding = face_encodings[0].tolist()
                    all_embeddings.append(embedding)
                    
                    # Add image info
                    image_id = str(uuid.uuid4())
                    face_images.append({
                        "image_id": image_id,
                        "capture_date": datetime.now(),
                        "image_path": img_path
                    })
                    
                    print(f"  Successfully extracted face embedding")
            except Exception as e:
                print(f"  Error processing {img_path}: {e}")
        
        # Skip if no valid embeddings were extracted
        if not all_embeddings:
            print(f"No valid embeddings found for {person_id}, skipping...")
            continue
        
        # Calculate average embedding for better matching
        average_embedding = np.mean(all_embeddings, axis=0).tolist()
        
        # Insert person data into MongoDB
        customers_collection.insert_one({
            "customer_id": person_id,
            "face_embedding": average_embedding,
            "all_embeddings": all_embeddings,  # Store all for future use
            "registration_date": datetime.now(),
            "last_seen_date": datetime.now(),
            "visit_count": 0,
            "face_images": face_images
        })
        
        print(f"Added {person_id} to database with {len(all_embeddings)} face embeddings")

if __name__ == "__main__":
    extract_face_embeddings()