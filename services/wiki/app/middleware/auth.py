"""Authentication and authorization middleware"""

import uuid
from functools import wraps
from typing import Callable, List, Optional

from app.services.auth_service_client import get_auth_client
from flask import jsonify, request


def get_auth_token() -> Optional[str]:
    """
    Extract JWT token from Authorization header.

    Returns:
        Token string if found, None otherwise
    """
    import logging

    logger = logging.getLogger(__name__)

    auth_header = request.headers.get("Authorization", "")
    logger.debug(
        f"Authorization header: {auth_header[:50]}..."
        if len(auth_header) > 50
        else f"Authorization header: {auth_header}"
    )

    if auth_header.startswith("Bearer "):
        token = auth_header[7:]  # Remove 'Bearer ' prefix
        logger.debug(f"Extracted token (first 20 chars): {token[:20]}...")
        return token
    elif auth_header.startswith("bearer "):  # Case-insensitive
        token = auth_header[7:]
        logger.debug(
            f"Extracted token (first 20 chars, lowercase Bearer): {token[:20]}..."
        )
        return token

    logger.warning(
        f"No Bearer token found in Authorization header. Header value: {auth_header[:50] if auth_header else 'None'}"
    )
    return None


def get_user_from_token(token: str) -> Optional[dict]:
    """
    Validate JWT token and extract user information.

    Calls Auth Service /api/auth/verify endpoint to validate token.

    Args:
        token: JWT token string

    Returns:
        Dict with user_id, username, role if valid, None otherwise
    """
    auth_client = get_auth_client()
    return auth_client.verify_token(token)


def require_auth(f: Callable) -> Callable:
    """
    Decorator to require authentication for an endpoint.

    Sets request.user_id and request.user_role if token is valid.
    Returns 401 if token is missing or invalid.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        import logging

        logger = logging.getLogger(__name__)

        token = get_auth_token()
        if not token:
            logger.warning(
                f"Authentication required but no token found. Endpoint: {request.path}, Method: {request.method}"
            )
            return jsonify({"error": "Authentication required"}), 401

        logger.debug(
            f"Verifying token for endpoint: {request.path}, Method: {request.method}, Token prefix: {token[:20]}..."
        )
        user = get_user_from_token(token)
        if not user:
            logger.warning(
                f"Token verification failed for endpoint: {request.path}, Method: {request.method}, Token prefix: {token[:20]}..."
            )
            return jsonify({"error": "Invalid or expired token"}), 401

        logger.debug(
            f"Token verified successfully. User: {user.get('username')}, Role: {user.get('role')}"
        )
        # Attach user info to request object
        request.user_id = uuid.UUID(user["user_id"])
        request.user_role = user["role"]
        request.username = user.get("username", "")

        return f(*args, **kwargs)

    return decorated_function


def require_role(allowed_roles: List[str]):
    """
    Decorator to require specific role(s) for an endpoint.

    Must be used after @require_auth or will return 401.

    Args:
        allowed_roles: List of allowed roles (e.g., ['writer', 'admin'])
    """

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if user is authenticated
            if not hasattr(request, "user_role"):
                return jsonify({"error": "Authentication required"}), 401

            user_role = request.user_role

            # Role hierarchy: admin > writer > player > viewer
            role_hierarchy = {"admin": 4, "writer": 3, "player": 2, "viewer": 1}

            user_level = role_hierarchy.get(user_role, 0)

            # Check if user has one of the allowed roles
            for role in allowed_roles:
                required_level = role_hierarchy.get(role, 0)
                if user_level >= required_level:
                    return f(*args, **kwargs)

            return (
                jsonify(
                    {
                        "error": "Insufficient permissions",
                        "required_role": (
                            allowed_roles[0]
                            if len(allowed_roles) == 1
                            else allowed_roles
                        ),
                    }
                ),
                403,
            )

        return decorated_function

    return decorator


def optional_auth(f: Callable) -> Callable:
    """
    Decorator to optionally authenticate if token is provided.

    Sets request.user_id and request.user_role if token is valid.
    Does not return error if token is missing (for public endpoints).
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_auth_token()
        if token:
            user = get_user_from_token(token)
            if user:
                request.user_id = uuid.UUID(user["user_id"])
                request.user_role = user["role"]
                request.username = user.get("username", "")
            else:
                # Invalid token, but don't fail - treat as unauthenticated
                request.user_id = None
                request.user_role = "viewer"
                request.username = None
        else:
            # No token, treat as viewer
            request.user_id = None
            request.user_role = "viewer"
            request.username = None

        return f(*args, **kwargs)

    return decorated_function


def get_current_user() -> Optional[dict]:
    """
    Get current authenticated user information from request.

    Returns:
        Dict with user_id, role, username if authenticated, None otherwise
    """
    if hasattr(request, "user_id") and request.user_id:
        return {
            "user_id": request.user_id,
            "role": getattr(request, "user_role", "viewer"),
            "username": getattr(request, "username", ""),
        }
    return None
