"""Unit tests for RefreshToken model"""

from datetime import datetime, timedelta, timezone

import pytest
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.services.password_service import PasswordService


class TestRefreshTokenModel:
    """Tests for RefreshToken model"""

    @pytest.fixture
    def test_user(self, app):
        """Create a test user for refresh token tests"""
        with app.app_context():
            from app import db

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
            return user.id

    def test_refresh_token_creation(self, app, test_user):
        """Test creating a refresh token"""
        with app.app_context():
            from app import db

            refresh_token = RefreshToken(
                user_id=test_user,
                token_hash="test-token-hash-123",
                expires_at=datetime.now(timezone.utc) + timedelta(days=7),
                created_at=datetime.now(timezone.utc),
            )

            db.session.add(refresh_token)
            db.session.commit()

            assert refresh_token.id is not None
            assert refresh_token.user_id == test_user
            assert refresh_token.token_hash == "test-token-hash-123"
            assert refresh_token.last_used_at is None

    def test_refresh_token_is_expired_not_expired(self, app, test_user):
        """Test is_expired method for non-expired token"""
        with app.app_context():
            from app import db

            refresh_token = RefreshToken(
                user_id=test_user,
                token_hash="test-token-hash",
                expires_at=datetime.now(timezone.utc) + timedelta(days=7),
                created_at=datetime.now(timezone.utc),
            )

            db.session.add(refresh_token)
            db.session.commit()

            assert refresh_token.is_expired() is False

    def test_refresh_token_is_expired_expired(self, app, test_user):
        """Test is_expired method for expired token"""
        with app.app_context():
            from app import db

            refresh_token = RefreshToken(
                user_id=test_user,
                token_hash="test-token-hash",
                expires_at=datetime.now(timezone.utc) - timedelta(days=1),
                created_at=datetime.now(timezone.utc) - timedelta(days=2),
            )

            db.session.add(refresh_token)
            db.session.commit()

            assert refresh_token.is_expired() is True

    def test_refresh_token_repr(self, app, test_user):
        """Test refresh token __repr__ method"""
        with app.app_context():
            from app import db

            refresh_token = RefreshToken(
                user_id=test_user,
                token_hash="test-token-hash",
                expires_at=datetime.now(timezone.utc) + timedelta(days=7),
                created_at=datetime.now(timezone.utc),
            )

            db.session.add(refresh_token)
            db.session.commit()

            repr_str = repr(refresh_token)
            assert "RefreshToken" in repr_str

    def test_refresh_token_user_relationship(self, app, test_user):
        """Test refresh token user relationship"""
        with app.app_context():
            from app import db

            refresh_token = RefreshToken(
                user_id=test_user,
                token_hash="test-token-hash",
                expires_at=datetime.now(timezone.utc) + timedelta(days=7),
                created_at=datetime.now(timezone.utc),
            )

            db.session.add(refresh_token)
            db.session.commit()

            # Test relationship
            user = db.session.query(User).filter_by(id=test_user).first()
            assert user is not None
            assert refresh_token.user_id == user.id

    def test_refresh_token_unique_token_hash(self, app, test_user):
        """Test that token_hash must be unique"""
        with app.app_context():
            from app import db
            from sqlalchemy.exc import IntegrityError

            refresh_token1 = RefreshToken(
                user_id=test_user,
                token_hash="unique-token-hash",
                expires_at=datetime.now(timezone.utc) + timedelta(days=7),
                created_at=datetime.now(timezone.utc),
            )

            refresh_token2 = RefreshToken(
                user_id=test_user,
                token_hash="unique-token-hash",  # Duplicate token_hash
                expires_at=datetime.now(timezone.utc) + timedelta(days=7),
                created_at=datetime.now(timezone.utc),
            )

            db.session.add(refresh_token1)
            db.session.commit()

            db.session.add(refresh_token2)
            with pytest.raises(IntegrityError):
                db.session.commit()

    def test_refresh_token_last_used_at(self, app, test_user):
        """Test refresh token last_used_at field"""
        with app.app_context():
            from app import db

            refresh_token = RefreshToken(
                user_id=test_user,
                token_hash="test-token-hash",
                expires_at=datetime.now(timezone.utc) + timedelta(days=7),
                created_at=datetime.now(timezone.utc),
            )

            db.session.add(refresh_token)
            db.session.commit()

            assert refresh_token.last_used_at is None

            # Update last_used_at
            refresh_token.last_used_at = datetime.now(timezone.utc)
            db.session.commit()

            assert refresh_token.last_used_at is not None
