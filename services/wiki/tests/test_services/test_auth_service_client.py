"""Tests for Auth Service client"""
from unittest.mock import patch, MagicMock
import pytest
import requests
from app.services.auth_service_client import AuthServiceClient, get_auth_client


def test_verify_token_success():
    """Test successful token verification"""
    client = AuthServiceClient(base_url='http://localhost:8000')
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'valid': True,
        'user': {
            'id': '123e4567-e89b-12d3-a456-426614174000',
            'username': 'testuser',
            'role': 'writer',
            'email': 'test@example.com'
        }
    }
    
    with patch('app.services.auth_service_client.requests.post', return_value=mock_response):
        result = client.verify_token('test-token')
        
        assert result is not None
        assert result['user_id'] == '123e4567-e89b-12d3-a456-426614174000'
        assert result['username'] == 'testuser'
        assert result['role'] == 'writer'
        assert result['email'] == 'test@example.com'


def test_verify_token_invalid():
    """Test token verification with invalid token"""
    client = AuthServiceClient(base_url='http://localhost:8000')
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'valid': False
    }
    
    with patch('app.services.auth_service_client.requests.post', return_value=mock_response):
        result = client.verify_token('invalid-token')
        assert result is None


def test_verify_token_401():
    """Test token verification with 401 response"""
    client = AuthServiceClient(base_url='http://localhost:8000')
    
    mock_response = MagicMock()
    mock_response.status_code = 401
    
    with patch('app.services.auth_service_client.requests.post', return_value=mock_response):
        result = client.verify_token('expired-token')
        assert result is None


def test_verify_token_timeout():
    """Test token verification with timeout"""
    client = AuthServiceClient(base_url='http://localhost:8000')
    
    with patch('app.services.auth_service_client.requests.post', side_effect=requests.exceptions.Timeout()):
        result = client.verify_token('test-token')
        assert result is None


def test_verify_token_connection_error():
    """Test token verification with connection error"""
    client = AuthServiceClient(base_url='http://localhost:8000')
    
    with patch('app.services.auth_service_client.requests.post', side_effect=requests.exceptions.ConnectionError()):
        result = client.verify_token('test-token')
        assert result is None


def test_get_user_profile_success():
    """Test successful user profile retrieval"""
    client = AuthServiceClient(base_url='http://localhost:8000')
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'id': '123e4567-e89b-12d3-a456-426614174000',
        'username': 'testuser',
        'email': 'test@example.com',
        'role': 'writer',
        'created_at': '2024-01-01T00:00:00Z'
    }
    
    with patch('app.services.auth_service_client.requests.get', return_value=mock_response):
        result = client.get_user_profile('123e4567-e89b-12d3-a456-426614174000')
        
        assert result is not None
        assert result['id'] == '123e4567-e89b-12d3-a456-426614174000'
        assert result['username'] == 'testuser'


def test_get_user_profile_not_found():
    """Test user profile retrieval when user not found"""
    client = AuthServiceClient(base_url='http://localhost:8000')
    
    mock_response = MagicMock()
    mock_response.status_code = 404
    
    with patch('app.services.auth_service_client.requests.get', return_value=mock_response):
        result = client.get_user_profile('nonexistent-id')
        assert result is None


def test_get_user_by_username_success():
    """Test successful user lookup by username"""
    client = AuthServiceClient(base_url='http://localhost:8000')
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'id': '123e4567-e89b-12d3-a456-426614174000',
        'username': 'testuser',
        'email': 'test@example.com',
        'role': 'admin'
    }
    
    with patch('app.services.auth_service_client.requests.get', return_value=mock_response):
        result = client.get_user_by_username('testuser')
        
        assert result is not None
        assert result['username'] == 'testuser'
        assert result['role'] == 'admin'


def test_get_user_by_username_not_found():
    """Test user lookup by username when user not found"""
    client = AuthServiceClient(base_url='http://localhost:8000')
    
    mock_response = MagicMock()
    mock_response.status_code = 404
    
    with patch('app.services.auth_service_client.requests.get', return_value=mock_response):
        result = client.get_user_by_username('nonexistent')
        assert result is None


def test_get_auth_client_singleton():
    """Test that get_auth_client returns singleton"""
    client1 = get_auth_client()
    client2 = get_auth_client()
    
    assert client1 is client2
    assert isinstance(client1, AuthServiceClient)
