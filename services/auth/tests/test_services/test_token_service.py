"""Unit tests for TokenService"""

import time
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from app.models.token_blacklist import TokenBlacklist
from app.models.user import User
from app.services.password_service import PasswordService
from app.services.token_service import TokenService


class TestGenerateAccessToken:
    """Tests for generate_access_token"""

    def test_generate_access_token_returns_string(self, app):
        """Test that generate_access_token returns a string"""
        with app.app_context():
            user = User(
                username="tokentest",
                email="token@example.com",
                password_hash=PasswordService.hash_password("TestPass123"),
                role="player",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            token = TokenService.generate_access_token(user)
            assert isinstance(token, str)
            assert len(token) > 0

    def test_generate_access_token_contains_user_info(self, app):
        """Test that generated token contains user information"""
        with app.app_context():
            user = User(
                username="tokentest2",
                email="token2@example.com",
                password_hash=PasswordService.hash_password("TestPass123"),
                role="admin",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            token = TokenService.generate_access_token(user)
            payload = jwt.decode(
                token, app.config["JWT_SECRET_KEY"], algorithms=["HS256"]
            )
            assert payload["user_id"] == str(user.id)
            assert payload["username"] == user.username
            assert payload["role"] == user.role
            assert "jti" in payload  # JWT ID
            assert "iat" in payload  # Issued at
            assert "exp" in payload  # Expiration

    def test_generate_access_token_has_expiration(self, app):
        """Test that generated token has correct expiration time"""
        with app.app_context():
            # Set custom expiration
            app.config["JWT_ACCESS_TOKEN_EXPIRATION"] = 7200  # 2 hours
            user = User(
                username="tokentest3",
                email="token3@example.com",
                password_hash=PasswordService.hash_password("TestPass123"),
                role="player",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            token = TokenService.generate_access_token(user)
            payload = jwt.decode(
                token, app.config["JWT_SECRET_KEY"], algorithms=["HS256"]
            )
            exp_time = payload["exp"]
            iat_time = payload["iat"]
            assert exp_time - iat_time == 7200  # 2 hours in seconds

    def test_generate_access_token_unique_jti(self, app):
        """Test that each token has a unique JWT ID"""
        with app.app_context():
            user = User(
                username="tokentest4",
                email="token4@example.com",
                password_hash=PasswordService.hash_password("TestPass123"),
                role="player",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            token1 = TokenService.generate_access_token(user)
            token2 = TokenService.generate_access_token(user)
            payload1 = jwt.decode(
                token1, app.config["JWT_SECRET_KEY"], algorithms=["HS256"]
            )
            payload2 = jwt.decode(
                token2, app.config["JWT_SECRET_KEY"], algorithms=["HS256"]
            )
            assert payload1["jti"] != payload2["jti"]


class TestGenerateRefreshToken:
    """Tests for generate_refresh_token"""

    def test_generate_refresh_token_returns_uuid_string(self, app):
        """Test that generate_refresh_token returns a UUID string"""
        with app.app_context():
            user = User(
                username="refreshtest",
                email="refresh@example.com",
                password_hash=PasswordService.hash_password("TestPass123"),
                role="player",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            token = TokenService.generate_refresh_token(user)
            assert isinstance(token, str)
            # Should be a valid UUID
            uuid.UUID(token)  # Will raise ValueError if invalid

    def test_generate_refresh_token_unique(self, app):
        """Test that each refresh token is unique"""
        with app.app_context():
            user = User(
                username="refreshtest2",
                email="refresh2@example.com",
                password_hash=PasswordService.hash_password("TestPass123"),
                role="player",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            token1 = TokenService.generate_refresh_token(user)
            token2 = TokenService.generate_refresh_token(user)
            assert token1 != token2


class TestVerifyToken:
    """Tests for verify_token"""

    def test_verify_token_valid(self, app):
        """Test verification of valid token"""
        with app.app_context():
            user = User(
                username="verifytest",
                email="verify@example.com",
                password_hash=PasswordService.hash_password("TestPass123"),
                role="player",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            token = TokenService.generate_access_token(user)
            payload = TokenService.verify_token(token)
            assert payload is not None
            assert payload["user_id"] == str(user.id)
            assert payload["username"] == user.username

    def test_verify_token_invalid_format(self, app):
        """Test verification of invalid token format"""
        with app.app_context():
            invalid_token = "not.a.valid.token"
            payload = TokenService.verify_token(invalid_token)
            assert payload is None

    def test_verify_token_wrong_secret(self, app):
        """Test verification of token signed with wrong secret"""
        with app.app_context():
            user = User(
                username="verifytest2",
                email="verify2@example.com",
                password_hash=PasswordService.hash_password("TestPass123"),
                role="player",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            # Generate token with correct secret
            token = TokenService.generate_access_token(user)
            # Change secret and try to verify
            original_secret = app.config["JWT_SECRET_KEY"]
            app.config["JWT_SECRET_KEY"] = "wrong-secret"
            payload = TokenService.verify_token(token)
            # Restore secret
            app.config["JWT_SECRET_KEY"] = original_secret
            assert payload is None

    def test_verify_token_expired(self, app):
        """Test verification of expired token"""
        with app.app_context():
            user = User(
                username="verifytest3",
                email="verify3@example.com",
                password_hash=PasswordService.hash_password("TestPass123"),
                role="player",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            # Generate token with very short expiration
            app.config["JWT_ACCESS_TOKEN_EXPIRATION"] = 1  # 1 second
            token = TokenService.generate_access_token(user)
            # Wait for token to expire
            time.sleep(2)
            payload = TokenService.verify_token(token)
            assert payload is None

    def test_verify_token_blacklisted(self, app):
        """Test that blacklisted tokens are rejected"""
        with app.app_context():
            from app import db

            user = User(
                username="verifytest4",
                email="verify4@example.com",
                password_hash=PasswordService.hash_password("TestPass123"),
                role="player",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.session.add(user)
            db.session.commit()

            token = TokenService.generate_access_token(user)
            payload = jwt.decode(
                token, app.config["JWT_SECRET_KEY"], algorithms=["HS256"]
            )
            token_id = payload["jti"]

            # Verify token is valid initially
            assert TokenService.verify_token(token) is not None

            # Blacklist the token
            expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
            TokenService.blacklist_token(token_id, str(user.id), expires_at)

            # Verify token is now rejected
            assert TokenService.verify_token(token) is None


class TestTokenBlacklist:
    """Tests for token blacklist functionality"""

    def test_is_token_blacklisted_not_blacklisted(self, app, db_session):
        """Test checking non-blacklisted token"""
        with app.app_context():
            token_id = str(uuid.uuid4())
            result = TokenService.is_token_blacklisted(token_id)
            assert result is False

    def test_is_token_blacklisted_blacklisted(self, app):
        """Test checking blacklisted token"""
        with app.app_context():
            from app import db

            user = User(
                username="blacklisttest",
                email="blacklist@example.com",
                password_hash=PasswordService.hash_password("TestPass123"),
                role="player",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.session.add(user)
            db.session.commit()

            token_id = str(uuid.uuid4())
            expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

            TokenService.blacklist_token(token_id, str(user.id), expires_at)
            result = TokenService.is_token_blacklisted(token_id)
            assert result is True

    def test_is_token_blacklisted_expired_entry(self, app):
        """Test that expired blacklist entries are cleaned up"""
        with app.app_context():
            from app import db

            user = User(
                username="blacklisttest2",
                email="blacklist2@example.com",
                password_hash=PasswordService.hash_password("TestPass123"),
                role="player",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.session.add(user)
            db.session.commit()

            token_id = str(uuid.uuid4())
            # Create expired blacklist entry
            expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
            blacklist_entry = TokenBlacklist(
                token_id=token_id,
                user_id=user.id,
                expires_at=expires_at,
                created_at=datetime.now(timezone.utc) - timedelta(hours=2),
            )
            db.session.add(blacklist_entry)
            db.session.commit()

            # Should return False and clean up expired entry
            result = TokenService.is_token_blacklisted(token_id)
            assert result is False

            # Verify entry was deleted
            entry = (
                db.session.query(TokenBlacklist).filter_by(token_id=token_id).first()
            )
            assert entry is None

    def test_blacklist_token_creates_entry(self, app):
        """Test that blacklist_token creates a blacklist entry"""
        with app.app_context():
            from app import db

            user = User(
                username="blacklisttest3",
                email="blacklist3@example.com",
                password_hash=PasswordService.hash_password("TestPass123"),
                role="player",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.session.add(user)
            db.session.commit()

            token_id = str(uuid.uuid4())
            expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

            TokenService.blacklist_token(token_id, str(user.id), expires_at)

            # Verify entry was created
            entry = (
                db.session.query(TokenBlacklist).filter_by(token_id=token_id).first()
            )
            assert entry is not None
            assert entry.token_id == token_id
            assert entry.user_id == user.id

    def test_blacklist_token_idempotent(self, app):
        """Test that blacklisting the same token twice doesn't create duplicates"""
        with app.app_context():
            from app import db

            user = User(
                username="blacklisttest4",
                email="blacklist4@example.com",
                password_hash=PasswordService.hash_password("TestPass123"),
                role="player",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.session.add(user)
            db.session.commit()

            token_id = str(uuid.uuid4())
            expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

            # Blacklist twice
            TokenService.blacklist_token(token_id, str(user.id), expires_at)
            TokenService.blacklist_token(token_id, str(user.id), expires_at)

            # Should only have one entry
            entries = (
                db.session.query(TokenBlacklist).filter_by(token_id=token_id).all()
            )
            assert len(entries) == 1


class TestGenerateServiceToken:
    """Tests for generate_service_token"""

    def test_generate_service_token_returns_string(self, app):
        """Test that generate_service_token returns a string"""
        with app.app_context():
            token = TokenService.generate_service_token("test-service", "test-id")
            assert isinstance(token, str)
            assert len(token) > 0

    def test_generate_service_token_contains_service_info(self, app):
        """Test that generated service token contains service information"""
        with app.app_context():
            service_name = "wiki-service"
            service_id = "wiki-123"
            token = TokenService.generate_service_token(service_name, service_id)
            payload = jwt.decode(
                token, app.config["JWT_SECRET_KEY"], algorithms=["HS256"]
            )
            assert payload["service_name"] == service_name
            assert payload["service_id"] == service_id
            assert payload["type"] == "service"
            assert "iat" in payload
            assert "exp" in payload

    def test_generate_service_token_has_long_expiration(self, app):
        """Test that service tokens have longer expiration (30 days)"""
        with app.app_context():
            token = TokenService.generate_service_token("test-service", "test-id")
            payload = jwt.decode(
                token, app.config["JWT_SECRET_KEY"], algorithms=["HS256"]
            )
            exp_time = payload["exp"]
            iat_time = payload["iat"]
            expiration_seconds = exp_time - iat_time
            expected_seconds = 30 * 24 * 60 * 60  # 30 days
            # Allow 1 second tolerance for timing
            assert abs(expiration_seconds - expected_seconds) <= 1

    def test_generate_service_token_structure(self, app):
        """Test that service tokens have correct structure"""
        with app.app_context():
            token = TokenService.generate_service_token("test-service", "test-id")
            # Token should be a valid JWT string
            assert isinstance(token, str)
            assert len(token) > 0
            # Should be decodable
            payload = jwt.decode(
                token, app.config["JWT_SECRET_KEY"], algorithms=["HS256"]
            )
            assert payload["service_name"] == "test-service"
            assert payload["service_id"] == "test-id"
