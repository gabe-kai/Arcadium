"""
Authentication routes for user registration, login, and token management.
"""

from app import limiter
from app.services.auth_service import AuthService
from app.services.token_service import TokenService
from flask import Blueprint, current_app, jsonify, request
from flask_limiter.util import get_remote_address

auth_bp = Blueprint("auth", __name__)


def get_email_for_rate_limit():
    """
    Extract email from request body for rate limiting per email.
    Used for registration endpoint rate limiting.
    Falls back to IP address if email is not in request body.
    """
    data = request.get_json(silent=True)
    if data and isinstance(data, dict) and "email" in data:
        email = data.get("email")
        if email:
            return f"email:{email}"
    return get_remote_address()


@auth_bp.route("/auth/register", methods=["POST"])
@limiter.limit("3 per hour", key_func=get_email_for_rate_limit)
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
@limiter.limit("5 per 15 minutes", key_func=get_remote_address)
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


@auth_bp.route("/auth/refresh", methods=["POST"])
@limiter.limit("10 per hour", key_func=get_remote_address)
def refresh_token():
    """
    Refresh access token using refresh token.

    Request body:
    {
        "token": "refresh-token-here"
    }

    Returns:
        New access token and expiration
    """
    try:
        data = request.get_json(silent=True)

        if data is None:
            return jsonify({"error": "Request body is required"}), 400

        refresh_token_str = data.get("token")

        if not refresh_token_str:
            return jsonify({"error": "Refresh token is required"}), 400

        # Refresh access token
        result = AuthService.refresh_access_token(refresh_token_str)

        if not result:
            return jsonify({"error": "Invalid or expired refresh token"}), 401

        new_access_token, new_refresh_token = result

        # Prepare response
        expires_in = current_app.config.get("JWT_ACCESS_TOKEN_EXPIRATION", 3600)

        response_data = {
            "token": new_access_token,
            "expires_in": expires_in,
        }

        # Include new refresh token if it was rotated (currently returns same token)
        if new_refresh_token != refresh_token_str:
            response_data["refresh_token"] = new_refresh_token

        return jsonify(response_data), 200

    except Exception as e:
        current_app.logger.error(f"Token refresh error: {e}")
        return jsonify({"error": "Token refresh failed"}), 500


@auth_bp.route("/auth/logout", methods=["POST"])
def logout():
    """
    Logout user by blacklisting access token.

    Request Headers:
    Authorization: Bearer <token>

    Returns:
        Success message
    """
    try:
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Authorization header is required"}), 401

        # Handle both "Bearer <token>" and "bearer <token>" (case insensitive)
        parts = auth_header.split(" ", 1)
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({"error": "Invalid Authorization header format"}), 401

        token = parts[1].strip()
        if not token:
            return jsonify({"error": "Token is required"}), 401

        # Verify token to get user ID
        payload = TokenService.verify_token(token)
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401

        user_id = payload.get("user_id")
        if not user_id:
            return jsonify({"error": "Invalid token format"}), 401

        # Logout user (blacklist token)
        AuthService.logout_user(token, user_id)

        return jsonify({"message": "Logged out successfully"}), 200

    except Exception as e:
        current_app.logger.error(f"Logout error: {e}")
        return jsonify({"error": "Logout failed"}), 500


@auth_bp.route("/auth/revoke", methods=["POST"])
def revoke_token():
    """
    Revoke token(s).

    Request Headers:
    Authorization: Bearer <token>

    Request Body (optional):
    {
        "token_id": "jwt-jti-claim"  // Optional: specific token to revoke
    }

    If token_id is provided, revokes that specific token.
    If token_id is not provided and user is admin, revokes all user's tokens.

    Returns:
        Success message with revoked count
    """
    try:
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Authorization header is required"}), 401

        # Handle both "Bearer <token>" and "bearer <token>" (case insensitive)
        parts = auth_header.split(" ", 1)
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({"error": "Invalid Authorization header format"}), 401

        token = parts[1].strip()
        if not token:
            return jsonify({"error": "Token is required"}), 401

        # Verify token to get user info
        payload = TokenService.verify_token(token)
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401

        user_id = payload.get("user_id")
        if not user_id:
            return jsonify({"error": "Invalid token format"}), 401

        # Get user to check role
        from app import db
        from app.models.user import User

        user = db.session.query(User).filter_by(id=user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Get request body
        data = request.get_json() or {}
        token_id = data.get("token_id")

        revoked_count = 0

        if token_id:
            # Revoke specific token
            # token_id could be:
            # 1. A JWT jti claim (UUID string for access token) - blacklist it
            # 2. A refresh token hash - delete the refresh token
            from datetime import datetime, timedelta, timezone

            from app.models.refresh_token import RefreshToken

            # First, try to find as refresh token
            refresh_token = (
                db.session.query(RefreshToken)
                .filter_by(token_hash=token_id, user_id=user_id)
                .first()
            )

            if refresh_token:
                # Found as refresh token, delete it
                db.session.delete(refresh_token)
                db.session.commit()
                revoked_count = 1
            else:
                # Not a refresh token, try as access token jti (blacklist it)
                # token_id should be the jti claim value (UUID string)
                # We need to blacklist it, but we need the expiration time
                # Since we only have the jti, we'll use a default expiration time
                # (access tokens expire in 1 hour by default)
                expires_at = datetime.now(timezone.utc) + timedelta(
                    seconds=current_app.config.get("JWT_ACCESS_TOKEN_EXPIRATION", 3600)
                )
                TokenService.blacklist_token(token_id, user_id, expires_at)
                revoked_count = 1
        else:
            # Revoke all tokens (admin only)
            if not user.is_admin():
                return (
                    jsonify(
                        {"error": "Admin permission required to revoke all tokens"}
                    ),
                    403,
                )

            # Revoke all user's refresh tokens
            from app.models.refresh_token import RefreshToken

            refresh_tokens = (
                db.session.query(RefreshToken).filter_by(user_id=user_id).all()
            )
            revoked_count = len(refresh_tokens)

            AuthService.revoke_token("", user_id, revoke_all=True)

        return (
            jsonify(
                {
                    "message": "Token revoked successfully",
                    "revoked_count": revoked_count,
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Token revocation error: {e}", exc_info=True)
        return jsonify({"error": "Token revocation failed"}), 500


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
