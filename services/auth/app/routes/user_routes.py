"""User management routes"""

import uuid
from datetime import datetime, timezone

from app import db
from app.middleware.auth import (
    get_current_user,
    require_admin,
    require_auth,
    require_service_token,
)
from app.models.user import User
from app.services.password_service import PasswordService
from app.utils.validators import validate_email, validate_password
from flask import Blueprint, current_app, jsonify, request

user_bp = Blueprint("user", __name__)

# Valid roles
VALID_ROLES = {"viewer", "player", "writer", "admin"}


@user_bp.route("/users/<user_id>", methods=["GET"])
@require_auth
def get_user_profile(user_id):
    """
    Get user profile by ID.

    Permissions: Self or Admin
    """
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "Authentication required"}), 401

        # Convert user_id to UUID
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            return jsonify({"error": "Invalid user ID format"}), 400

        # Get user from database
        user = db.session.query(User).filter_by(id=user_uuid).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Check permissions (self or admin)
        current_user_id = current_user.get("user_id")
        current_user_role = current_user.get("role")

        if str(user.id) != current_user_id and current_user_role != "admin":
            return jsonify({"error": "Insufficient permissions"}), 403

        # Return user profile (include email if self or admin)
        include_email = str(user.id) == current_user_id or current_user_role == "admin"
        user_dict = user.to_dict(include_email=include_email)

        return jsonify(user_dict), 200

    except Exception as e:
        current_app.logger.error(f"Get user profile error: {e}")
        return jsonify({"error": "Failed to get user profile"}), 500


@user_bp.route("/users/<user_id>", methods=["PUT"])
@require_auth
def update_user_profile(user_id):
    """
    Update user profile.

    Request body:
    {
        "email": "newemail@example.com",  // Optional
        "password": "newpassword"          // Optional
    }

    Permissions: Self or Admin
    """
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "Authentication required"}), 401

        # Convert user_id to UUID
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            return jsonify({"error": "Invalid user ID format"}), 400

        # Get user from database
        user = db.session.query(User).filter_by(id=user_uuid).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Check permissions (self or admin)
        current_user_id = current_user.get("user_id")
        current_user_role = current_user.get("role")

        if str(user.id) != current_user_id and current_user_role != "admin":
            return jsonify({"error": "Insufficient permissions"}), 403

        # Get request body
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400

        # Update email if provided
        if "email" in data:
            new_email = data.get("email")
            if new_email:
                # Validate email
                is_valid, error = validate_email(new_email)
                if not is_valid:
                    return jsonify({"error": f"Invalid email: {error}"}), 400

                # Check if email is already taken by another user
                existing_email = (
                    db.session.query(User).filter_by(email=new_email).first()
                )
                if existing_email and existing_email.id != user.id:
                    return jsonify({"error": "Email already exists"}), 400

                user.email = new_email

        # Update password if provided
        if "password" in data:
            new_password = data.get("password")
            if new_password:
                # Validate password
                is_valid, error = validate_password(new_password)
                if not is_valid:
                    return jsonify({"error": f"Invalid password: {error}"}), 400

                # Check password history (returns True if password was recently used)
                max_history = current_app.config.get("PASSWORD_HISTORY_COUNT", 3)
                if PasswordService.check_password_history(
                    str(user.id), new_password, max_history
                ):
                    return (
                        jsonify(
                            {"error": f"Cannot reuse last {max_history} passwords"}
                        ),
                        400,
                    )

                # Hash and update password
                password_hash = PasswordService.hash_password(new_password)
                user.password_hash = password_hash
                PasswordService.save_password_history(str(user.id), password_hash)

        # Update timestamp
        user.updated_at = datetime.now(timezone.utc)

        db.session.commit()

        # Return updated user profile
        include_email = str(user.id) == current_user_id or current_user_role == "admin"
        user_dict = user.to_dict(include_email=include_email)

        return jsonify(user_dict), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Update user profile error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to update user profile"}), 500


@user_bp.route("/users/username/<username>", methods=["GET"])
def get_user_by_username(username):
    """
    Get user profile by username (public endpoint).

    Returns limited user information (no email).
    """
    try:
        # Get user from database
        user = db.session.query(User).filter_by(username=username).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Return limited user profile (no email for public endpoint)
        user_dict = user.to_dict(include_email=False)

        return jsonify(user_dict), 200

    except Exception as e:
        current_app.logger.error(f"Get user by username error: {e}")
        return jsonify({"error": "Failed to get user profile"}), 500


@user_bp.route("/users/<user_id>/role", methods=["PUT"])
@require_admin
def update_user_role(user_id):
    """
    Update user role (admin only).

    Request body:
    {
        "role": "writer"  // "viewer", "player", "writer", or "admin"
    }

    Permissions: Admin
    """
    try:
        # Convert user_id to UUID
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            return jsonify({"error": "Invalid user ID format"}), 400

        # Get user from database
        user = db.session.query(User).filter_by(id=user_uuid).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Prevent demoting first user
        if user.is_first_user:
            return jsonify({"error": "Cannot modify first user's role"}), 403

        # Get request body
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400

        new_role = data.get("role")
        if not new_role:
            return jsonify({"error": "Role is required"}), 400

        # Validate role
        if new_role not in VALID_ROLES:
            return (
                jsonify(
                    {"error": f"Invalid role. Must be one of: {', '.join(VALID_ROLES)}"}
                ),
                400,
            )

        # Update role
        user.role = new_role
        user.updated_at = datetime.now(timezone.utc)

        db.session.commit()

        # Return updated user
        user_dict = user.to_dict(include_email=True)
        return jsonify(user_dict), 200

    except Exception as e:
        current_app.logger.error(f"Update user role error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to update user role"}), 500


@user_bp.route("/users", methods=["GET"])
@require_admin
def list_users():
    """
    List all users (admin only).

    Query parameters:
    - role: Filter by role (optional)
    - limit: Number of results (optional, default: 50)
    - offset: Pagination offset (optional, default: 0)

    Permissions: Admin
    """
    try:
        # Get query parameters
        role_filter = request.args.get("role")
        limit = int(request.args.get("limit", 50))
        offset = int(request.args.get("offset", 0))

        # Validate limit
        if limit < 1 or limit > 100:
            limit = 50

        # Build query
        query = db.session.query(User)

        # Apply role filter if provided
        if role_filter:
            if role_filter not in VALID_ROLES:
                return (
                    jsonify(
                        {
                            "error": f"Invalid role filter. Must be one of: {', '.join(VALID_ROLES)}"
                        }
                    ),
                    400,
                )
            query = query.filter_by(role=role_filter)

        # Get total count
        total = query.count()

        # Get paginated results
        users = query.offset(offset).limit(limit).all()

        # Convert to dictionaries (include email for admin)
        users_list = [user.to_dict(include_email=True) for user in users]

        return (
            jsonify(
                {
                    "users": users_list,
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                }
            ),
            200,
        )

    except ValueError as e:
        return jsonify({"error": f"Invalid query parameter: {str(e)}"}), 400
    except Exception as e:
        current_app.logger.error(f"List users error: {e}")
        return jsonify({"error": "Failed to list users"}), 500


@user_bp.route("/users/system", methods=["POST"])
@require_service_token
def create_system_user():
    """
    Create system user (service-to-service endpoint).

    Request body:
    {
        "username": "admin",
        "email": "admin@system",
        "role": "admin"
    }

    Permissions: Service token required
    """
    try:
        # Get request body
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400

        username = data.get("username")
        email = data.get("email")
        role = data.get("role", "admin")

        if not username or not email:
            return jsonify({"error": "Username and email are required"}), 400

        # Validate role
        if role not in VALID_ROLES:
            return (
                jsonify(
                    {"error": f"Invalid role. Must be one of: {', '.join(VALID_ROLES)}"}
                ),
                400,
            )

        # Check if username already exists
        existing_user = db.session.query(User).filter_by(username=username).first()
        if existing_user:
            return jsonify({"error": "Username already exists"}), 400

        # Check if email already exists
        existing_email = db.session.query(User).filter_by(email=email).first()
        if existing_email:
            return jsonify({"error": "Email already exists"}), 400

        # Create system user (no password for system users)
        # Generate a random password hash that will never match
        import bcrypt

        fake_password_hash = bcrypt.hashpw(
            b"system-user-no-password", bcrypt.gensalt()
        ).decode("utf-8")

        user = User(
            username=username,
            email=email,
            password_hash=fake_password_hash,
            role=role,
            is_system_user=True,
            is_first_user=False,
            email_verified=True,  # System users are considered verified
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        db.session.add(user)
        db.session.commit()

        # Return user profile
        user_dict = user.to_dict(include_email=True)
        return jsonify(user_dict), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Create system user error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to create system user"}), 500
