"""Navigation endpoints"""

import uuid

from app.middleware.auth import optional_auth
from app.services.navigation_service import NavigationService
from flask import Blueprint, jsonify, request

navigation_bp = Blueprint("navigation", __name__)


@navigation_bp.route("/navigation", methods=["GET"])
@optional_auth
def get_navigation():
    """
    Get the full page hierarchy as a navigation tree.

    Permissions: Public (viewer) - but drafts filtered by permission
    """
    try:
        # Get user info from request (set by optional_auth middleware)
        user_role = getattr(request, "user_role", "viewer")
        user_id = getattr(request, "user_id", None)

        # Convert user_id string to UUID if present
        if user_id and isinstance(user_id, str):
            try:
                user_id = uuid.UUID(user_id)
            except ValueError:
                user_id = None

        # Get navigation tree
        tree = NavigationService.get_navigation_tree(
            user_role=user_role, user_id=user_id
        )

        return jsonify({"tree": tree}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@navigation_bp.route("/pages/<uuid:page_id>/breadcrumb", methods=["GET"])
@optional_auth
def get_breadcrumb(page_id):
    """
    Get breadcrumb path from root to the specified page.

    Permissions: Public (viewer)
    """
    try:
        # Get breadcrumb
        breadcrumb = NavigationService.get_breadcrumb(page_id)

        return jsonify({"breadcrumb": breadcrumb}), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@navigation_bp.route("/pages/<uuid:page_id>/navigation", methods=["GET"])
@optional_auth
def get_previous_next(page_id):
    """
    Get previous and next pages in the same parent's children list.

    Permissions: Public (viewer) - but drafts filtered by permission
    """
    try:
        # Get user info from request (set by optional_auth middleware)
        user_role = getattr(request, "user_role", "viewer")
        user_id = getattr(request, "user_id", None)

        # Convert user_id string to UUID if present
        if user_id and isinstance(user_id, str):
            try:
                user_id = uuid.UUID(user_id)
            except ValueError:
                user_id = None

        # Get previous/next
        result = NavigationService.get_previous_next(
            page_id=page_id, user_role=user_role, user_id=user_id
        )

        return jsonify(result), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
