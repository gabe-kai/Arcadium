"""Tests for token validation utilities"""

import time
import uuid

import jwt

from shared.auth.tokens.validation import (
    decode_token,
    get_token_role,
    get_token_user_id,
    is_token_expired,
    validate_jwt_token,
)


class TestValidateJWTToken:
    """Tests for validate_jwt_token function"""

    def test_validate_valid_token(self):
        """Test validation of a valid JWT token"""
        secret = "test-secret-key"
        payload = {
            "user_id": "123e4567-e89b-12d3-a456-426614174000",
            "role": "admin",
            "exp": int(time.time()) + 3600,  # 1 hour from now
        }
        token = jwt.encode(payload, secret, algorithm="HS256")

        result = validate_jwt_token(token, secret)
        assert result is not None
        assert result["user_id"] == payload["user_id"]
        assert result["role"] == payload["role"]

    def test_validate_expired_token(self):
        """Test validation of an expired token"""
        secret = "test-secret-key"
        payload = {
            "user_id": "123e4567-e89b-12d3-a456-426614174000",
            "role": "admin",
            "exp": int(time.time()) - 3600,  # 1 hour ago
        }
        token = jwt.encode(payload, secret, algorithm="HS256")

        result = validate_jwt_token(token, secret)
        assert result is None

    def test_validate_invalid_token(self):
        """Test validation of an invalid token"""
        secret = "test-secret-key"
        invalid_token = "invalid.token.here"

        result = validate_jwt_token(invalid_token, secret)
        assert result is None

    def test_validate_token_wrong_secret(self):
        """Test validation with wrong secret key"""
        secret = "test-secret-key"
        wrong_secret = "wrong-secret-key"
        payload = {
            "user_id": "123e4567-e89b-12d3-a456-426614174000",
            "role": "admin",
            "exp": int(time.time()) + 3600,
        }
        token = jwt.encode(payload, secret, algorithm="HS256")

        result = validate_jwt_token(token, wrong_secret)
        assert result is None

    def test_validate_token_different_algorithm(self):
        """Test validation with different algorithm"""
        secret = "test-secret-key"
        payload = {
            "user_id": "123e4567-e89b-12d3-a456-426614174000",
            "role": "admin",
            "exp": int(time.time()) + 3600,
        }
        token = jwt.encode(payload, secret, algorithm="HS256")

        # Should work with correct algorithm
        result = validate_jwt_token(token, secret, algorithm="HS256")
        assert result is not None

        # Should fail with wrong algorithm
        result = validate_jwt_token(token, secret, algorithm="HS512")
        assert result is None


class TestDecodeToken:
    """Tests for decode_token function"""

    def test_decode_valid_token(self):
        """Test decoding a valid token (without validation)"""
        secret = "test-secret-key"
        payload = {
            "user_id": "123e4567-e89b-12d3-a456-426614174000",
            "role": "admin",
            "exp": int(time.time()) + 3600,
        }
        token = jwt.encode(payload, secret, algorithm="HS256")

        result = decode_token(token, secret)
        assert result is not None
        assert result["user_id"] == payload["user_id"]
        assert result["role"] == payload["role"]

    def test_decode_expired_token(self):
        """Test decoding an expired token (should still decode)"""
        secret = "test-secret-key"
        payload = {
            "user_id": "123e4567-e89b-12d3-a456-426614174000",
            "role": "admin",
            "exp": int(time.time()) - 3600,  # Expired
        }
        token = jwt.encode(payload, secret, algorithm="HS256")

        # decode_token doesn't validate expiration
        result = decode_token(token, secret)
        assert result is not None
        assert result["user_id"] == payload["user_id"]

    def test_decode_invalid_token(self):
        """Test decoding an invalid token"""
        invalid_token = "invalid.token.here"
        result = decode_token(invalid_token, "secret")
        assert result is None


class TestIsTokenExpired:
    """Tests for is_token_expired function"""

    def test_token_not_expired(self):
        """Test checking non-expired token"""
        payload = {"exp": int(time.time()) + 3600}  # 1 hour from now
        assert is_token_expired(payload) is False

    def test_token_expired(self):
        """Test checking expired token"""
        payload = {"exp": int(time.time()) - 3600}  # 1 hour ago
        assert is_token_expired(payload) is True

    def test_token_no_exp_claim(self):
        """Test token without exp claim (should be considered expired)"""
        payload = {"user_id": "123", "role": "admin"}
        assert is_token_expired(payload) is True


class TestGetTokenUserID:
    """Tests for get_token_user_id function"""

    def test_get_valid_user_id(self):
        """Test extracting valid UUID user ID"""
        user_id_str = "123e4567-e89b-12d3-a456-426614174000"
        payload = {"user_id": user_id_str}
        result = get_token_user_id(payload)
        assert result is not None
        assert isinstance(result, uuid.UUID)
        assert str(result) == user_id_str

    def test_get_missing_user_id(self):
        """Test extracting user ID when not present"""
        payload = {"role": "admin"}
        result = get_token_user_id(payload)
        assert result is None

    def test_get_invalid_user_id(self):
        """Test extracting invalid user ID format"""
        payload = {"user_id": "not-a-valid-uuid"}
        result = get_token_user_id(payload)
        assert result is None


class TestGetTokenRole:
    """Tests for get_token_role function"""

    def test_get_valid_role(self):
        """Test extracting valid role"""
        payload = {"role": "admin"}
        result = get_token_role(payload)
        assert result == "admin"

    def test_get_missing_role(self):
        """Test extracting role when not present"""
        payload = {"user_id": "123"}
        result = get_token_role(payload)
        assert result is None
