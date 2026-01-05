"""Tests for token management endpoints (refresh, logout, revoke)"""

import pytest
from app import db
from app.models.refresh_token import RefreshToken
from app.services.auth_service import AuthService
from app.services.token_service import TokenService


@pytest.fixture
def test_user_id(app):
    """Create a test user and return user info dict"""
    import uuid

    unique_id = str(uuid.uuid4())[:8]
    username = f"testuser_{unique_id}"
    email = f"test_{unique_id}@example.com"
    with app.app_context():
        user, _ = AuthService.register_user(
            username=username, email=email, password="TestPass123"
        )
        db.session.commit()
        return {"user_id": str(user.id), "username": username, "email": email}


@pytest.fixture
def test_user_with_tokens(app, test_user_id):
    """Create a test user and generate tokens"""
    with app.app_context():
        # Login to get tokens
        username = test_user_id["username"]
        result = AuthService.login_user(username, "TestPass123")
        if result:
            user, access_token, refresh_token = result
            db.session.commit()
            return {
                "user_id": str(user.id),
                "access_token": access_token,
                "refresh_token": refresh_token,
            }
        return None


class TestRefreshEndpoint:
    """Tests for POST /api/auth/refresh"""

    def test_refresh_token_success(self, client, app, test_user_with_tokens):
        """Test successful token refresh"""
        with app.app_context():
            tokens = test_user_with_tokens
            if not tokens:
                pytest.skip("Failed to create test user with tokens")

            response = client.post(
                "/api/auth/refresh",
                json={"token": tokens["refresh_token"]},
                content_type="application/json",
            )

            assert response.status_code == 200
            data = response.get_json()
            assert "token" in data
            assert "expires_in" in data
            assert data["expires_in"] == 3600  # Default expiration

            # Verify new token is valid
            new_token = data["token"]
            payload = TokenService.verify_token(new_token)
            assert payload is not None
            assert payload["user_id"] == tokens["user_id"]

    def test_refresh_token_invalid_token(self, client, app):
        """Test refresh with invalid token"""
        response = client.post(
            "/api/auth/refresh",
            json={"token": "invalid-refresh-token"},
            content_type="application/json",
        )

        assert response.status_code == 401
        data = response.get_json()
        assert "error" in data

    def test_refresh_token_missing_token(self, client, app):
        """Test refresh without token"""
        response = client.post(
            "/api/auth/refresh", json={}, content_type="application/json"
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_refresh_token_missing_body(self, client, app):
        """Test refresh without request body"""
        response = client.post("/api/auth/refresh")

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_refresh_token_expired_token(self, client, app, test_user_with_tokens):
        """Test refresh with expired refresh token"""
        with app.app_context():
            tokens = test_user_with_tokens
            if not tokens:
                pytest.skip("Failed to create test user with tokens")

            # Delete the refresh token to simulate expiration
            refresh_token = (
                db.session.query(RefreshToken)
                .filter_by(token_hash=tokens["refresh_token"])
                .first()
            )
            if refresh_token:
                db.session.delete(refresh_token)
                db.session.commit()

            response = client.post(
                "/api/auth/refresh",
                json={"token": tokens["refresh_token"]},
                content_type="application/json",
            )

            assert response.status_code == 401
            data = response.get_json()
            assert "error" in data


class TestLogoutEndpoint:
    """Tests for POST /api/auth/logout"""

    def test_logout_success(self, client, app, test_user_with_tokens):
        """Test successful logout"""
        with app.app_context():
            tokens = test_user_with_tokens
            if not tokens:
                pytest.skip("Failed to create test user with tokens")

            access_token = tokens["access_token"]

            response = client.post(
                "/api/auth/logout",
                headers={"Authorization": f"Bearer {access_token}"},
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data["message"] == "Logged out successfully"

            # Verify token is blacklisted by trying to verify it
            verify_response = client.post(
                "/api/auth/verify",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            assert verify_response.status_code == 401

    def test_logout_missing_authorization_header(self, client, app):
        """Test logout without Authorization header"""
        response = client.post("/api/auth/logout")

        assert response.status_code == 401
        data = response.get_json()
        assert "error" in data

    def test_logout_invalid_token(self, client, app):
        """Test logout with invalid token"""
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code == 401
        data = response.get_json()
        assert "error" in data

    def test_logout_invalid_header_format(self, client, app):
        """Test logout with invalid Authorization header format"""
        response = client.post(
            "/api/auth/logout", headers={"Authorization": "InvalidFormat token"}
        )

        assert response.status_code == 401
        data = response.get_json()
        assert "error" in data


class TestRevokeEndpoint:
    """Tests for POST /api/auth/revoke"""

    def test_revoke_specific_refresh_token(self, client, app, test_user_with_tokens):
        """Test revoking a specific refresh token"""
        with app.app_context():
            tokens = test_user_with_tokens
            if not tokens:
                pytest.skip("Failed to create test user with tokens")

            access_token = tokens["access_token"]
            refresh_token = tokens["refresh_token"]

            response = client.post(
                "/api/auth/revoke",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"token_id": refresh_token},
                content_type="application/json",
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data["message"] == "Token revoked successfully"
            assert data["revoked_count"] == 1

            # Verify refresh token is deleted
            refresh_token_obj = (
                db.session.query(RefreshToken)
                .filter_by(token_hash=refresh_token)
                .first()
            )
            assert refresh_token_obj is None

    def test_revoke_specific_access_token_jti(self, client, app, test_user_with_tokens):
        """Test revoking a specific access token by jti"""
        with app.app_context():
            tokens = test_user_with_tokens
            if not tokens:
                pytest.skip("Failed to create test user with tokens")

            access_token = tokens["access_token"]

            # Get token jti before revoking
            payload = TokenService.verify_token(access_token)
            assert payload is not None  # Token should be valid
            token_jti = payload.get("jti")
            assert token_jti is not None

            response = client.post(
                "/api/auth/revoke",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"token_id": token_jti},
                content_type="application/json",
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data["message"] == "Token revoked successfully"
            assert data["revoked_count"] == 1

            # Verify token is blacklisted
            verify_response = client.post(
                "/api/auth/verify",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            assert verify_response.status_code == 401

    def test_revoke_all_tokens_as_admin(self, client, app):
        """Test revoking all tokens as admin"""
        with app.app_context():
            # Create admin user (first user)
            admin_user, _ = AuthService.register_user(
                username="admin", email="admin@example.com", password="AdminPass123"
            )
            db.session.commit()

            # Login to get tokens
            result = AuthService.login_user("admin", "AdminPass123")
            if not result:
                pytest.skip("Failed to login admin user")

            admin_user, access_token, refresh_token = result

            # Create another refresh token for the user
            from datetime import datetime, timedelta, timezone

            from app.services.token_service import TokenService

            refresh_token2 = TokenService.generate_refresh_token(admin_user)
            expires_at = datetime.now(timezone.utc) + timedelta(days=7)
            refresh_token_obj = RefreshToken(
                user_id=admin_user.id,
                token_hash=refresh_token2,
                expires_at=expires_at,
                created_at=datetime.now(timezone.utc),
                last_used_at=datetime.now(timezone.utc),
            )
            db.session.add(refresh_token_obj)
            db.session.commit()

            # Count refresh tokens
            token_count = (
                db.session.query(RefreshToken).filter_by(user_id=admin_user.id).count()
            )

            response = client.post(
                "/api/auth/revoke",
                headers={"Authorization": f"Bearer {access_token}"},
                json={},
                content_type="application/json",
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data["message"] == "Token revoked successfully"
            assert data["revoked_count"] == token_count

            # Verify all refresh tokens are deleted
            remaining_tokens = (
                db.session.query(RefreshToken).filter_by(user_id=admin_user.id).count()
            )
            assert remaining_tokens == 0

    def test_revoke_all_tokens_as_non_admin(self, client, app):
        """Test revoking all tokens as non-admin (should fail)"""
        with app.app_context():
            # Create first user (becomes admin)
            admin_user, _ = AuthService.register_user(
                username="adminuser",
                email="admin@example.com",
                password="AdminPass123",
            )
            db.session.commit()

            # Create a second user (non-admin, since first user is admin)
            player_user, _ = AuthService.register_user(
                username="playeruser",
                email="player@example.com",
                password="PlayerPass123",
            )
            db.session.commit()

            # Login to get tokens for player user
            result = AuthService.login_user("playeruser", "PlayerPass123")
            if not result:
                pytest.skip("Failed to login player user")

            player_user, access_token, refresh_token = result

            response = client.post(
                "/api/auth/revoke",
                headers={"Authorization": f"Bearer {access_token}"},
                json={},
                content_type="application/json",
            )

            assert response.status_code == 403
            data = response.get_json()
            assert "error" in data
            assert "admin" in data["error"].lower()

    def test_revoke_missing_authorization_header(self, client, app):
        """Test revoke without Authorization header"""
        response = client.post("/api/auth/revoke", json={"token_id": "some-token-id"})

        assert response.status_code == 401
        data = response.get_json()
        assert "error" in data

    def test_revoke_invalid_token(self, client, app):
        """Test revoke with invalid token"""
        response = client.post(
            "/api/auth/revoke",
            headers={"Authorization": "Bearer invalid-token"},
            json={"token_id": "some-token-id"},
        )

        assert response.status_code == 401
        data = response.get_json()
        assert "error" in data

    def test_revoke_nonexistent_token(self, client, app, test_user_with_tokens):
        """Test revoking a token that doesn't exist"""
        with app.app_context():
            tokens = test_user_with_tokens
            if not tokens:
                pytest.skip("Failed to create test user with tokens")

            access_token = tokens["access_token"]

            response = client.post(
                "/api/auth/revoke",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"token_id": "nonexistent-token-id"},
                content_type="application/json",
            )

            # Should still succeed (token is blacklisted even if it doesn't exist as refresh token)
            assert response.status_code == 200
            data = response.get_json()
            assert data["message"] == "Token revoked successfully"
