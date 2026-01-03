"""Integration tests for complete authentication flows"""

from datetime import datetime, timedelta, timezone

from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.services.auth_service import AuthService
from app.services.password_service import PasswordService
from app.services.token_service import TokenService


class TestRegistrationFlow:
    """Integration tests for user registration flow"""

    def test_complete_registration_flow(self, app):
        """Test complete registration flow - user creation, password hashing, password history"""
        with app.app_context():
            from app import db
            from app.models.password_history import PasswordHistory

            # Register user
            user, is_first_user = AuthService.register_user(
                username="newuser",
                email="newuser@example.com",
                password="TestPass123",
            )

            # Get user fresh from database to avoid detached instance issues
            db_user = db.session.query(User).filter_by(username="newuser").first()

            # Verify user was created
            assert db_user is not None
            assert db_user.username == "newuser"
            assert db_user.email == "newuser@example.com"
            assert db_user.password_hash is not None

            # Verify password is hashed correctly
            assert PasswordService.check_password("TestPass123", db_user.password_hash)

            # Verify password history was saved
            history = (
                db.session.query(PasswordHistory).filter_by(user_id=db_user.id).first()
            )
            assert history is not None
            assert PasswordService.check_password("TestPass123", history.password_hash)

    def test_first_user_registration_becomes_admin(self, app):
        """Test that first user registration flow creates admin"""
        with app.app_context():
            from app import db

            # Clear all users
            db.session.query(User).delete()
            db.session.commit()

            # Register first user
            user, is_first_user = AuthService.register_user(
                username="firstuser",
                email="first@example.com",
                password="TestPass123",
            )

            # Verify first user is admin
            assert user.role == "admin"
            assert user.is_first_user is True
            assert is_first_user is True


class TestLoginFlow:
    """Integration tests for user login flow"""

    def test_complete_login_flow(self, app):
        """Test complete login flow - authentication, token generation, refresh token storage"""
        with app.app_context():
            from app import db

            # Register user first
            user, _ = AuthService.register_user(
                username="logintest",
                email="login@example.com",
                password="TestPass123",
            )

            # Login user
            result = AuthService.login_user("logintest", "TestPass123")

            assert result is not None
            logged_in_user, access_token, refresh_token = result

            # Verify user matches
            assert logged_in_user.id == user.id
            assert logged_in_user.username == "logintest"

            # Verify tokens are generated
            assert access_token is not None
            assert refresh_token is not None

            # Verify access token is valid
            payload = TokenService.verify_token(access_token)
            assert payload is not None
            assert payload["user_id"] == str(user.id)
            assert payload["username"] == "logintest"

            # Verify refresh token is stored in database
            refresh_token_obj = (
                db.session.query(RefreshToken)
                .filter_by(token_hash=refresh_token)
                .first()
            )
            assert refresh_token_obj is not None
            assert refresh_token_obj.user_id == user.id

            # Verify last_login was updated
            db.session.refresh(user)
            assert user.last_login is not None

    def test_login_failure_invalid_credentials(self, app):
        """Test login flow with invalid credentials"""
        with app.app_context():
            # Register user
            AuthService.register_user(
                username="logintest2",
                email="login2@example.com",
                password="TestPass123",
            )

            # Try login with wrong password
            result = AuthService.login_user("logintest2", "WrongPassword123")
            assert result is None

            # Try login with wrong username
            result = AuthService.login_user("nonexistent", "TestPass123")
            assert result is None


class TestTokenRefreshFlow:
    """Integration tests for token refresh flow"""

    def test_complete_token_refresh_flow(self, app):
        """Test complete token refresh flow"""
        with app.app_context():
            from app import db

            # Register and login user
            user, _ = AuthService.register_user(
                username="refreshtest",
                email="refresh@example.com",
                password="TestPass123",
            )

            login_result = AuthService.login_user("refreshtest", "TestPass123")
            assert login_result is not None
            _, initial_access_token, refresh_token = login_result

            # Verify initial access token works
            payload = TokenService.verify_token(initial_access_token)
            assert payload is not None

            # Refresh the token
            refresh_result = AuthService.refresh_access_token(refresh_token)
            assert refresh_result is not None
            new_access_token, new_refresh_token = refresh_result

            # Verify new access token is valid
            new_payload = TokenService.verify_token(new_access_token)
            assert new_payload is not None
            assert new_payload["user_id"] == str(user.id)

            # Verify refresh token last_used_at was updated
            refresh_token_obj = (
                db.session.query(RefreshToken)
                .filter_by(token_hash=refresh_token)
                .first()
            )
            assert refresh_token_obj is not None
            assert refresh_token_obj.last_used_at is not None

    def test_token_refresh_with_expired_refresh_token(self, app):
        """Test token refresh flow with expired refresh token"""
        with app.app_context():
            from app import db

            # Register and login user
            user, _ = AuthService.register_user(
                username="refreshtest2",
                email="refresh2@example.com",
                password="TestPass123",
            )

            login_result = AuthService.login_user("refreshtest2", "TestPass123")
            assert login_result is not None
            _, _, refresh_token = login_result

            # Expire the refresh token
            refresh_token_obj = (
                db.session.query(RefreshToken)
                .filter_by(token_hash=refresh_token)
                .first()
            )
            expired_at = datetime.now(timezone.utc) - timedelta(hours=1)
            # Convert to naive UTC for storage
            refresh_token_obj.expires_at = (
                expired_at.replace(tzinfo=None) if expired_at.tzinfo else expired_at
            )
            db.session.commit()

            # Try to refresh - should fail
            refresh_result = AuthService.refresh_access_token(refresh_token)
            assert refresh_result is None

            # Verify refresh token was deleted
            refresh_token_obj = (
                db.session.query(RefreshToken)
                .filter_by(token_hash=refresh_token)
                .first()
            )
            assert refresh_token_obj is None


class TestLogoutFlow:
    """Integration tests for user logout flow"""

    def test_complete_logout_flow(self, app):
        """Test complete logout flow - token blacklisting"""
        with app.app_context():
            from app import db
            from app.models.token_blacklist import TokenBlacklist

            # Register and login user
            user, _ = AuthService.register_user(
                username="logouttest",
                email="logout@example.com",
                password="TestPass123",
            )

            login_result = AuthService.login_user("logouttest", "TestPass123")
            assert login_result is not None
            _, access_token, _ = login_result

            # Verify token is valid before logout
            payload = TokenService.verify_token(access_token)
            assert payload is not None
            token_id = payload["jti"]

            # Logout
            AuthService.logout_user(access_token, str(user.id))

            # Verify token is blacklisted
            blacklist_entry = (
                db.session.query(TokenBlacklist).filter_by(token_id=token_id).first()
            )
            assert blacklist_entry is not None

            # Verify token verification fails after logout
            verify_result = TokenService.verify_token(access_token)
            assert verify_result is None


class TestUserProfileManagementFlow:
    """Integration tests for user profile management flow"""

    def test_complete_profile_update_flow(self, app):
        """Test complete profile update flow"""
        with app.app_context():
            from app import db

            # Register user
            user, _ = AuthService.register_user(
                username="profiletest",
                email="profile@example.com",
                password="TestPass123",
            )

            # Update user profile
            user.email = "newemail@example.com"
            user.updated_at = datetime.now(timezone.utc)
            db.session.commit()

            # Verify update
            db.session.refresh(user)
            assert user.email == "newemail@example.com"

    def test_password_update_flow(self, app):
        """Test password update flow with password history"""
        with app.app_context():
            from app import db
            from app.models.password_history import PasswordHistory

            # Register user
            user, _ = AuthService.register_user(
                username="passwordtest",
                email="password@example.com",
                password="OldPassword123",
            )

            # Get user fresh from database to avoid detached instance issues
            db_user = db.session.query(User).filter_by(username="passwordtest").first()
            assert db_user is not None

            # Update password
            new_password = "NewPassword123"
            new_password_hash = PasswordService.hash_password(new_password)
            db_user.password_hash = new_password_hash
            db_user.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
            db.session.commit()

            # Save to password history
            PasswordService.save_password_history(str(db_user.id), new_password_hash)

            # Verify password was changed
            db.session.refresh(db_user)
            assert PasswordService.check_password(new_password, db_user.password_hash)
            assert not PasswordService.check_password(
                "OldPassword123", db_user.password_hash
            )

            # Verify old password is in history
            history = (
                db.session.query(PasswordHistory)
                .filter_by(user_id=db_user.id)
                .order_by(PasswordHistory.created_at.desc())
                .first()
            )
            assert history is not None
            assert PasswordService.check_password(new_password, history.password_hash)

            # Verify password history check prevents reuse
            is_in_history = PasswordService.check_password_history(
                str(db_user.id), new_password, max_history=3
            )
            assert is_in_history is True


class TestRoleManagementFlow:
    """Integration tests for role management flow"""

    def test_admin_role_update_flow(self, app):
        """Test role update flow by admin"""
        with app.app_context():
            from app import db

            # Register admin (first user)
            db.session.query(User).delete()
            db.session.commit()

            admin_user, _ = AuthService.register_user(
                username="admin",
                email="admin@example.com",
                password="AdminPass123",
            )

            # Register regular user
            regular_user, _ = AuthService.register_user(
                username="regular",
                email="regular@example.com",
                password="RegularPass123",
            )

            # Verify initial roles
            assert admin_user.role == "admin"
            assert regular_user.role == "player"

            # Admin updates regular user's role
            regular_user.role = "writer"
            regular_user.updated_at = datetime.now(timezone.utc)
            db.session.commit()

            # Verify role was updated
            db.session.refresh(regular_user)
            assert regular_user.role == "writer"

            # Verify role methods work correctly
            assert regular_user.is_writer() is True
            assert regular_user.is_admin() is False
            assert regular_user.has_role("writer") is True
            assert regular_user.has_role("admin") is False
