# Customer Recognition System

A system that uses face recognition to identify customers, predict their spending, and track purchase history.

## Features

- Face recognition for customer identification
- Purchase prediction using machine learning
- Customer purchase history tracking
- Employee authentication system
- Real-time dashboard updates

## Docker Deployment

### Prerequisites

- Docker and Docker Compose installed on your system
- Webcam (for face recognition component)

### Quick Start

1. Clone this repository:
   ```
   git clone <repository-url>
   cd customer_recognition
   ```

2. Build and start the containers:
   ```
   docker-compose up -d
   ```

3. Access the web interface:
   ```
   http://localhost:5001
   ```

4. Default login credentials:
   - Username: admin1001
   - Password: Admin@1001

### Environment Variables

You can customize the deployment by setting these environment variables:

- `SECRET_KEY`: Flask secret key
- `JWT_SECRET_KEY`: Key for JWT token generation
- `MONGO_URI`: MongoDB connection string (defaults to the local mongo container)

Example:
```
SECRET_KEY=your_custom_secret docker-compose up -d
```

### Running Face Recognition

The face recognition component needs access to your camera. To run it:

1. Install dependencies on your host machine:
   ```
   pip install -r requirements.txt
   ```

2. Run the face recognition script:
   ```
   python simple_face_recognition.py
   ```

## Manual Setup (without Docker)

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the setup script:
   ```
   python run_system.py
   ```

3. Access the web interface:
   ```
   http://localhost:5001
   ```

## Project Structure

- `app.py`: Main Flask application
- `simple_face_recognition.py`: Face recognition component
- `train_model.py`: Machine learning model for purchase prediction
- `auth/`: Authentication module
- `templates/`: HTML templates
- `static/`: CSS, JavaScript, and images
- `data/`: Customer data
- `models/`: Trained ML models

## Notes for Deployment

- The face recognition component requires a webcam connection
- For production deployment, consider using a proper WSGI server like Gunicorn
- Ensure proper security measures are in place before exposing to the internet
- The MongoDB instance contains important customer data - set up proper backups 