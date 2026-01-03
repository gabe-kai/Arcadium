"""Authentication and authorization middleware decorators"""

from functools import wraps

from app.services.token_service import TokenService
from flask import g, request


def get_user_from_token(token: str):
    """
    Extract user information from JWT token.

    Args:
        token: JWT token string

    Returns:
        Dictionary with user_id, username, role if valid, None otherwise
    """
    payload = TokenService.verify_token(token)
    if not payload:
        return None

    return {
        "user_id": payload.get("user_id"),
        "username": payload.get("username"),
        "role": payload.get("role"),
    }


def get_current_user():
    """
    Get current user from Flask's g object (set by require_auth decorator).

    Returns:
        Dictionary with user_id, username, role, or None if not authenticated
    """
    return getattr(g, "current_user", None)


def require_auth(f):
    """
    Decorator to require authentication for an endpoint.

    Expects Authorization header: Bearer <token>
    Sets g.current_user with user information if valid.

    Returns 401 if token is missing or invalid.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            from flask import jsonify

            return jsonify({"error": "Authorization header is required"}), 401

        # Handle both "Bearer <token>" and "bearer <token>" (case insensitive)
        parts = auth_header.split(" ", 1)
        if len(parts) != 2 or parts[0].lower() != "bearer":
            from flask import jsonify

            return jsonify({"error": "Invalid Authorization header format"}), 401

        token = parts[1].strip()
        if not token:
            from flask import jsonify

            return jsonify({"error": "Token is required"}), 401

        # Verify token and get user info
        user_info = get_user_from_token(token)
        if not user_info:
            from flask import jsonify

            return jsonify({"error": "Invalid or expired token"}), 401

        # Store user info in Flask's g object for use in route handler
        g.current_user = user_info

        return f(*args, **kwargs)

    return decorated_function


def require_role(required_role: str):
    """
    Decorator factory to require a specific role.

    Args:
        required_role: Required role ("viewer", "player", "writer", "admin")

    Usage:
        @require_role("admin")
        def admin_only_endpoint():
            ...
    """
    role_hierarchy = {"viewer": 0, "player": 1, "writer": 2, "admin": 3}

    def decorator(f):
        @wraps(f)
        @require_auth
        def decorated_function(*args, **kwargs):
            current_user = get_current_user()
            if not current_user:
                from flask import jsonify

                return jsonify({"error": "Authentication required"}), 401

            user_role = current_user.get("role")
            user_level = role_hierarchy.get(user_role, 0)
            required_level = role_hierarchy.get(required_role, 0)

            if user_level < required_level:
                from flask import jsonify

                return jsonify({"error": f"{required_role} role required"}), 403

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def require_admin(f):
    """
    Decorator to require admin role.

    Usage:
        @require_admin
        def admin_only_endpoint():
            ...
    """
    return require_role("admin")(f)


def require_service_token(f):
    """
    Decorator to require service token (for service-to-service authentication).

    Expects Authorization header: Service-Token <token>
    Validates service token using TokenService.

    Returns 401 if token is missing or invalid.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            from flask import jsonify

            return jsonify({"error": "Authorization header is required"}), 401

        # Handle "Service-Token <token>" format (case insensitive)
        parts = auth_header.split(" ", 1)
        if len(parts) != 2 or parts[0].lower() != "service-token":
            from flask import jsonify

            return jsonify({"error": "Invalid Authorization header format"}), 401

        token = parts[1].strip()
        if not token:
            from flask import jsonify

            return jsonify({"error": "Service token is required"}), 401

        # Verify service token
        payload = TokenService.verify_token(token)
        if not payload:
            from flask import jsonify

            return jsonify({"error": "Invalid or expired service token"}), 401

        # Check if it's a service token (type should be "service")
        token_type = payload.get("type")
        if token_type != "service":
            from flask import jsonify

            return jsonify({"error": "Service token required"}), 401

        # Store service info in Flask's g object
        g.service_token = {
            "service_id": payload.get("service_id"),
            "service_name": payload.get("service_name"),
        }

        return f(*args, **kwargs)

    return decorated_function
