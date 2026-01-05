"""Unit tests for validators"""

from app.utils.validators import (
    sanitize_username,
    validate_email,
    validate_password,
    validate_username,
)


class TestValidateUsername:
    """Tests for validate_username function"""

    def test_validate_username_valid(self):
        """Test validation of valid username"""
        is_valid, error = validate_username("testuser")
        assert is_valid is True
        assert error == ""

    def test_validate_username_valid_with_underscore(self):
        """Test validation of username with underscore"""
        is_valid, error = validate_username("test_user")
        assert is_valid is True
        assert error == ""

    def test_validate_username_valid_with_hyphen(self):
        """Test validation of username with hyphen"""
        is_valid, error = validate_username("test-user")
        assert is_valid is True
        assert error == ""

    def test_validate_username_valid_with_numbers(self):
        """Test validation of username with numbers"""
        is_valid, error = validate_username("test123")
        assert is_valid is True
        assert error == ""

    def test_validate_username_empty(self):
        """Test validation of empty username"""
        is_valid, error = validate_username("")
        assert is_valid is False
        assert "required" in error.lower()

    def test_validate_username_too_short(self):
        """Test validation of username shorter than 3 characters"""
        is_valid, error = validate_username("ab")
        assert is_valid is False
        assert "3 characters" in error

    def test_validate_username_too_long(self):
        """Test validation of username longer than 100 characters"""
        long_username = "a" * 101
        is_valid, error = validate_username(long_username)
        assert is_valid is False
        assert "100 characters" in error

    def test_validate_username_invalid_characters(self):
        """Test validation of username with invalid characters"""
        is_valid, error = validate_username("test user")
        assert is_valid is False
        assert "letters, numbers" in error.lower() or "letters" in error.lower()

    def test_validate_username_starts_with_invalid(self):
        """Test validation of username starting with invalid character"""
        is_valid, error = validate_username("_testuser")
        assert is_valid is False
        assert "start" in error.lower()

    def test_validate_username_minimum_length(self):
        """Test validation of username with exactly 3 characters (minimum)"""
        is_valid, error = validate_username("abc")
        assert is_valid is True
        assert error == ""

    def test_validate_username_maximum_length(self):
        """Test validation of username with exactly 100 characters (maximum)"""
        max_username = "a" * 100
        is_valid, error = validate_username(max_username)
        assert is_valid is True
        assert error == ""


class TestValidateEmail:
    """Tests for validate_email function"""

    def test_validate_email_valid(self):
        """Test validation of valid email"""
        is_valid, error = validate_email("test@example.com")
        assert is_valid is True
        assert error == ""

    def test_validate_email_valid_with_subdomain(self):
        """Test validation of email with subdomain"""
        is_valid, error = validate_email("test@mail.example.com")
        assert is_valid is True
        assert error == ""

    def test_validate_email_valid_with_plus(self):
        """Test validation of email with plus sign"""
        is_valid, error = validate_email("test+tag@example.com")
        assert is_valid is True
        assert error == ""

    def test_validate_email_valid_with_dots(self):
        """Test validation of email with dots"""
        is_valid, error = validate_email("test.user@example.com")
        assert is_valid is True
        assert error == ""

    def test_validate_email_empty(self):
        """Test validation of empty email"""
        is_valid, error = validate_email("")
        assert is_valid is False
        assert "required" in error.lower()

    def test_validate_email_no_at_sign(self):
        """Test validation of email without @ sign"""
        is_valid, error = validate_email("testexample.com")
        assert is_valid is False
        assert "format" in error.lower()

    def test_validate_email_no_domain(self):
        """Test validation of email without domain"""
        is_valid, error = validate_email("test@")
        assert is_valid is False
        assert "format" in error.lower()

    def test_validate_email_no_tld(self):
        """Test validation of email without TLD"""
        is_valid, error = validate_email("test@example")
        assert is_valid is False
        assert "format" in error.lower()

    def test_validate_email_too_long(self):
        """Test validation of email longer than 255 characters"""
        long_email = "a" * 250 + "@example.com"
        is_valid, error = validate_email(long_email)
        assert is_valid is False
        assert "255 characters" in error

    def test_validate_email_maximum_length(self):
        """Test validation of email with exactly 255 characters"""
        # Create email that's exactly 255 chars: 244 chars local + @example.com (11 chars)
        max_email = "a" * 243 + "@example.com"
        assert len(max_email) == 255
        is_valid, error = validate_email(max_email)
        assert is_valid is True
        assert error == ""


class TestValidatePassword:
    """Tests for validate_password function (wrapper around PasswordService)"""

    def test_validate_password_valid(self, app):
        """Test validation of valid password"""
        with app.app_context():
            is_valid, error = validate_password("TestPass123")
            assert is_valid is True
            assert error == ""

    def test_validate_password_too_short(self, app):
        """Test validation of password shorter than 8 characters"""
        with app.app_context():
            is_valid, error = validate_password("Short1")
            assert is_valid is False
            assert "8 characters" in error

    def test_validate_password_no_uppercase(self, app):
        """Test validation of password without uppercase letter"""
        with app.app_context():
            is_valid, error = validate_password("testpass123")
            assert is_valid is False
            assert "uppercase" in error.lower()

    def test_validate_password_no_lowercase(self, app):
        """Test validation of password without lowercase letter"""
        with app.app_context():
            is_valid, error = validate_password("TESTPASS123")
            assert is_valid is False
            assert "lowercase" in error.lower()

    def test_validate_password_no_number(self, app):
        """Test validation of password without number"""
        with app.app_context():
            is_valid, error = validate_password("TestPassword")
            assert is_valid is False
            assert "number" in error.lower()

    def test_validate_password_special_characters_allowed(self, app):
        """Test that special characters are allowed"""
        with app.app_context():
            is_valid, error = validate_password("TestPass123!@#")
            assert is_valid is True
            assert error == ""

    def test_validate_password_minimum_valid(self, app):
        """Test that minimum valid password passes"""
        with app.app_context():
            is_valid, error = validate_password("Test1234")
            assert is_valid is True
            assert error == ""


class TestSanitizeUsername:
    """Tests for sanitize_username function"""

    def test_sanitize_username_lowercase(self):
        """Test that username is converted to lowercase"""
        result = sanitize_username("TestUser")
        assert result == "testuser"

    def test_sanitize_username_trim_whitespace(self):
        """Test that leading and trailing whitespace is trimmed"""
        result = sanitize_username("  testuser  ")
        assert result == "testuser"

    def test_sanitize_username_lowercase_and_trim(self):
        """Test that username is lowercased and trimmed"""
        result = sanitize_username("  TestUser  ")
        assert result == "testuser"

    def test_sanitize_username_no_change_needed(self):
        """Test that username that's already lowercase and trimmed is unchanged"""
        result = sanitize_username("testuser")
        assert result == "testuser"

    def test_sanitize_username_preserves_internal_characters(self):
        """Test that internal characters (numbers, underscores, hyphens) are preserved"""
        result = sanitize_username("  Test_User-123  ")
        assert result == "test_user-123"
