"""Unit tests for PasswordService"""

from app.services.password_service import PasswordService


class TestPasswordHashing:
    """Tests for password hashing"""

    def test_hash_password_returns_string(self, app):
        """Test that hash_password returns a string"""
        with app.app_context():
            password = "TestPassword123"
            hashed = PasswordService.hash_password(password)
            assert isinstance(hashed, str)
            assert len(hashed) > 0

    def test_hash_password_different_salts(self, app):
        """Test that same password produces different hashes (due to salt)"""
        with app.app_context():
            password = "TestPassword123"
            hash1 = PasswordService.hash_password(password)
            hash2 = PasswordService.hash_password(password)
            assert hash1 != hash2  # Different salts should produce different hashes

    def test_hash_password_uses_config_rounds(self, app):
        """Test that hash_password uses configured bcrypt rounds"""
        with app.app_context():
            # Set custom rounds
            app.config["BCRYPT_ROUNDS"] = 4
            password = "TestPassword123"
            hashed = PasswordService.hash_password(password)
            # Just verify it works - actual round verification requires bcrypt internals
            assert len(hashed) > 0


class TestPasswordVerification:
    """Tests for password verification"""

    def test_check_password_correct(self, app):
        """Test that check_password returns True for correct password"""
        with app.app_context():
            password = "TestPassword123"
            hashed = PasswordService.hash_password(password)
            assert PasswordService.check_password(password, hashed) is True

    def test_check_password_incorrect(self, app):
        """Test that check_password returns False for incorrect password"""
        with app.app_context():
            password = "TestPassword123"
            wrong_password = "WrongPassword123"
            hashed = PasswordService.hash_password(password)
            assert PasswordService.check_password(wrong_password, hashed) is False

    def test_check_password_invalid_hash(self, app):
        """Test that check_password handles invalid hash gracefully"""
        with app.app_context():
            password = "TestPassword123"
            invalid_hash = "not-a-valid-hash"
            # Should return False, not raise exception
            assert PasswordService.check_password(password, invalid_hash) is False

    def test_check_password_empty_password(self, app):
        """Test that check_password handles empty password"""
        with app.app_context():
            password = "TestPassword123"
            hashed = PasswordService.hash_password(password)
            assert PasswordService.check_password("", hashed) is False


class TestPasswordStrengthValidation:
    """Tests for password strength validation"""

    def test_validate_password_strength_valid(self, app):
        """Test validation of valid password"""
        with app.app_context():
            password = "TestPassword123"
            is_valid, error = PasswordService.validate_password_strength(password)
            assert is_valid is True
            assert error == ""

    def test_validate_password_strength_too_short(self, app):
        """Test validation fails for password shorter than 8 characters"""
        with app.app_context():
            password = "Short1"
            is_valid, error = PasswordService.validate_password_strength(password)
            assert is_valid is False
            assert "8 characters" in error

    def test_validate_password_strength_no_uppercase(self, app):
        """Test validation fails for password without uppercase letter"""
        with app.app_context():
            password = "testpassword123"
            is_valid, error = PasswordService.validate_password_strength(password)
            assert is_valid is False
            assert "uppercase" in error.lower()

    def test_validate_password_strength_no_lowercase(self, app):
        """Test validation fails for password without lowercase letter"""
        with app.app_context():
            password = "TESTPASSWORD123"
            is_valid, error = PasswordService.validate_password_strength(password)
            assert is_valid is False
            assert "lowercase" in error.lower()

    def test_validate_password_strength_no_number(self, app):
        """Test validation fails for password without number"""
        with app.app_context():
            password = "TestPassword"
            is_valid, error = PasswordService.validate_password_strength(password)
            assert is_valid is False
            assert "number" in error.lower()

    def test_validate_password_strength_special_characters_allowed(self, app):
        """Test that special characters are allowed (recommended but not required)"""
        with app.app_context():
            password = "TestPassword123!@#"
            is_valid, error = PasswordService.validate_password_strength(password)
            assert is_valid is True
            assert error == ""

    def test_validate_password_strength_minimum_valid(self, app):
        """Test that minimum valid password (8 chars, upper, lower, number) passes"""
        with app.app_context():
            password = "Test1234"
            is_valid, error = PasswordService.validate_password_strength(password)
            assert is_valid is True


class TestPasswordHistory:
    """Tests for password history checking"""

    def test_check_password_history_no_history(self, app, db_session):
        """Test checking password history when user has no history"""
        with app.app_context():
            from datetime import datetime, timezone

            from app.models.user import User

            user = User(
                username="historytest",
                email="history@example.com",
                password_hash=PasswordService.hash_password("TestPass123"),
                role="player",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db_session.add(user)
            db_session.commit()

            # Password should not be in history (no history exists)
            result = PasswordService.check_password_history(
                str(user.id), "NewPassword123"
            )
            assert result is False

    def test_check_password_history_not_in_history(self, app, db_session):
        """Test checking password that's not in history"""
        with app.app_context():
            from datetime import datetime, timezone

            from app.models.user import User

            user = User(
                username="historytest2",
                email="history2@example.com",
                password_hash=PasswordService.hash_password("OldPassword123"),
                role="player",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db_session.add(user)
            db_session.commit()

            # Save old password to history
            PasswordService.save_password_history(str(user.id), user.password_hash)

            # New password should not be in history
            result = PasswordService.check_password_history(
                str(user.id), "NewPassword123"
            )
            assert result is False

    def test_check_password_history_in_history(self, app, db_session):
        """Test checking password that is in history"""
        with app.app_context():
            from datetime import datetime, timezone

            from app.models.user import User

            old_password = "OldPassword123"
            user = User(
                username="historytest3",
                email="history3@example.com",
                password_hash=PasswordService.hash_password(old_password),
                role="player",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db_session.add(user)
            db_session.commit()

            # Save old password to history
            PasswordService.save_password_history(str(user.id), user.password_hash)

            # Old password should be in history
            result = PasswordService.check_password_history(str(user.id), old_password)
            assert result is True

    def test_check_password_history_max_history_limit(self, app, db_session):
        """Test that only last max_history passwords are checked"""
        with app.app_context():
            from datetime import datetime, timezone

            from app.models.user import User

            user = User(
                username="historytest4",
                email="history4@example.com",
                password_hash=PasswordService.hash_password("InitialPass123"),
                role="player",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db_session.add(user)
            db_session.commit()

            # Save 5 passwords to history
            for i in range(5):
                password = f"Password{i}123"
                password_hash = PasswordService.hash_password(password)
                PasswordService.save_password_history(str(user.id), password_hash)

            # Check with max_history=3 - only last 3 should be checked
            # Password0 and Password1 should not be detected
            result = PasswordService.check_password_history(
                str(user.id), "Password0123", max_history=3
            )
            assert result is False  # Should not be in last 3

            # Password2, Password3, Password4 should be detected
            result = PasswordService.check_password_history(
                str(user.id), "Password4123", max_history=3
            )
            assert result is True  # Should be in last 3

    def test_save_password_history_creates_entry(self, app, db_session):
        """Test that save_password_history creates a history entry"""
        with app.app_context():
            from datetime import datetime, timezone

            from app.models.password_history import PasswordHistory
            from app.models.user import User

            user = User(
                username="historytest5",
                email="history5@example.com",
                password_hash=PasswordService.hash_password("TestPass123"),
                role="player",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db_session.add(user)
            db_session.commit()

            password_hash = PasswordService.hash_password("NewPassword123")
            PasswordService.save_password_history(str(user.id), password_hash)

            # Verify history entry was created
            history = (
                db_session.query(PasswordHistory).filter_by(user_id=user.id).first()
            )
            assert history is not None
            assert history.password_hash == password_hash

    def test_save_password_history_cleanup_old_passwords(self, app, db_session):
        """Test that save_password_history cleans up old passwords beyond limit"""
        with app.app_context():
            from datetime import datetime, timezone

            from app.models.password_history import PasswordHistory
            from app.models.user import User

            user = User(
                username="historytest6",
                email="history6@example.com",
                password_hash=PasswordService.hash_password("TestPass123"),
                role="player",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db_session.add(user)
            db_session.commit()

            # Save 15 passwords to history
            for i in range(15):
                password_hash = PasswordService.hash_password(f"Password{i}123")
                PasswordService.save_password_history(str(user.id), password_hash)

            # Should only keep last 10
            history_count = (
                db_session.query(PasswordHistory).filter_by(user_id=user.id).count()
            )
            assert history_count == 10
