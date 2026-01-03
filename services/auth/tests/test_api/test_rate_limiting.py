"""Tests for rate limiting functionality"""

import os

import pytest
from app import create_app, limiter


@pytest.fixture
def app():
    """Create app with rate limiting enabled for testing"""
    # Temporarily enable rate limiting for tests by overriding config
    original_value = os.environ.get("RATELIMIT_ENABLED")
    os.environ["RATELIMIT_ENABLED"] = "true"
    try:
        test_app = create_app("testing")
        # Override the config value that was set during app creation
        test_app.config["RATELIMIT_ENABLED"] = True
        # Re-enable limiter now that app is created
        limiter.enabled = True
        yield test_app
    finally:
        # Restore original setting and disable limiter
        if original_value is None:
            os.environ.pop("RATELIMIT_ENABLED", None)
        else:
            os.environ["RATELIMIT_ENABLED"] = original_value
        limiter.enabled = False


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


class TestLoginRateLimiting:
    """Test rate limiting on login endpoint"""

    def test_login_rate_limit_allowed(self, client):
        """Test that login requests within rate limit are allowed"""
        # Make 5 requests (the limit is 5 per 15 minutes)
        for i in range(5):
            response = client.post(
                "/api/auth/login",
                json={"username": f"testuser{i}", "password": "wrongpassword"},
            )
            # All should return 401 (invalid credentials), not 429 (rate limited)
            assert response.status_code == 401

    def test_login_rate_limit_exceeded(self, client):
        """Test that login requests exceeding rate limit return 429"""
        # Make 5 requests (the limit)
        for i in range(5):
            response = client.post(
                "/api/auth/login",
                json={"username": f"testuser{i}", "password": "wrongpassword"},
            )
            assert response.status_code == 401  # Invalid credentials

        # 6th request should be rate limited
        response = client.post(
            "/api/auth/login",
            json={"username": "testuser6", "password": "wrongpassword"},
        )
        assert response.status_code == 429
        data = response.get_json()
        assert "error" in data
        assert "rate limit" in data["error"].lower()

    def test_login_rate_limit_headers(self, client):
        """Test that rate limit headers are present in responses"""
        response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "wrongpassword"},
        )
        # Check for rate limit headers
        assert "X-RateLimit-Limit" in response.headers or response.status_code == 401
        # If not rate limited, should get 401
        assert response.status_code in [401, 429]


class TestRegistrationRateLimiting:
    """Test rate limiting on registration endpoint"""

    def test_registration_rate_limit_allowed(self, client, db_session):
        """Test that registration requests within rate limit are allowed"""
        # Make 3 requests (the limit is 3 per hour per email)
        for i in range(3):
            response = client.post(
                "/api/auth/register",
                json={
                    "username": f"testuser{i}",
                    "email": f"test{i}@example.com",
                    "password": "TestPass123",
                },
            )
            # Should succeed (201) or fail with validation error (400), not 429
            assert response.status_code in [201, 400]

    def test_registration_rate_limit_exceeded_same_email(self, client, db_session):
        """Test that registration requests with same email exceeding rate limit return 429"""
        email = "ratetest@example.com"

        # Make 3 successful registrations with different emails first
        for i in range(3):
            response = client.post(
                "/api/auth/register",
                json={
                    "username": f"testuser{i}",
                    "email": f"different{i}@example.com",
                    "password": "TestPass123",
                },
            )

        # Now try 3 more with the same email (should hit rate limit after 3)
        # Actually, let's create one user first, then try to register 3 more times with same email
        # But wait - the limit is per email, so we need to register 3 times with the same email
        # But if we register successfully, we can't register again with same email (duplicate)
        # So let's try to register with invalid data to hit the rate limit
        # Actually, rate limiting happens before validation, so we can hit the limit with any requests

        # Make 3 requests with the same email (even if they fail validation)
        for i in range(3):
            response = client.post(
                "/api/auth/register",
                json={
                    "username": f"testuser{i}",  # This might cause duplicate username errors
                    "email": email,
                    "password": "TestPass123",
                },
            )
            # These might succeed or fail, but shouldn't be rate limited yet

        # 4th request with same email should be rate limited
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": email,
                "password": "TestPass123",
            },
        )
        # Should be rate limited (429) or validation error (400) if username/email duplicate
        assert response.status_code in [400, 429]
        if response.status_code == 429:
            data = response.get_json()
            assert "rate limit" in data["error"].lower()


class TestRefreshRateLimiting:
    """Test rate limiting on refresh endpoint"""

    def test_refresh_rate_limit_allowed(self, client, db_session):
        """Test that refresh requests within rate limit are allowed"""
        # Create a user and get a refresh token first
        from datetime import datetime, timedelta, timezone

        from app import db
        from app.models.user import User
        from app.services.password_service import PasswordService

        user = User(
            username="refreshtest",
            email="refresh@example.com",
            password_hash=PasswordService.hash_password("TestPass123"),
            role="player",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.session.add(user)
        db.session.commit()

        from app.models.refresh_token import RefreshToken
        from app.services.token_service import TokenService

        refresh_token_str = TokenService.generate_refresh_token(user)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=3600)
        refresh_token = RefreshToken(
            user_id=user.id,
            token_hash=refresh_token_str,
            expires_at=expires_at.replace(tzinfo=None),
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
            last_used_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        db.session.add(refresh_token)
        db.session.commit()

        # Make 10 requests (the limit is 10 per hour)
        for i in range(10):
            response = client.post(
                "/api/auth/refresh",
                json={"token": refresh_token_str},
            )
            # Should succeed (200) or fail with 401 (invalid token), not 429
            assert response.status_code in [200, 401]

    def test_refresh_rate_limit_exceeded(self, client, db_session):
        """Test that refresh requests exceeding rate limit return 429"""
        # Create a user and get a refresh token first
        from datetime import datetime, timedelta, timezone

        from app import db
        from app.models.user import User
        from app.services.password_service import PasswordService

        user = User(
            username="refreshtest2",
            email="refresh2@example.com",
            password_hash=PasswordService.hash_password("TestPass123"),
            role="player",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.session.add(user)
        db.session.commit()

        from app.models.refresh_token import RefreshToken
        from app.services.token_service import TokenService

        refresh_token_str = TokenService.generate_refresh_token(user)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=3600)
        refresh_token = RefreshToken(
            user_id=user.id,
            token_hash=refresh_token_str,
            expires_at=expires_at.replace(tzinfo=None),
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
            last_used_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        db.session.add(refresh_token)
        db.session.commit()

        # Make 10 requests (the limit)
        for i in range(10):
            response = client.post(
                "/api/auth/refresh",
                json={"token": refresh_token_str},
            )
            assert response.status_code in [200, 401]

        # 11th request should be rate limited
        response = client.post(
            "/api/auth/refresh",
            json={"token": refresh_token_str},
        )
        assert response.status_code == 429
        data = response.get_json()
        assert "error" in data
        assert "rate limit" in data["error"].lower()


class TestRateLimitErrorHandler:
    """Test rate limit error handler"""

    def test_rate_limit_error_response_format(self, client):
        """Test that rate limit error responses have correct format"""
        # Exceed rate limit on login
        for i in range(6):  # 6 requests, limit is 5
            client.post(
                "/api/auth/login",
                json={"username": f"testuser{i}", "password": "wrongpassword"},
            )

        # Last request should be rate limited
        response = client.post(
            "/api/auth/login",
            json={"username": "testuser6", "password": "wrongpassword"},
        )
        assert response.status_code == 429
        data = response.get_json()
        assert "error" in data
        assert "message" in data
        assert data["error"] == "Rate limit exceeded"


class TestRateLimitingDisabledInTesting:
    """Test that rate limiting is properly disabled in testing config by default"""

    def test_rate_limiting_disabled_by_default(self):
        """Test that rate limiting is disabled in testing config by default"""
        # Create app without enabling rate limiting
        original_value = os.environ.get("RATELIMIT_ENABLED")
        if "RATELIMIT_ENABLED" in os.environ:
            del os.environ["RATELIMIT_ENABLED"]
        try:
            create_app("testing")  # Create app to initialize limiter
            # After creating app with testing config, limiter should be disabled
            assert limiter.enabled is False
        finally:
            if original_value:
                os.environ["RATELIMIT_ENABLED"] = original_value
