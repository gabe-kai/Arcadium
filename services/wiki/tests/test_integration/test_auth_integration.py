"""Integration tests for Auth Service integration"""

from unittest.mock import MagicMock, patch

from app.middleware.auth import get_user_from_token
from app.services.auth_service_client import AuthServiceClient


def test_get_user_from_token_integration():
    """Test token validation integration"""
    # Mock Auth Service response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "valid": True,
        "user": {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "username": "testuser",
            "role": "writer",
            "email": "test@example.com",
        },
    }

    with patch(
        "app.services.auth_service_client.requests.post", return_value=mock_response
    ):
        result = get_user_from_token("test-token")

        assert result is not None
        assert result["user_id"] == "123e4567-e89b-12d3-a456-426614174000"
        assert result["username"] == "testuser"
        assert result["role"] == "writer"


def test_get_user_from_token_invalid():
    """Test token validation with invalid token"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"valid": False}

    with patch(
        "app.services.auth_service_client.requests.post", return_value=mock_response
    ):
        result = get_user_from_token("invalid-token")
        assert result is None


def test_auth_service_client_user_profile():
    """Test user profile retrieval"""
    client = AuthServiceClient(base_url="http://localhost:8000")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "username": "testuser",
        "email": "test@example.com",
        "role": "admin",
    }

    with patch(
        "app.services.auth_service_client.requests.get", return_value=mock_response
    ):
        profile = client.get_user_profile("123e4567-e89b-12d3-a456-426614174000")

        assert profile is not None
        assert profile["username"] == "testuser"
        assert profile["role"] == "admin"
