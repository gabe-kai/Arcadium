"""Tests for service token utilities"""

import time

import jwt

from shared.auth.tokens.service_tokens import (
    get_service_id,
    get_service_name,
    is_service_token,
    validate_service_token,
)


class TestValidateServiceToken:
    """Tests for validate_service_token function"""

    def test_validate_valid_service_token(self):
        """Test validation of a valid service token"""
        secret = "test-secret-key"
        payload = {
            "service_name": "wiki",
            "service_id": "wiki-123",
            "type": "service",
            "exp": int(time.time()) + 3600,
        }
        token = jwt.encode(payload, secret, algorithm="HS256")

        result = validate_service_token(token, secret)
        assert result is not None
        assert result["service_name"] == "wiki"
        assert result["service_id"] == "wiki-123"
        assert result["type"] == "service"

    def test_validate_user_token_as_service_token(self):
        """Test that user token is rejected as service token"""
        secret = "test-secret-key"
        payload = {
            "user_id": "123e4567-e89b-12d3-a456-426614174000",
            "role": "admin",
            "type": "user",  # Not a service token
            "exp": int(time.time()) + 3600,
        }
        token = jwt.encode(payload, secret, algorithm="HS256")

        result = validate_service_token(token, secret)
        assert result is None

    def test_validate_token_without_type(self):
        """Test that token without type is rejected"""
        secret = "test-secret-key"
        payload = {
            "service_name": "wiki",
            "service_id": "wiki-123",
            # No type field
            "exp": int(time.time()) + 3600,
        }
        token = jwt.encode(payload, secret, algorithm="HS256")

        result = validate_service_token(token, secret)
        assert result is None

    def test_validate_expired_service_token(self):
        """Test validation of expired service token"""
        secret = "test-secret-key"
        payload = {
            "service_name": "wiki",
            "service_id": "wiki-123",
            "type": "service",
            "exp": int(time.time()) - 3600,  # Expired
        }
        token = jwt.encode(payload, secret, algorithm="HS256")

        result = validate_service_token(token, secret)
        assert result is None

    def test_validate_invalid_service_token(self):
        """Test validation of invalid token"""
        secret = "test-secret-key"
        invalid_token = "invalid.token.here"

        result = validate_service_token(invalid_token, secret)
        assert result is None


class TestGetServiceName:
    """Tests for get_service_name function"""

    def test_get_valid_service_name(self):
        """Test extracting valid service name"""
        payload = {"service_name": "wiki", "type": "service"}
        result = get_service_name(payload)
        assert result == "wiki"

    def test_get_missing_service_name(self):
        """Test extracting service name when not present"""
        payload = {"service_id": "wiki-123", "type": "service"}
        result = get_service_name(payload)
        assert result is None


class TestGetServiceID:
    """Tests for get_service_id function"""

    def test_get_valid_service_id(self):
        """Test extracting valid service ID"""
        payload = {"service_id": "wiki-123", "type": "service"}
        result = get_service_id(payload)
        assert result == "wiki-123"

    def test_get_missing_service_id(self):
        """Test extracting service ID when not present"""
        payload = {"service_name": "wiki", "type": "service"}
        result = get_service_id(payload)
        assert result is None


class TestIsServiceToken:
    """Tests for is_service_token function"""

    def test_is_service_token_true(self):
        """Test that service token is identified correctly"""
        payload = {
            "service_name": "wiki",
            "service_id": "wiki-123",
            "type": "service",
        }
        assert is_service_token(payload) is True

    def test_is_service_token_false_user_token(self):
        """Test that user token is not identified as service token"""
        payload = {
            "user_id": "123e4567-e89b-12d3-a456-426614174000",
            "role": "admin",
            "type": "user",
        }
        assert is_service_token(payload) is False

    def test_is_service_token_false_no_type(self):
        """Test that token without type is not service token"""
        payload = {"service_name": "wiki", "service_id": "wiki-123"}
        assert is_service_token(payload) is False

    def test_is_service_token_false_wrong_type(self):
        """Test that token with wrong type is not service token"""
        payload = {
            "service_name": "wiki",
            "service_id": "wiki-123",
            "type": "invalid",
        }
        assert is_service_token(payload) is False
