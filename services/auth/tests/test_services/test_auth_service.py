"""Unit tests for AuthService"""

from datetime import datetime, timedelta, timezone

import pytest
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.services.auth_service import AuthService
from app.services.password_service import PasswordService
from app.services.token_service import TokenService


class TestRegisterUser:
    """Tests for register_user method"""

    def test_register_user_creates_user(self, app):
        """Test that register_user creates a new user"""
        with app.app_context():
            from app import db

            user, is_first_user = AuthService.register_user(
                username="newuser", email="newuser@example.com", password="TestPass123"
            )

            assert user is not None
            assert user.username == "newuser"
            assert user.email == "newuser@example.com"
            assert user.password_hash is not None
            assert PasswordService.check_password("TestPass123", user.password_hash)

            # Verify user is in database
            db_user = db.session.query(User).filter_by(username="newuser").first()
            assert db_user is not None
            assert db_user.id == user.id

    def test_register_first_user_becomes_admin(self, app):
        """Test that first user becomes admin"""
        with app.app_context():
            from app import db

            # Clear all users first
            db.session.query(User).delete()
            db.session.commit()

            user, is_first_user = AuthService.register_user(
                username="firstuser",
                email="first@example.com",
                password="TestPass123",
            )

            assert user.role == "admin"
            assert user.is_first_user is True
            assert is_first_user is True

    def test_register_subsequent_user_gets_player_role(self, app):
        """Test that subsequent users get player role"""
        with app.app_context():
            from app import db

            # Ensure at least one user exists (first user)
            existing_count = db.session.query(User).count()
            if existing_count == 0:
                AuthService.register_user(
                    username="firstuser",
                    email="first@example.com",
                    password="TestPass123",
                )

            user, is_first_user = AuthService.register_user(
                username="seconduser",
                email="second@example.com",
                password="TestPass123",
            )

            assert user.role == "player"
            assert user.is_first_user is False
            assert is_first_user is False

    def test_register_user_saves_password_history(self, app):
        """Test that register_user saves password to history"""
        with app.app_context():
            from app import db
            from app.models.password_history import PasswordHistory

            user, _ = AuthService.register_user(
                username="historyuser",
                email="history@example.com",
                password="TestPass123",
            )

            # Verify password history was saved
            history = (
                db.session.query(PasswordHistory).filter_by(user_id=user.id).first()
            )
            assert history is not None
            assert PasswordService.check_password("TestPass123", history.password_hash)

    def test_register_user_duplicate_username(self, app):
        """Test that register_user raises error for duplicate username"""
        with app.app_context():
            AuthService.register_user(
                username="duplicate", email="dup1@example.com", password="TestPass123"
            )

            with pytest.raises(ValueError, match="Username already exists"):
                AuthService.register_user(
                    username="duplicate",
                    email="dup2@example.com",
                    password="TestPass123",
                )

    def test_register_user_duplicate_email(self, app):
        """Test that register_user raises error for duplicate email"""
        with app.app_context():
            AuthService.register_user(
                username="user1", email="duplicate@example.com", password="TestPass123"
            )

            with pytest.raises(ValueError, match="Email already exists"):
                AuthService.register_user(
                    username="user2",
                    email="duplicate@example.com",
                    password="TestPass123",
                )

    def test_register_user_invalid_username(self, app):
        """Test that register_user validates username"""
        with app.app_context():
            with pytest.raises(ValueError, match="Invalid username"):
                AuthService.register_user(
                    username="ab",  # Too short
                    email="test@example.com",
                    password="TestPass123",
                )

    def test_register_user_invalid_email(self, app):
        """Test that register_user validates email"""
        with app.app_context():
            with pytest.raises(ValueError, match="Invalid email"):
                AuthService.register_user(
                    username="testuser",
                    email="invalid-email",
                    password="TestPass123",
                )

    def test_register_user_invalid_password(self, app):
        """Test that register_user validates password"""
        with app.app_context():
            with pytest.raises(ValueError, match="Invalid password"):
                AuthService.register_user(
                    username="testuser",
                    email="test@example.com",
                    password="weak",  # Too weak
                )


class TestLoginUser:
    """Tests for login_user method"""

    @pytest.fixture
    def test_user(self, app):
        """Create a test user for login tests"""
        with app.app_context():

            user, _ = AuthService.register_user(
                username="logintest",
                email="login@example.com",
                password="TestPass123",
            )
            # Return user ID instead of user object to avoid detached instance issues
            return user.id

    def test_login_user_success(self, app, test_user):
        """Test successful user login"""
        with app.app_context():
            from app import db

            result = AuthService.login_user("logintest", "TestPass123")

            assert result is not None
            user, access_token, refresh_token = result
            assert user.id == test_user
            assert user.username == "logintest"
            assert access_token is not None
            assert refresh_token is not None

            # Verify refresh token is stored
            refresh_token_obj = (
                db.session.query(RefreshToken)
                .filter_by(token_hash=refresh_token)
                .first()
            )
            assert refresh_token_obj is not None
            assert refresh_token_obj.user_id == user.id

    def test_login_user_updates_last_login(self, app, test_user):
        """Test that login updates last_login timestamp"""
        with app.app_context():
            from app import db

            # Get user from database
            user = db.session.query(User).filter_by(id=test_user).first()
            initial_login = user.last_login

            AuthService.login_user("logintest", "TestPass123")

            # Refresh user from database
            db.session.refresh(user)
            assert user.last_login is not None
            if initial_login:
                assert user.last_login > initial_login

    def test_login_user_invalid_username(self, app):
        """Test login with invalid username"""
        with app.app_context():
            result = AuthService.login_user("nonexistent", "TestPass123")
            assert result is None

    def test_login_user_invalid_password(self, app, test_user):
        """Test login with invalid password"""
        with app.app_context():
            result = AuthService.login_user("logintest", "WrongPassword123")
            assert result is None

    def test_login_user_case_insensitive_username(self, app, test_user):
        """Test that login is case-insensitive for username"""
        with app.app_context():
            # Username is sanitized to lowercase in register, so "LOGINTEST" should match "logintest"
            result = AuthService.login_user("LOGINTEST", "TestPass123")
            # Username sanitization converts to lowercase, so this should work
            assert result is not None
            user, _, _ = result
            assert user.username == "logintest"


class TestRefreshAccessToken:
    """Tests for refresh_access_token method"""

    @pytest.fixture
    def test_user_with_refresh_token(self, app):
        """Create a test user with refresh token"""
        with app.app_context():
            from app import db

            user, _ = AuthService.register_user(
                username="refreshtest",
                email="refresh@example.com",
                password="TestPass123",
            )

            refresh_token_str = TokenService.generate_refresh_token(user)
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=3600)
            # Convert to naive UTC for storage (PostgreSQL DateTime doesn't store timezone)
            expires_at_naive = expires_at.replace(tzinfo=None)

            refresh_token = RefreshToken(
                user_id=user.id,
                token_hash=refresh_token_str,
                expires_at=expires_at_naive,
                created_at=datetime.now(timezone.utc).replace(tzinfo=None),
            )
            db.session.add(refresh_token)
            db.session.commit()

            # Return user_id instead of user object to avoid detached instance issues
            return user.id, refresh_token_str

    def test_refresh_access_token_success(self, app, test_user_with_refresh_token):
        """Test successful token refresh"""
        with app.app_context():
            from app import db
            from app.models.refresh_token import RefreshToken

            user_id, refresh_token_str = test_user_with_refresh_token

            # Verify refresh token exists and is not expired before testing
            refresh_token_obj = (
                db.session.query(RefreshToken)
                .filter_by(token_hash=refresh_token_str)
                .first()
            )
            assert refresh_token_obj is not None, "Refresh token should exist"
            assert (
                not refresh_token_obj.is_expired()
            ), f"Refresh token should not be expired. expires_at: {refresh_token_obj.expires_at}, now: {datetime.now(timezone.utc)}"

            result = AuthService.refresh_access_token(refresh_token_str)

            assert (
                result is not None
            ), f"refresh_access_token returned None. Token hash: {refresh_token_str}"
            new_access_token, new_refresh_token = result
            assert new_access_token is not None
            assert new_refresh_token is not None

            # Verify new access token is valid
            payload = TokenService.verify_token(new_access_token)
            assert payload is not None
            assert payload["user_id"] == str(user_id)

    def test_refresh_access_token_updates_last_used(
        self, app, test_user_with_refresh_token
    ):
        """Test that refresh updates last_used_at timestamp"""
        with app.app_context():
            from app import db

            _, refresh_token_str = test_user_with_refresh_token

            refresh_token_obj = (
                db.session.query(RefreshToken)
                .filter_by(token_hash=refresh_token_str)
                .first()
            )
            initial_last_used = refresh_token_obj.last_used_at

            AuthService.refresh_access_token(refresh_token_str)

            # Refresh from database
            db.session.refresh(refresh_token_obj)
            assert refresh_token_obj.last_used_at is not None
            if initial_last_used:
                assert refresh_token_obj.last_used_at > initial_last_used

    def test_refresh_access_token_invalid_token(self, app):
        """Test refresh with invalid refresh token"""
        with app.app_context():
            result = AuthService.refresh_access_token("invalid-refresh-token")
            assert result is None

    def test_refresh_access_token_expired_token(
        self, app, test_user_with_refresh_token
    ):
        """Test refresh with expired refresh token"""
        with app.app_context():
            from app import db

            _, refresh_token_str = test_user_with_refresh_token

            # Expire the refresh token
            refresh_token_obj = (
                db.session.query(RefreshToken)
                .filter_by(token_hash=refresh_token_str)
                .first()
            )
            expired_at = datetime.now(timezone.utc) - timedelta(hours=1)
            # Convert to naive UTC for storage
            refresh_token_obj.expires_at = (
                expired_at.replace(tzinfo=None) if expired_at.tzinfo else expired_at
            )
            db.session.commit()

            result = AuthService.refresh_access_token(refresh_token_str)
            assert result is None


class TestLogoutUser:
    """Tests for logout_user method"""

    @pytest.fixture
    def test_user_with_token(self, app):
        """Create a test user and generate token"""
        with app.app_context():
            user, _ = AuthService.register_user(
                username="logouttest",
                email="logout@example.com",
                password="TestPass123",
            )

            access_token = TokenService.generate_access_token(user)
            return user, access_token

    def test_logout_user_blacklists_token(self, app, test_user_with_token):
        """Test that logout_user blacklists the token"""
        with app.app_context():
            from app import db
            from app.models.token_blacklist import TokenBlacklist

            user, access_token = test_user_with_token

            # Verify token is valid before logout
            payload = TokenService.verify_token(access_token)
            assert payload is not None

            # Logout
            AuthService.logout_user(access_token, str(user.id))

            # Verify token is blacklisted
            token_id = payload["jti"]
            blacklist_entry = (
                db.session.query(TokenBlacklist).filter_by(token_id=token_id).first()
            )
            assert blacklist_entry is not None

    def test_logout_user_invalid_token(self, app):
        """Test logout with invalid token"""
        with app.app_context():
            # Should not raise exception, just return
            AuthService.logout_user("invalid-token", "user-id")


class TestRevokeToken:
    """Tests for revoke_token method"""

    @pytest.fixture
    def test_user_with_tokens(self, app):
        """Create a test user with access and refresh tokens"""
        with app.app_context():
            from app import db

            user, _ = AuthService.register_user(
                username="revoketest",
                email="revoke@example.com",
                password="TestPass123",
            )

            access_token = TokenService.generate_access_token(user)
            refresh_token_str = TokenService.generate_refresh_token(user)
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=3600)

            refresh_token = RefreshToken(
                user_id=user.id,
                token_hash=refresh_token_str,
                expires_at=expires_at,
                created_at=datetime.now(timezone.utc),
            )
            db.session.add(refresh_token)
            db.session.commit()

            # Return user_id instead of user object to avoid detached instance issues
            return user.id, access_token, refresh_token_str

    def test_revoke_refresh_token(self, app, test_user_with_tokens):
        """Test revoking a refresh token"""
        with app.app_context():
            from app import db

            user_id, _, refresh_token_str = test_user_with_tokens

            # Verify refresh token exists before
            refresh_token_obj = (
                db.session.query(RefreshToken)
                .filter_by(token_hash=refresh_token_str)
                .first()
            )
            assert refresh_token_obj is not None

            # Revoke the refresh token
            AuthService.revoke_token(refresh_token_str, str(user_id), revoke_all=False)

            # Verify refresh token is deleted
            refresh_token_obj = (
                db.session.query(RefreshToken)
                .filter_by(token_hash=refresh_token_str)
                .first()
            )
            assert refresh_token_obj is None

    def test_revoke_all_tokens(self, app, test_user_with_tokens):
        """Test revoking all tokens"""
        with app.app_context():
            from app import db

            user_id, _, refresh_token_str = test_user_with_tokens

            # Get user from database to generate token
            user = db.session.query(User).filter_by(id=user_id).first()

            # Create additional refresh tokens
            refresh_token_str2 = TokenService.generate_refresh_token(user)
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=3600)
            # Convert to naive UTC for storage
            expires_at_naive = (
                expires_at.replace(tzinfo=None) if expires_at.tzinfo else expires_at
            )
            refresh_token2 = RefreshToken(
                user_id=user_id,
                token_hash=refresh_token_str2,
                expires_at=expires_at_naive,
                created_at=datetime.now(timezone.utc).replace(tzinfo=None),
            )
            db.session.add(refresh_token2)
            db.session.commit()

            # Verify we have multiple tokens
            token_count_before = (
                db.session.query(RefreshToken).filter_by(user_id=user_id).count()
            )
            assert token_count_before >= 2

            # Revoke all tokens
            AuthService.revoke_token("", str(user_id), revoke_all=True)

            # Verify all refresh tokens are deleted
            refresh_tokens = (
                db.session.query(RefreshToken).filter_by(user_id=user_id).all()
            )
            assert len(refresh_tokens) == 0

    def test_revoke_nonexistent_refresh_token(self, app, test_user_with_tokens):
        """Test revoking a refresh token that doesn't exist"""
        with app.app_context():
            user_id, _, _ = test_user_with_tokens

            # Should not raise exception, just do nothing
            AuthService.revoke_token(
                "nonexistent-token-id", str(user_id), revoke_all=False
            )

            # No tokens should be affected (method doesn't raise errors for nonexistent tokens)
            # This is expected behavior - the method silently handles missing tokens
