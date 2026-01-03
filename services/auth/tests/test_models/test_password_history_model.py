"""Unit tests for PasswordHistory model"""

from datetime import datetime, timezone

import pytest
from app.models.password_history import PasswordHistory
from app.models.user import User
from app.services.password_service import PasswordService


class TestPasswordHistoryModel:
    """Tests for PasswordHistory model"""

    @pytest.fixture
    def test_user(self, app):
        """Create a test user for password history tests"""
        with app.app_context():
            from app import db

            user = User(
                username="historytest",
                email="history@example.com",
                password_hash=PasswordService.hash_password("TestPass123"),
                role="player",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            db.session.add(user)
            db.session.commit()
            return user.id

    def test_password_history_creation(self, app, test_user):
        """Test creating a password history entry"""
        with app.app_context():
            from app import db

            password_hash = PasswordService.hash_password("TestPass123")

            history_entry = PasswordHistory(
                user_id=test_user,
                password_hash=password_hash,
                created_at=datetime.now(timezone.utc),
            )

            db.session.add(history_entry)
            db.session.commit()

            assert history_entry.id is not None
            assert history_entry.user_id == test_user
            assert history_entry.password_hash == password_hash

    def test_password_history_timestamps(self, app, test_user):
        """Test password history timestamp field"""
        with app.app_context():
            from app import db

            password_hash = PasswordService.hash_password("TestPass123")

            history_entry = PasswordHistory(
                user_id=test_user,
                password_hash=password_hash,
                created_at=datetime.now(timezone.utc),
            )

            db.session.add(history_entry)
            db.session.commit()

            # Verify timestamp exists (may be stored as naive but represents UTC)
            assert history_entry.created_at is not None

    def test_password_history_cascade_delete(self, app, test_user):
        """Test that password history is deleted when user is deleted"""
        with app.app_context():
            from app import db

            password_hash = PasswordService.hash_password("TestPass123")

            history_entry = PasswordHistory(
                user_id=test_user,
                password_hash=password_hash,
                created_at=datetime.now(timezone.utc),
            )

            db.session.add(history_entry)
            db.session.commit()

            # Verify history entry exists
            assert history_entry.id is not None

            # Delete user
            user = db.session.query(User).filter_by(id=test_user).first()
            db.session.delete(user)
            db.session.commit()

            # Verify history entry is also deleted (due to CASCADE)
            deleted_entry = (
                db.session.query(PasswordHistory).filter_by(id=history_entry.id).first()
            )
            assert deleted_entry is None

    def test_password_history_multiple_entries(self, app, test_user):
        """Test that a user can have multiple password history entries"""
        with app.app_context():
            from app import db

            password_hash1 = PasswordService.hash_password("Password1")
            password_hash2 = PasswordService.hash_password("Password2")
            password_hash3 = PasswordService.hash_password("Password3")

            history1 = PasswordHistory(
                user_id=test_user,
                password_hash=password_hash1,
                created_at=datetime.now(timezone.utc),
            )

            history2 = PasswordHistory(
                user_id=test_user,
                password_hash=password_hash2,
                created_at=datetime.now(timezone.utc),
            )

            history3 = PasswordHistory(
                user_id=test_user,
                password_hash=password_hash3,
                created_at=datetime.now(timezone.utc),
            )

            db.session.add(history1)
            db.session.add(history2)
            db.session.add(history3)
            db.session.commit()

            # Verify all entries exist
            history_count = (
                db.session.query(PasswordHistory).filter_by(user_id=test_user).count()
            )
            assert history_count == 3
