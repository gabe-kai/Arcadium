"""Search and index endpoints"""

from app.middleware.auth import optional_auth
from app.services.search_index_service import SearchIndexService
from flask import Blueprint, jsonify, request

search_bp = Blueprint("search", __name__)


@search_bp.route("/search", methods=["GET"])
@optional_auth
def search_pages():
    """
    Search pages by query string.

    Query Parameters:
    - q (required): Search query
    - section (optional): Filter by section
    - include_drafts (optional, default: false): Include draft pages (only for creator or admin)
    - limit (optional): Number of results (default: 20)
    - offset (optional): Pagination offset (default: 0)

    Permissions: Public (viewer) - but drafts filtered by permission
    """
    try:
        # Get query parameter
        query = request.args.get("q")
        if query is None:
            # Missing query parameter is an error
            return jsonify({"error": 'Query parameter "q" is required'}), 400

        query = query.strip()
        if not query:
            # Empty query returns empty results, not an error
            return jsonify({"results": [], "total": 0, "query": ""}), 200

        # Get optional parameters
        section = request.args.get("section")
        include_drafts = request.args.get("include_drafts", "false").lower() == "true"

        # Validate limit parameter
        try:
            limit = int(request.args.get("limit", 20))
            if limit < 0:
                limit = 20  # Use default for negative values
            if limit > 1000:
                limit = 1000  # Cap at reasonable maximum
        except (ValueError, TypeError):
            limit = 20  # Use default for invalid values

        # Validate offset parameter
        try:
            offset = int(request.args.get("offset", 0))
            if offset < 0:
                offset = 0  # Use default for negative values
        except (ValueError, TypeError):
            offset = 0  # Use default for invalid values

        # Get user info from request (set by optional_auth middleware)
        user_role = getattr(request, "user_role", "viewer")
        user_id = getattr(request, "user_id", None)

        # Perform search (get all results for total count, then paginate)
        all_results = SearchIndexService.search(
            query=query,
            limit=10000,  # Get all for total count
            section=section,
            include_drafts=include_drafts,
            user_role=user_role,
            user_id=user_id,
        )

        total = len(all_results)

        # Apply pagination
        paginated_results = all_results[offset : offset + limit]

        return (
            jsonify(
                {
                    "results": paginated_results,
                    "total": total,
                    "query": query,
                    "limit": limit,
                    "offset": offset,
                }
            ),
            200,
        )

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@search_bp.route("/index", methods=["GET"])
@optional_auth
def get_master_index():
    """
    Get master index organized by first letter of page titles.

    Query Parameters:
    - letter (optional): Filter by starting letter
    - section (optional): Filter by section

    Permissions: Public (viewer)
    """
    try:
        # Get optional parameters
        letter = request.args.get("letter")
        section = request.args.get("section")

        # Get master index
        index = SearchIndexService.get_master_index(letter=letter, section=section)

        return jsonify({"index": index}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
