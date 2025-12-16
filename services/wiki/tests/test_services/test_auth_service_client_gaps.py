"""Additional edge case tests for Auth Service client to fill coverage gaps"""
from unittest.mock import patch, MagicMock
import pytest
import requests
from app.services.auth_service_client import AuthServiceClient


def test_verify_token_500_error():
    """Test token verification with 500 server error"""
    client = AuthServiceClient(base_url='http://localhost:8000')
    
    mock_response = MagicMock()
    mock_response.status_code = 500
    
    with patch('app.services.auth_service_client.requests.post', return_value=mock_response):
        result = client.verify_token('test-token')
        assert result is None


def test_verify_token_503_service_unavailable():
    """Test token verification with 503 service unavailable"""
    client = AuthServiceClient(base_url='http://localhost:8000')
    
    mock_response = MagicMock()
    mock_response.status_code = 503
    
    with patch('app.services.auth_service_client.requests.post', return_value=mock_response):
        result = client.verify_token('test-token')
        assert result is None


def test_verify_token_json_decode_error():
    """Test token verification with malformed JSON response"""
    client = AuthServiceClient(base_url='http://localhost:8000')
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.side_effect = ValueError("Invalid JSON")
    
    with patch('app.services.auth_service_client.requests.post', return_value=mock_response):
        result = client.verify_token('test-token')
        assert result is None


def test_verify_token_missing_user_key():
    """Test token verification when response is valid but missing user key"""
    client = AuthServiceClient(base_url='http://localhost:8000')
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'valid': True
        # Missing 'user' key
    }
    
    with patch('app.services.auth_service_client.requests.post', return_value=mock_response):
        result = client.verify_token('test-token')
        # Should handle gracefully and return dict with empty values
        assert result is not None
        assert result['user_id'] is None or result['user_id'] == ''
        assert result['username'] == ''
        assert result['role'] == 'viewer'


def test_verify_token_empty_token():
    """Test token verification with empty token"""
    client = AuthServiceClient(base_url='http://localhost:8000')
    
    mock_response = MagicMock()
    mock_response.status_code = 401
    
    with patch('app.services.auth_service_client.requests.post', return_value=mock_response):
        result = client.verify_token('')
        assert result is None


def test_get_user_profile_500_error():
    """Test user profile retrieval with 500 server error"""
    client = AuthServiceClient(base_url='http://localhost:8000')
    
    mock_response = MagicMock()
    mock_response.status_code = 500
    
    with patch('app.services.auth_service_client.requests.get', return_value=mock_response):
        result = client.get_user_profile('user-id')
        assert result is None


def test_get_user_profile_json_decode_error():
    """Test user profile retrieval with malformed JSON"""
    client = AuthServiceClient(base_url='http://localhost:8000')
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.side_effect = ValueError("Invalid JSON")
    
    with patch('app.services.auth_service_client.requests.get', return_value=mock_response):
        result = client.get_user_profile('user-id')
        assert result is None


def test_get_user_by_username_500_error():
    """Test user lookup by username with 500 server error"""
    client = AuthServiceClient(base_url='http://localhost:8000')
    
    mock_response = MagicMock()
    mock_response.status_code = 500
    
    with patch('app.services.auth_service_client.requests.get', return_value=mock_response):
        result = client.get_user_by_username('testuser')
        assert result is None


def test_get_user_by_username_json_decode_error():
    """Test user lookup by username with malformed JSON"""
    client = AuthServiceClient(base_url='http://localhost:8000')
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.side_effect = ValueError("Invalid JSON")
    
    with patch('app.services.auth_service_client.requests.get', return_value=mock_response):
        result = client.get_user_by_username('testuser')
        assert result is None


def test_verify_token_generic_exception():
    """Test token verification with unexpected exception"""
    client = AuthServiceClient(base_url='http://localhost:8000')
    
    with patch('app.services.auth_service_client.requests.post', side_effect=Exception("Unexpected error")):
        result = client.verify_token('test-token')
        assert result is None
