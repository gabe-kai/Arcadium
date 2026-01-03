"""
JWT token validation utilities for shared use across services.

These utilities provide token validation and decoding functionality
that can be used by any service that needs to validate JWT tokens
from the Auth Service.
"""

import uuid
from typing import Dict, Optional

import jwt


def validate_jwt_token(
    token: str, secret: str, algorithm: str = "HS256"
) -> Optional[Dict]:
    """
    Validate and decode a JWT token.

    Args:
        token: JWT token string to validate
        secret: Secret key used to sign the token
        algorithm: JWT algorithm (default: HS256)

    Returns:
        Decoded token payload dictionary if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, secret, algorithms=[algorithm])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def decode_token(token: str, secret: str, algorithm: str = "HS256") -> Optional[Dict]:
    """
    Decode a JWT token without validation (for debugging/inspection only).

    WARNING: This function does not validate the token signature or expiration.
    Use validate_jwt_token() for secure token validation in production code.

    Args:
        token: JWT token string to decode
        secret: Secret key (not used for validation, but required by jwt.decode)
        algorithm: JWT algorithm (default: HS256)

    Returns:
        Decoded token payload dictionary, None if decoding fails
    """
    try:
        payload = jwt.decode(
            token, secret, algorithms=[algorithm], options={"verify_signature": False}
        )
        return payload
    except jwt.InvalidTokenError:
        return None


def is_token_expired(token_payload: Dict) -> bool:
    """
    Check if a token payload indicates the token is expired.

    Args:
        token_payload: Decoded JWT token payload dictionary

    Returns:
        True if token is expired, False otherwise
    """
    exp = token_payload.get("exp")
    if not exp:
        return True  # No expiration claim means invalid/expired

    from time import time

    return exp < int(time())


def get_token_user_id(token_payload: Dict) -> Optional[uuid.UUID]:
    """
    Extract user ID from token payload.

    Args:
        token_payload: Decoded JWT token payload dictionary

    Returns:
        User ID as UUID if present, None otherwise
    """
    user_id_str = token_payload.get("user_id")
    if not user_id_str:
        return None

    try:
        return uuid.UUID(user_id_str)
    except (ValueError, TypeError):
        return None


def get_token_role(token_payload: Dict) -> Optional[str]:
    """
    Extract role from token payload.

    Args:
        token_payload: Decoded JWT token payload dictionary

    Returns:
        User role string if present, None otherwise
    """
    return token_payload.get("role")
