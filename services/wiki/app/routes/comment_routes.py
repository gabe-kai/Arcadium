"""Comment endpoints"""

import uuid

from app import db
from app.middleware.auth import optional_auth, require_auth, require_role
from app.models.comment import Comment
from app.models.page import Page
from app.services.comment_service import CommentService
from flask import Blueprint, jsonify, request

comment_bp = Blueprint("comments", __name__)


@comment_bp.route("/pages/<uuid:page_id>/comments", methods=["GET"])
@optional_auth
def get_comments(page_id):
    """
    Get all comments for a page.

    Query Parameters:
    - include_replies: Include nested replies (default: true)

    Permissions: Public (viewer)
    """
    try:
        # Check if page exists
        page = db.session.get(Page, page_id)
        if not page:
            return jsonify({"error": "Page not found"}), 404

        # Get query parameters
        include_replies = request.args.get("include_replies", "true").lower() == "true"

        # Get comments
        comments = CommentService.get_comments(page_id, include_replies=include_replies)

        return jsonify({"comments": comments}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@comment_bp.route("/pages/<uuid:page_id>/comments", methods=["POST"])
@require_auth
@require_role(["player", "writer", "admin"])
def create_comment(page_id):
    """
    Create a new comment or reply.

    Request Body:
    {
        "content": "Comment text",
        "is_recommendation": false,
        "parent_comment_id": "uuid-or-null"
    }

    Permissions: Player, Writer, Admin
    """
    try:
        # Get user ID from request (set by auth middleware)
        user_id = request.user_id

        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body required"}), 400

        content = data.get("content")
        if not content:
            return jsonify({"error": "Content is required"}), 400

        is_recommendation = data.get("is_recommendation", False)
        parent_comment_id_str = data.get("parent_comment_id")

        # Parse parent_comment_id if provided
        parent_comment_id = None
        if parent_comment_id_str:
            try:
                parent_comment_id = uuid.UUID(parent_comment_id_str)
            except ValueError:
                return jsonify({"error": "Invalid parent_comment_id format"}), 400

        # Create comment
        try:
            comment = CommentService.create_comment(
                page_id=page_id,
                user_id=user_id,
                content=content,
                is_recommendation=is_recommendation,
                parent_comment_id=parent_comment_id,
            )
        except ValueError as e:
            error_msg = str(e)
            if "Maximum comment thread depth" in error_msg:
                # Extract depth info for better error response
                return (
                    jsonify(
                        {
                            "error": "Maximum comment thread depth reached",
                            "max_depth": CommentService.MAX_THREAD_DEPTH,
                            "current_depth": CommentService.MAX_THREAD_DEPTH,
                        }
                    ),
                    400,
                )
            return jsonify({"error": error_msg}), 400

        # Return created comment
        return (
            jsonify(
                {
                    "id": str(comment.id),
                    "content": comment.content,
                    "is_recommendation": comment.is_recommendation,
                    "parent_comment_id": (
                        str(comment.parent_comment_id)
                        if comment.parent_comment_id
                        else None
                    ),
                    "thread_depth": comment.thread_depth,
                    "created_at": (
                        comment.created_at.isoformat() if comment.created_at else None
                    ),
                }
            ),
            201,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@comment_bp.route("/comments/<uuid:comment_id>", methods=["PUT"])
@require_auth
def update_comment(comment_id):
    """
    Update a comment.

    Request Body:
    {
        "content": "Updated comment text"
    }

    Permissions: Owner, Admin
    """
    try:
        # Get user ID and role from request
        user_id = request.user_id
        user_role = request.user_role

        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body required"}), 400

        content = data.get("content")
        if not content:
            return jsonify({"error": "Content is required"}), 400

        # Check if comment exists
        comment = db.session.get(Comment, comment_id)
        if not comment:
            return jsonify({"error": "Comment not found"}), 404

        # Check permission: owner or admin
        if comment.user_id != user_id and user_role != "admin":
            return (
                jsonify(
                    {"error": "Insufficient permissions", "required": "Owner or Admin"}
                ),
                403,
            )

        # Update comment
        try:
            updated_comment = CommentService.update_comment(
                comment_id, user_id, content, user_role=user_role
            )
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        # Return updated comment
        return (
            jsonify(
                {
                    "id": str(updated_comment.id),
                    "content": updated_comment.content,
                    "updated_at": (
                        updated_comment.updated_at.isoformat()
                        if updated_comment.updated_at
                        else None
                    ),
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@comment_bp.route("/comments/<uuid:comment_id>", methods=["DELETE"])
@require_auth
def delete_comment(comment_id):
    """
    Delete a comment.

    Permissions: Owner, Admin
    """
    try:
        # Get user ID and role from request
        user_id = request.user_id
        user_role = request.user_role

        # Check if comment exists
        comment = db.session.get(Comment, comment_id)
        if not comment:
            return jsonify({"error": "Comment not found"}), 404

        # Check permission: owner or admin
        if comment.user_id != user_id and user_role != "admin":
            return (
                jsonify(
                    {"error": "Insufficient permissions", "required": "Owner or Admin"}
                ),
                403,
            )

        # Delete comment
        try:
            CommentService.delete_comment(comment_id, user_id, user_role=user_role)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        return jsonify({"message": "Comment deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
