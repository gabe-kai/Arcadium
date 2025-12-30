"""
Authentication routes for user registration, login, and token management.
"""

from app.services.auth_service import AuthService
from app.services.token_service import TokenService
from flask import Blueprint, current_app, jsonify, request

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/auth/register", methods=["POST"])
def register():
    """
    Register a new user.

    First user becomes admin, subsequent users are players.

    Request body:
    {
        "username": "newuser",
        "email": "user@example.com",
        "password": "SecurePass123"
    }

    Returns:
        User info and tokens
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Request body is required"}), 400

        username = data.get("username")
        email = data.get("email")
        password = data.get("password")

        if not username or not email or not password:
            return jsonify({"error": "Username, email, and password are required"}), 400

        # Register user
        user, is_first_user = AuthService.register_user(username, email, password)

        # Generate tokens
        access_token = TokenService.generate_access_token(user)
        refresh_token_str = TokenService.generate_refresh_token(user)

        # Store refresh token
        from datetime import datetime, timedelta, timezone

        from app.models.refresh_token import RefreshToken

        expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=current_app.config.get("JWT_REFRESH_TOKEN_EXPIRATION", 604800)
        )

        refresh_token = RefreshToken(
            user_id=user.id,
            token_hash=refresh_token_str,
            expires_at=expires_at,
            created_at=datetime.now(timezone.utc),
            last_used_at=datetime.now(timezone.utc),
        )

        from app import db

        db.session.add(refresh_token)
        db.session.commit()

        # Prepare response
        expires_in = current_app.config.get("JWT_ACCESS_TOKEN_EXPIRATION", 3600)

        return (
            jsonify(
                {
                    "user": {
                        "id": str(user.id),
                        "username": user.username,
                        "email": user.email,
                        "role": user.role,
                        "is_first_user": is_first_user,
                        "email_verified": user.email_verified,
                    },
                    "token": access_token,
                    "refresh_token": refresh_token_str,
                    "expires_in": expires_in,
                    "requires_email_verification": False,  # Email verification not implemented yet
                }
            ),
            201,
        )

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Registration error: {e}")
        return jsonify({"error": "Registration failed"}), 500


@auth_bp.route("/auth/login", methods=["POST"])
def login():
    """
    Login user and get tokens.

    Request body:
    {
        "username": "username",
        "password": "password"
    }

    Returns:
        User info and tokens
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Request body is required"}), 400

        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400

        # Login user
        result = AuthService.login_user(username, password)

        if not result:
            return jsonify({"error": "Invalid username or password"}), 401

        user, access_token, refresh_token_str = result

        # Prepare response
        expires_in = current_app.config.get("JWT_ACCESS_TOKEN_EXPIRATION", 3600)

        return (
            jsonify(
                {
                    "user": {
                        "id": str(user.id),
                        "username": user.username,
                        "email": user.email,
                        "role": user.role,
                    },
                    "token": access_token,
                    "refresh_token": refresh_token_str,
                    "expires_in": expires_in,
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Login error: {e}")
        return jsonify({"error": "Login failed"}), 500


@auth_bp.route("/auth/verify", methods=["POST"])
def verify_token():
    """
    Verify authentication token.

    Request body:
    {
        "token": "jwt-token"
    }

    Or Authorization header:
    Authorization: Bearer <token>

    Returns:
        Token validity and user info
    """
    try:
        token = None

        # Try to get token from request body first
        if request.is_json or (
            request.content_type and "application/json" in request.content_type
        ):
            try:
                data = request.get_json(silent=True)
                if data and isinstance(data, dict):
                    token = data.get("token")
            except Exception:
                pass  # Ignore JSON parsing errors

        # If not in body, try Authorization header
        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header:
                # Handle both "Bearer <token>" and "bearer <token>" (case insensitive)
                parts = auth_header.split(" ", 1)
                if len(parts) == 2 and parts[0].lower() == "bearer":
                    token = parts[1].strip()

        if not token:
            return jsonify({"error": "Token is required"}), 400

        # Verify token
        user_info = AuthService.verify_user_token(token)

        if not user_info:
            return jsonify({"valid": False, "error": "Invalid or expired token"}), 401

        return (
            jsonify(
                {
                    "valid": True,
                    "user": {
                        "id": user_info["user_id"],
                        "username": user_info["username"],
                        "role": user_info["role"],
                    },
                    "expires_at": user_info["expires_at"],
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Token verification error: {e}", exc_info=True)
        import traceback

        current_app.logger.error(traceback.format_exc())
        return (
            jsonify({"valid": False, "error": f"Token verification failed: {str(e)}"}),
            500,
        )


@auth_bp.route("/logs", methods=["GET"])
# Temporarily removed auth requirements to focus on core functionality
# @require_auth
# @require_role(["admin"])
def get_logs():
    """Get recent log entries for the auth service.

    Permissions: Admin (temporarily disabled for development)

    Query parameters:
        limit: Maximum number of log entries to return (default: 100, max: 500)
        level: Filter by log level (ERROR, WARNING, INFO, DEBUG)
    """
    try:
        from app.utils.log_handler import get_log_handler

        # Get query parameters
        limit = min(int(request.args.get("limit", 100)), 500)
        level = request.args.get("level", None)

        # Get recent logs
        log_handler = get_log_handler()
        logs = log_handler.get_recent_logs(limit=limit, level=level)

        return (
            jsonify(
                {
                    "logs": logs,
                    "count": len(logs),
                    "total_available": len(log_handler.logs),
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
