"""Unit tests for TokenBlacklist model"""

from datetime import datetime, timedelta, timezone

import pytest
from app.models.token_blacklist import TokenBlacklist
from app.models.user import User
from app.services.password_service import PasswordService


class TestTokenBlacklistModel:
    """Tests for TokenBlacklist model"""

    @pytest.fixture
    def test_user(self, app):
        """Create a test user for token blacklist tests"""
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
            return user.id

    def test_token_blacklist_creation(self, app, test_user):
        """Test creating a token blacklist entry"""
        with app.app_context():
            from app import db

            expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
            blacklist_entry = TokenBlacklist(
                token_id="test-token-id-123",
                user_id=test_user,
                expires_at=expires_at.replace(tzinfo=None),
                created_at=datetime.now(timezone.utc).replace(tzinfo=None),
            )

            db.session.add(blacklist_entry)
            db.session.commit()

            assert blacklist_entry.id is not None
            assert blacklist_entry.token_id == "test-token-id-123"
            assert blacklist_entry.user_id == test_user

    def test_token_blacklist_is_expired_not_expired(self, app, test_user):
        """Test is_expired method for non-expired entry"""
        with app.app_context():
            from app import db

            # Use a future expiration time (1 hour from now)
            future_expires = datetime.now(timezone.utc) + timedelta(hours=1)
            blacklist_entry = TokenBlacklist(
                token_id="test-token-id",
                user_id=test_user,
                expires_at=future_expires.replace(tzinfo=None),
                created_at=datetime.now(timezone.utc).replace(tzinfo=None),
            )

            db.session.add(blacklist_entry)
            db.session.commit()

            # Refresh from database to ensure we're testing the actual stored value
            db.session.refresh(blacklist_entry)
            assert blacklist_entry.is_expired() is False

    def test_token_blacklist_is_expired_expired(self, app, test_user):
        """Test is_expired method for expired entry"""
        with app.app_context():
            from app import db

            expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
            created_at = datetime.now(timezone.utc) - timedelta(hours=2)
            blacklist_entry = TokenBlacklist(
                token_id="test-token-id",
                user_id=test_user,
                expires_at=expires_at.replace(tzinfo=None),
                created_at=created_at.replace(tzinfo=None),
            )

            db.session.add(blacklist_entry)
            db.session.commit()

            assert blacklist_entry.is_expired() is True

    def test_token_blacklist_repr(self, app, test_user):
        """Test token blacklist __repr__ method"""
        with app.app_context():
            from app import db

            blacklist_entry = TokenBlacklist(
                token_id="test-token-id",
                user_id=test_user,
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
                created_at=datetime.now(timezone.utc),
            )

            db.session.add(blacklist_entry)
            db.session.commit()

            repr_str = repr(blacklist_entry)
            assert "TokenBlacklist" in repr_str
            assert "test-token-id" in repr_str

    def test_token_blacklist_user_id_nullable(self, app):
        """Test that user_id can be null"""
        with app.app_context():
            from app import db

            expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
            blacklist_entry = TokenBlacklist(
                token_id="test-token-id",
                user_id=None,
                expires_at=expires_at.replace(tzinfo=None),
                created_at=datetime.now(timezone.utc).replace(tzinfo=None),
            )

            db.session.add(blacklist_entry)
            db.session.commit()

            assert blacklist_entry.user_id is None
