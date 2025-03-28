# Customer Recognition System

A system that uses face recognition to identify customers, predict their spending, and track purchase history.

## Features

- Face recognition for customer identification
- Purchase prediction using machine learning
- Customer purchase history tracking
- Employee authentication system
- Real-time dashboard updates

## Security Notice

This system has been updated to address several security concerns:

- Proper password hashing with bcrypt
- No hardcoded secrets (all via environment variables)
- Restricted CORS settings
- HTTPS support with proper security headers
- MongoDB authentication
- Localhost-only bindings for development mode

## Docker Deployment

### Prerequisites

- Docker and Docker Compose installed on your system
- Webcam (for face recognition component)
- Environment variables properly configured

### Environment Setup

1. Copy the example environment file:
   ```
   cp .env.example .env
   ```

2. Edit the `.env` file and set all required variables:
   - Generate strong random keys for `SECRET_KEY` and `JWT_SECRET_KEY`
   - Set `MONGO_PASSWORD` for database authentication
   - Configure `CORS_ALLOWED_ORIGINS` for production

### Quick Start

1. Build and start the containers:
   ```
   docker-compose up -d
   ```

2. Access the web interface:
   ```
   https://localhost:5001
   ```

3. Default login credentials:
   - Username: admin1001
   - Password: Admin@1001

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

## Production Deployment

For production deployment:

1. Use the production Docker Compose file:
   ```
   docker-compose -f docker-compose.prod.yml up -d
   ```

2. Ensure you've set proper values in `.env`:
   ```
   SECRET_KEY=<strong-random-key>
   JWT_SECRET_KEY=<different-strong-random-key>
   MONGO_PASSWORD=<strong-password>
   FLASK_ENV=production
   CORS_ALLOWED_ORIGINS=https://your-domain.com
   ```

3. Use a proper reverse proxy (Nginx) with SSL termination for production.

4. Set up regular backups of the MongoDB database.

## Security Recommendations

1. **SSL/TLS**: Always use HTTPS in production with valid certificates
2. **Environment Variables**: Never commit `.env` files to version control
3. **Authentication**: Change default passwords immediately
4. **MongoDB**: Use strong passwords and restrict network access
5. **Firewall**: Configure a firewall to restrict access to your servers
6. **Updates**: Regularly update dependencies to patch security vulnerabilities

## Project Structure

- `app.py`: Main Flask application
- `simple_face_recognition.py`: Face recognition component
- `train_model.py`: Machine learning model for purchase prediction
- `auth/`: Authentication module
- `templates/`: HTML templates
- `static/`: CSS, JavaScript, and images
- `data/`: Customer data
- `models/`: Trained ML models

## Troubleshooting

- **Database Connection Issues**: Check MongoDB authentication settings
- **Face Recognition Not Working**: Verify camera access and permissions
- **HTTPS Certificate Warnings**: Accept self-signed certs in development or use proper certs in production

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

## Notes for Deployment

- The face recognition component requires a webcam connection
- For production deployment, consider using a proper WSGI server like Gunicorn
- Ensure proper security measures are in place before exposing to the internet
- The MongoDB instance contains important customer data - set up proper backups 