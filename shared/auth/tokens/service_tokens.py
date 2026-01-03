"""
Service token validation utilities for shared use across services.

These utilities provide service token validation functionality for
service-to-service authentication.
"""

from typing import Dict, Optional

from .validation import validate_jwt_token


def validate_service_token(
    token: str, secret: str, algorithm: str = "HS256"
) -> Optional[Dict]:
    """
    Validate a service token (for service-to-service authentication).

    Args:
        token: JWT service token string to validate
        secret: Secret key used to sign the token
        algorithm: JWT algorithm (default: HS256)

    Returns:
        Decoded token payload dictionary if valid, None otherwise
    """
    payload = validate_jwt_token(token, secret, algorithm)
    if not payload:
        return None

    # Verify it's actually a service token
    token_type = payload.get("type")
    if token_type != "service":
        return None

    return payload


def get_service_name(token_payload: Dict) -> Optional[str]:
    """
    Extract service name from service token payload.

    Args:
        token_payload: Decoded service token payload dictionary

    Returns:
        Service name string if present, None otherwise
    """
    return token_payload.get("service_name")


def get_service_id(token_payload: Dict) -> Optional[str]:
    """
    Extract service ID from service token payload.

    Args:
        token_payload: Decoded service token payload dictionary

    Returns:
        Service ID string if present, None otherwise
    """
    return token_payload.get("service_id")


def is_service_token(token_payload: Dict) -> bool:
    """
    Check if a token payload represents a service token.

    Args:
        token_payload: Decoded JWT token payload dictionary

    Returns:
        True if token is a service token, False otherwise
    """
    token_type = token_payload.get("type")
    return token_type == "service"
