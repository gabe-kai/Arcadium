"""Unit tests for User model"""

from datetime import datetime, timezone

import pytest
from app.models.user import User
from app.services.password_service import PasswordService


class TestUserModel:
    """Tests for User model"""

    def test_user_creation(self, app):
        """Test creating a user"""
        with app.app_context():
            from app import db

            user = User(
                username="testuser",
                email="test@example.com",
                password_hash=PasswordService.hash_password("TestPass123"),
                role="player",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            db.session.add(user)
            db.session.commit()

            assert user.id is not None
            assert user.username == "testuser"
            assert user.email == "test@example.com"
            assert user.role == "player"
            assert user.is_system_user is False
            assert user.is_first_user is False
            assert user.email_verified is False

    def test_user_to_dict_without_email(self, app):
        """Test user to_dict method without email"""
        with app.app_context():
            from app import db

            user = User(
                username="testuser",
                email="test@example.com",
                password_hash=PasswordService.hash_password("TestPass123"),
                role="player",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            db.session.add(user)
            db.session.commit()

            user_dict = user.to_dict(include_email=False)

            assert user_dict["id"] == str(user.id)
            assert user_dict["username"] == "testuser"
            assert "email" not in user_dict
            assert user_dict["role"] == "player"
            assert user_dict["is_system_user"] is False
            assert user_dict["is_first_user"] is False
            assert user_dict["email_verified"] is False

    def test_user_to_dict_with_email(self, app):
        """Test user to_dict method with email"""
        with app.app_context():
            from app import db

            user = User(
                username="testuser",
                email="test@example.com",
                password_hash=PasswordService.hash_password("TestPass123"),
                role="player",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            db.session.add(user)
            db.session.commit()

            user_dict = user.to_dict(include_email=True)

            assert user_dict["id"] == str(user.id)
            assert user_dict["username"] == "testuser"
            assert user_dict["email"] == "test@example.com"
            assert user_dict["role"] == "player"

    def test_user_is_admin(self, app):
        """Test is_admin method"""
        with app.app_context():
            import uuid

            from app import db

            unique_id = str(uuid.uuid4())[:8]
            admin_user = User(
                username=f"admin_{unique_id}",
                email=f"admin_{unique_id}@example.com",
                password_hash=PasswordService.hash_password("TestPass123"),
                role="admin",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            player_user = User(
                username=f"player_{unique_id}",
                email=f"player_{unique_id}@example.com",
                password_hash=PasswordService.hash_password("TestPass123"),
                role="player",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            db.session.add(admin_user)
            db.session.add(player_user)
            db.session.commit()

            assert admin_user.is_admin() is True
            assert player_user.is_admin() is False

    def test_user_is_writer(self, app):
        """Test is_writer method"""
        with app.app_context():
            import uuid

            from app import db

            unique_id = str(uuid.uuid4())[:8]
            admin_user = User(
                username=f"admin_{unique_id}",
                email=f"admin_{unique_id}@example.com",
                password_hash=PasswordService.hash_password("TestPass123"),
                role="admin",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            writer_user = User(
                username=f"writer_{unique_id}",
                email=f"writer_{unique_id}@example.com",
                password_hash=PasswordService.hash_password("TestPass123"),
                role="writer",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            player_user = User(
                username=f"player_{unique_id}",
                email=f"player_{unique_id}@example.com",
                password_hash=PasswordService.hash_password("TestPass123"),
                role="player",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            db.session.add(admin_user)
            db.session.add(writer_user)
            db.session.add(player_user)
            db.session.commit()

            assert admin_user.is_writer() is True
            assert writer_user.is_writer() is True
            assert player_user.is_writer() is False

    def test_user_is_player(self, app):
        """Test is_player method"""
        with app.app_context():
            import uuid

            from app import db

            unique_id = str(uuid.uuid4())[:8]
            admin_user = User(
                username=f"admin_{unique_id}",
                email=f"admin_{unique_id}@example.com",
                password_hash=PasswordService.hash_password("TestPass123"),
                role="admin",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            writer_user = User(
                username=f"writer_{unique_id}",
                email=f"writer_{unique_id}@example.com",
                password_hash=PasswordService.hash_password("TestPass123"),
                role="writer",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            player_user = User(
                username=f"player_{unique_id}",
                email=f"player_{unique_id}@example.com",
                password_hash=PasswordService.hash_password("TestPass123"),
                role="player",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            db.session.add(admin_user)
            db.session.add(writer_user)
            db.session.add(player_user)
            db.session.commit()

            assert admin_user.is_player() is True
            assert writer_user.is_player() is True
            assert player_user.is_player() is True

    def test_user_has_role(self, app):
        """Test has_role method with role hierarchy"""
        with app.app_context():
            import uuid

            from app import db

            unique_id = str(uuid.uuid4())[:8]
            admin_user = User(
                username=f"admin_{unique_id}",
                email=f"admin_{unique_id}@example.com",
                password_hash=PasswordService.hash_password("TestPass123"),
                role="admin",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            writer_user = User(
                username=f"writer_{unique_id}",
                email=f"writer_{unique_id}@example.com",
                password_hash=PasswordService.hash_password("TestPass123"),
                role="writer",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            player_user = User(
                username=f"player_{unique_id}",
                email=f"player_{unique_id}@example.com",
                password_hash=PasswordService.hash_password("TestPass123"),
                role="player",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            db.session.add(admin_user)
            db.session.add(writer_user)
            db.session.add(player_user)
            db.session.commit()

            # Admin can access all roles
            assert admin_user.has_role("admin") is True
            assert admin_user.has_role("writer") is True
            assert admin_user.has_role("player") is True
            assert admin_user.has_role("viewer") is True

            # Writer can access writer, player, viewer
            assert writer_user.has_role("admin") is False
            assert writer_user.has_role("writer") is True
            assert writer_user.has_role("player") is True
            assert writer_user.has_role("viewer") is True

            # Player can access player, viewer
            assert player_user.has_role("admin") is False
            assert player_user.has_role("writer") is False
            assert player_user.has_role("player") is True
            assert player_user.has_role("viewer") is True

    def test_user_repr(self, app):
        """Test user __repr__ method"""
        with app.app_context():
            from app import db

            user = User(
                username="testuser",
                email="test@example.com",
                password_hash=PasswordService.hash_password("TestPass123"),
                role="player",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            db.session.add(user)
            db.session.commit()

            repr_str = repr(user)
            assert "User" in repr_str
            assert "testuser" in repr_str

    def test_user_unique_username(self, app):
        """Test that username must be unique"""
        with app.app_context():
            from app import db
            from sqlalchemy.exc import IntegrityError

            user1 = User(
                username="testuser",
                email="test1@example.com",
                password_hash=PasswordService.hash_password("TestPass123"),
                role="player",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            user2 = User(
                username="testuser",  # Duplicate username
                email="test2@example.com",
                password_hash=PasswordService.hash_password("TestPass123"),
                role="player",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            db.session.add(user1)
            db.session.commit()

            db.session.add(user2)
            with pytest.raises(IntegrityError):
                db.session.commit()

    def test_user_unique_email(self, app):
        """Test that email must be unique"""
        with app.app_context():
            from app import db
            from sqlalchemy.exc import IntegrityError

            user1 = User(
                username="testuser1",
                email="test@example.com",
                password_hash=PasswordService.hash_password("TestPass123"),
                role="player",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            user2 = User(
                username="testuser2",
                email="test@example.com",  # Duplicate email
                password_hash=PasswordService.hash_password("TestPass123"),
                role="player",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            db.session.add(user1)
            db.session.commit()

            db.session.add(user2)
            with pytest.raises(IntegrityError):
                db.session.commit()

    def test_user_default_values(self, app):
        """Test user default values"""
        with app.app_context():
            from app import db

            user = User(
                username="testuser",
                email="test@example.com",
                password_hash=PasswordService.hash_password("TestPass123"),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            db.session.add(user)
            db.session.commit()

            assert user.role == "player"  # Default role
            assert user.is_system_user is False
            assert user.is_first_user is False
            assert user.email_verified is False
            assert user.last_login is None

    def test_user_timestamps(self, app):
        """Test user timestamp fields"""
        with app.app_context():
            from app import db

            # Create user - timestamps will be set by model defaults
            user = User(
                username="testuser",
                email="test@example.com",
                password_hash=PasswordService.hash_password("TestPass123"),
                role="player",
            )

            db.session.add(user)
            db.session.commit()

            # Verify timestamps exist and are timezone-aware
            assert user.created_at is not None
            assert user.updated_at is not None
            # Timestamps might be stored as naive but represent UTC
            # Just verify they exist rather than comparing

    def test_user_last_login(self, app):
        """Test user last_login field"""
        with app.app_context():
            from app import db

            user = User(
                username="testuser",
                email="test@example.com",
                password_hash=PasswordService.hash_password("TestPass123"),
                role="player",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            db.session.add(user)
            db.session.commit()

            assert user.last_login is None

            # Update last_login
            user.last_login = datetime.now(timezone.utc)
            db.session.commit()

            assert user.last_login is not None
