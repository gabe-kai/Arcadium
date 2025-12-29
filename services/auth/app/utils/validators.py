"""
Input validators for authentication.
"""

import re
from typing import Tuple


def validate_username(username: str) -> Tuple[bool, str]:
    """
    Validate username format.

    Rules:
    - 3-100 characters
    - Alphanumeric + underscore/hyphen only
    - Must start with letter or number

    Args:
        username: Username to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not username:
        return False, "Username is required"

    if len(username) < 3:
        return False, "Username must be at least 3 characters long"

    if len(username) > 100:
        return False, "Username must be no more than 100 characters long"

    # Alphanumeric + underscore/hyphen only
    if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$", username):
        return (
            False,
            "Username can only contain letters, numbers, underscores, and hyphens, and must start with a letter or number",
        )

    return True, ""


def validate_email(email: str) -> Tuple[bool, str]:
    """
    Validate email format.

    Args:
        email: Email to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not email:
        return False, "Email is required"

    # Basic email regex (RFC 5322 compliant would be more complex)
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if not re.match(email_pattern, email):
        return False, "Invalid email format"

    if len(email) > 255:
        return False, "Email must be no more than 255 characters long"

    return True, ""


def validate_password(password: str) -> Tuple[bool, str]:
    """
    Validate password strength.

    This is a wrapper around PasswordService.validate_password_strength
    for consistency with other validators.

    Args:
        password: Password to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    from app.services.password_service import PasswordService

    return PasswordService.validate_password_strength(password)


def sanitize_username(username: str) -> str:
    """
    Sanitize username input.

    Removes leading/trailing whitespace and converts to lowercase.

    Args:
        username: Username to sanitize

    Returns:
        Sanitized username
    """
    return username.strip().lower()
