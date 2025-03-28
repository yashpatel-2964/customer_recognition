import pytest
import json
import os
from app import app
from unittest.mock import patch, MagicMock

@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    # Configure app for testing
    app.config.update({
        "TESTING": True,
    })
    
    # Create test client
    with app.test_client() as client:
        yield client

def test_root_redirects(client):
    """Test that the root URL redirects to login when not authenticated"""
    response = client.get('/')
    assert response.status_code == 302  # 302 is redirect
    assert '/auth/login' in response.location

@patch('app.token_required')
def test_dashboard_unauthorized(mock_token_required, client):
    """Test that dashboard requires authentication"""
    # Mock the token_required decorator to raise an exception
    mock_token_required.side_effect = Exception("Unauthorized")
    
    response = client.get('/dashboard')
    assert response.status_code == 302  # Should redirect to login

@patch('app.get_cached_database')
def test_api_test_detection(mock_db, client):
    """Test the test_detection API endpoint"""
    # Mock database connection
    mock_db.return_value = MagicMock()
    
    response = client.post('/api/test_detection', 
                          data=json.dumps({'customer_id': 'C1001'}),
                          content_type='application/json')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert 'Test detection added for C1001' in data['message']

@patch('app.get_model')
def test_model_loading(mock_get_model, client):
    """Test model loading functionality"""
    # Create a mock model
    mock_model = MagicMock()
    mock_model.predict.return_value = 50.0
    mock_get_model.return_value = mock_model
    
    # This test is just ensuring the model loading doesn't crash
    from app import get_model
    model = get_model()
    assert model is not None
    
    # Test prediction
    prediction = model.predict('C1001')
    assert prediction == 50.0 