"""Page CRUD endpoints"""

import uuid
from datetime import datetime, timezone

from app import db
from app.middleware.auth import (
    get_current_user,
    optional_auth,
    require_auth,
    require_role,
)
from app.models.page import Page
from app.services.cache_service import CacheService
from app.services.link_service import LinkService
from app.services.page_service import PageService
from app.services.search_index_service import SearchIndexService
from app.utils.markdown_service import markdown_to_html, parse_frontmatter
from app.utils.toc_service import generate_toc
from flask import Blueprint, jsonify, request

page_bp = Blueprint("pages", __name__)


@page_bp.route("/pages", methods=["GET"])
@optional_auth
def list_pages():
    """
    List pages with filtering and pagination.

    Query Parameters:
    - section: Filter by section name
    - parent_id: Filter by parent page ID
    - slug: Filter by exact slug match
    - search: Search term for title/content
    - status: Filter by status (published, draft) - defaults to published for non-creators
    - include_drafts: Include draft pages (only for creator or admin)
    - limit: Number of results (default: 50)
    - offset: Pagination offset
    """
    try:
        # Get query parameters
        section = request.args.get("section")
        parent_id_str = request.args.get("parent_id")
        slug = request.args.get("slug")
        search = request.args.get("search")
        status = request.args.get("status")
        include_drafts = request.args.get("include_drafts", "false").lower() == "true"
        limit = int(request.args.get("limit", 50))
        offset = int(request.args.get("offset", 0))

        # Parse parent_id if provided
        parent_id = None
        if parent_id_str:
            try:
                parent_id = uuid.UUID(parent_id_str)
            except ValueError:
                return jsonify({"error": "Invalid parent_id format"}), 400

        # Get current user info
        current_user = get_current_user()
        user_id = current_user["user_id"] if current_user else None
        user_role = current_user["role"] if current_user else "viewer"

        # Determine if user can see drafts
        can_see_drafts = user_role in ["admin", "writer"] and include_drafts

        # If slug is provided, do a direct lookup (for validation)
        if slug:
            page = Page.query.filter_by(slug=slug).first()
            if not page:
                return (
                    jsonify({"pages": [], "total": 0, "limit": limit, "offset": 0}),
                    200,
                )

            # Check draft and archived visibility
            if page.status == "draft":
                if not can_see_drafts or (
                    user_role == "writer" and page.created_by != user_id
                ):
                    return (
                        jsonify({"pages": [], "total": 0, "limit": limit, "offset": 0}),
                        200,
                    )
            # Exclude archived pages from list (they're hidden)
            if page.status == "archived":
                return (
                    jsonify({"pages": [], "total": 0, "limit": limit, "offset": 0}),
                    200,
                )

            return (
                jsonify(
                    {
                        "pages": [
                            {
                                "id": str(page.id),
                                "title": page.title,
                                "slug": page.slug,
                                "parent_id": (
                                    str(page.parent_id) if page.parent_id else None
                                ),
                                "section": page.section,
                                "order": page.order_index,
                                "status": page.status,
                                "created_at": (
                                    page.created_at.isoformat()
                                    if page.created_at
                                    else None
                                ),
                                "updated_at": (
                                    page.updated_at.isoformat()
                                    if page.updated_at
                                    else None
                                ),
                                "created_by": str(page.created_by),
                                "updated_by": str(page.updated_by),
                            }
                        ],
                        "total": 1,
                        "limit": limit,
                        "offset": 0,
                    }
                ),
                200,
            )

        # If search is provided, use search service
        if search:
            from app.services.search_index_service import SearchIndexService

            results = SearchIndexService.search(
                query=search, section=section, limit=limit, offset=offset
            )

            # Filter results based on draft visibility
            filtered_results = []
            for result in results:
                page = Page.query.get(result["page_id"])
                if not page:
                    continue

                # Check draft visibility
                if page.status == "draft":
                    if not can_see_drafts or (
                        user_role == "writer" and page.created_by != user_id
                    ):
                        continue

                filtered_results.append(
                    {
                        "id": str(page.id),
                        "title": page.title,
                        "slug": page.slug,
                        "parent_id": str(page.parent_id) if page.parent_id else None,
                        "section": page.section,
                        "order": page.order_index,
                        "status": page.status,
                        "created_at": (
                            page.created_at.isoformat() if page.created_at else None
                        ),
                        "updated_at": (
                            page.updated_at.isoformat() if page.updated_at else None
                        ),
                        "created_by": str(page.created_by),
                        "updated_by": str(page.updated_by),
                        "relevance_score": result.get("score", 0),
                    }
                )

            return (
                jsonify(
                    {
                        "pages": filtered_results,
                        "total": len(filtered_results),
                        "limit": limit,
                        "offset": offset,
                    }
                ),
                200,
            )

        # Use PageService to list pages
        # PageService.list_pages handles draft filtering internally
        pages = PageService.list_pages(
            user_role=user_role,
            user_id=user_id,
            parent_id=parent_id,
            section=section,
            status=status,
            include_drafts=can_see_drafts,
        )

        # Apply pagination manually (PageService doesn't handle limit/offset yet)
        total = len(pages)
        pages = pages[offset : offset + limit]

        # Convert to JSON
        pages_data = []
        for page in pages:
            pages_data.append(
                {
                    "id": str(page.id),
                    "title": page.title,
                    "slug": page.slug,
                    "parent_id": str(page.parent_id) if page.parent_id else None,
                    "section": page.section,
                    "order": page.order_index,
                    "status": page.status,
                    "created_at": (
                        page.created_at.isoformat() if page.created_at else None
                    ),
                    "updated_at": (
                        page.updated_at.isoformat() if page.updated_at else None
                    ),
                    "created_by": str(page.created_by),
                    "updated_by": str(page.updated_by),
                }
            )

        # Get total count (for pagination)
        total_query = Page.query
        # Exclude archived pages from normal views
        total_query = total_query.filter(Page.status != "archived")
        if section:
            total_query = total_query.filter_by(section=section)
        if parent_id:
            total_query = total_query.filter_by(parent_id=parent_id)
        if slug:
            total_query = total_query.filter_by(slug=slug)
        if status and not can_see_drafts:
            total_query = total_query.filter_by(status=status)
        elif not can_see_drafts:
            total_query = total_query.filter_by(status="published")

        total = total_query.count()

        return (
            jsonify(
                {"pages": pages_data, "total": total, "limit": limit, "offset": offset}
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@page_bp.route("/pages/<page_id>", methods=["GET"])
@optional_auth
def get_page(page_id):
    """
    Get a single page by ID.

    Returns JSON by default. Add ?format=html to get HTML view.

    Draft pages return 404 for non-creators and non-admins.
    """
    from flask import request

    # Check if HTML format requested
    format_type = request.args.get("format", "json")

    try:
        page_id_uuid = uuid.UUID(page_id)
    except ValueError:
        if format_type == "html":
            return (
                "<html><body><h1>Error</h1><p>Invalid page ID format</p></body></html>",
                400,
            )
        return jsonify({"error": "Invalid page ID format"}), 400

    try:
        page = db.session.get(Page, page_id_uuid)
        if not page:
            if format_type == "html":
                return (
                    "<html><body><h1>Page Not Found</h1><p>The requested page does not exist.</p></body></html>",
                    404,
                )
            return jsonify({"error": "Page not found"}), 404

        # Get current user info
        current_user = get_current_user()
        user_id = current_user["user_id"] if current_user else None
        user_role = current_user["role"] if current_user else "viewer"

        # Check draft visibility
        if page.status == "draft":
            if user_role not in ["admin", "writer"]:
                if format_type == "html":
                    return (
                        "<html><body><h1>Page Not Found</h1><p>The requested page does not exist.</p></body></html>",
                        404,
                    )
                return jsonify({"error": "Page not found"}), 404
            if user_role == "writer" and page.created_by != user_id:
                if format_type == "html":
                    return (
                        "<html><body><h1>Page Not Found</h1><p>The requested page does not exist.</p></body></html>",
                        404,
                    )
                return jsonify({"error": "Page not found"}), 404

        # Check archived visibility (archived pages are hidden from normal views)
        # Only admins and writers (who can archive) can view archived pages
        if page.status == "archived":
            if user_role not in ["admin", "writer"]:
                if format_type == "html":
                    return (
                        "<html><body><h1>Page Not Found</h1><p>The requested page does not exist.</p></body></html>",
                        404,
                    )
                return jsonify({"error": "Page not found"}), 404
            # Writers can only view archived pages they created or can archive
            if user_role == "writer" and not PageService.can_archive(
                page, user_role, user_id
            ):
                if format_type == "html":
                    return (
                        "<html><body><h1>Page Not Found</h1><p>The requested page does not exist.</p></body></html>",
                        404,
                    )
                return jsonify({"error": "Page not found"}), 404

        # Parse frontmatter to get markdown content (frontmatter should not be in HTML or API response)
        # This handles both old pages (with frontmatter) and new pages (without frontmatter)
        _, markdown_content = parse_frontmatter(page.content)

        # Get or generate TOC (with caching) - use markdown content without frontmatter
        toc = CacheService.get_toc_cache(markdown_content)
        if toc is None:
            toc = generate_toc(markdown_content)
            CacheService.set_toc_cache(
                markdown_content, toc, str(user_id) if user_id else None
            )

        # Get or generate HTML (with caching) - use markdown content without frontmatter
        html_content = CacheService.get_html_cache(markdown_content)
        if html_content is None:
            html_content = markdown_to_html(markdown_content)
            CacheService.set_html_cache(
                markdown_content, html_content, str(user_id) if user_id else None
            )

        # If HTML format requested, return styled HTML page
        if format_type == "html":
            from flask import make_response, render_template_string

            # Get forward links (outgoing)
            forward_links = LinkService.get_outgoing_links(page.id)
            forward_links_data = [
                {"page_id": str(link.id), "title": link.title, "slug": link.slug}
                for link in forward_links
            ]

            # Get backlinks (incoming)
            backlinks = LinkService.get_incoming_links(page.id)
            backlinks_data = [
                {"page_id": str(link.id), "title": link.title, "slug": link.slug}
                for link in backlinks
            ]

            # Convert TOC list to HTML with proper nesting
            toc_html = ""
            if toc:
                toc_html = "<ul>"
                current_level = 2  # Start at H2
                for i, entry in enumerate(toc):
                    level = entry["level"]
                    # Close nested lists if we're going back up levels
                    while current_level > level:
                        toc_html += "</ul></li>"
                        current_level -= 1
                    # Close previous list item if we're at the same or deeper level
                    if i > 0 and current_level <= level:
                        toc_html += "</li>"
                    # Open new nested list if we're going deeper
                    if level > current_level:
                        toc_html += "<ul>"
                    # Add the list item
                    toc_html += f'<li><a href="#{entry["anchor"]}">{entry["text"]}</a>'
                    current_level = level
                # Close all remaining lists
                toc_html += "</li>"  # Close last item
                while current_level >= 2:
                    toc_html += "</ul>"
                    current_level -= 1

            html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - Wiki</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: white;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        header {
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            color: #2c3e50;
        }
        .meta {
            color: #666;
            font-size: 0.9em;
            margin-bottom: 20px;
        }
        .content {
            font-size: 1.1em;
            line-height: 1.8;
        }
        .content h2 { margin-top: 30px; margin-bottom: 15px; color: #34495e; }
        .content h3 { margin-top: 25px; margin-bottom: 12px; color: #34495e; }
        .content h4 { margin-top: 20px; margin-bottom: 10px; color: #34495e; }
        .content p { margin-bottom: 15px; }
        .content code {
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }
        .content pre {
            background: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            margin-bottom: 15px;
        }
        .content a {
            color: #3498db;
            text-decoration: none;
        }
        .content a:hover {
            text-decoration: underline;
        }
        .toc {
            background: #f9f9f9;
            border-left: 4px solid #3498db;
            padding: 20px;
            margin: 20px 0;
        }
        .toc h3 {
            margin-top: 0;
            margin-bottom: 15px;
        }
        .toc ul {
            list-style: none;
            padding-left: 20px;
        }
        .toc li {
            margin: 8px 0;
        }
        .toc a {
            color: #3498db;
            text-decoration: none;
        }
        .links {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #e0e0e0;
        }
        .links h3 {
            margin-bottom: 15px;
        }
        .links ul {
            list-style: none;
        }
        .links li {
            margin: 8px 0;
        }
        .links a {
            color: #3498db;
            text-decoration: none;
        }
        .links a:hover {
            text-decoration: underline;
        }
        footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #e0e0e0;
            color: #666;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{{ title }}</h1>
            <div class="meta">
                <span>Last updated: {{ updated_at }}</span>
                {% if word_count %}
                <span> | Words: {{ word_count }}</span>
                {% endif %}
                {% if content_size_kb %}
                <span> | Size: {{ "%.1f"|format(content_size_kb) }} KB</span>
                {% endif %}
            </div>
        </header>

        {% if table_of_contents %}
        <div class="toc">
            <h3>Table of Contents</h3>
            {{ table_of_contents|safe }}
        </div>
        {% endif %}

        <div class="content">
            {{ html_content|safe }}
        </div>

        {% if forward_links or backlinks %}
        <div class="links">
            {% if forward_links %}
            <h3>See Also</h3>
            <ul>
                {% for link in forward_links %}
                <li><a href="/api/pages/{{ link.page_id }}?format=html">{{ link.title }}</a></li>
                {% endfor %}
            </ul>
            {% endif %}

            {% if backlinks %}
            <h3>Pages Linking Here</h3>
            <ul>
                {% for link in backlinks %}
                <li><a href="/api/pages/{{ link.page_id }}?format=html">{{ link.title }}</a></li>
                {% endfor %}
            </ul>
            {% endif %}
        </div>
        {% endif %}

        <footer>
            <p>Wiki Service API | <a href="/api/pages">View as JSON</a> | <a href="/api">API Documentation</a></p>
        </footer>
    </div>
</body>
</html>
            """

            html_output = render_template_string(
                html_template,
                title=page.title,
                html_content=html_content,
                toc_html=toc_html,
                forward_links=forward_links_data,
                backlinks=backlinks_data,
                updated_at=(
                    page.updated_at.strftime("%Y-%m-%d %H:%M:%S")
                    if page.updated_at
                    else "Unknown"
                ),
                word_count=page.word_count,
                content_size_kb=page.content_size_kb,
            )
            response = make_response(html_output, 200)
            response.headers["Content-Type"] = "text/html; charset=utf-8"
            return response

        # JSON response (default)
        # Get forward links (outgoing)
        forward_links = LinkService.get_outgoing_links(page.id)
        forward_links_data = [
            {"page_id": str(link.id), "title": link.title, "slug": link.slug}
            for link in forward_links
        ]

        # Get backlinks (incoming)
        backlinks = LinkService.get_incoming_links(page.id)
        backlinks_data = [
            {"page_id": str(link.id), "title": link.title, "slug": link.slug}
            for link in backlinks
        ]

        # Check if user can edit/delete/archive this page
        can_edit = PageService.can_edit(page, user_role, user_id)
        can_delete = PageService.can_delete(page, user_role, user_id)
        can_archive = PageService.can_archive(page, user_role, user_id)

        # Check for sync conflicts (only for users who can edit)
        sync_conflict = None
        if can_edit:
            sync_conflict = PageService.check_sync_conflict(page)

        # Build response
        # Parse frontmatter for HTML generation, but return full content (with frontmatter) for API
        # Frontend will parse and strip frontmatter for editor display
        response_data = {
            "id": str(page.id),
            "title": page.title,
            "slug": page.slug,
            "content": page.content,  # Return full content with frontmatter (for AI system)
            "html_content": html_content,  # HTML is generated from markdown without frontmatter
            "parent_id": str(page.parent_id) if page.parent_id else None,
            "section": page.section,
            "order": page.order_index,
            "status": page.status,
            "word_count": page.word_count,
            "content_size_kb": page.content_size_kb,
            "table_of_contents": toc,
            "forward_links": forward_links_data,
            "backlinks": backlinks_data,
            "created_at": page.created_at.isoformat() if page.created_at else None,
            "updated_at": page.updated_at.isoformat() if page.updated_at else None,
            "version": page.version,
            "can_edit": can_edit,
            "can_delete": can_delete,
            "can_archive": can_archive,
        }

        # Add sync conflict information if present
        if sync_conflict:
            response_data["sync_conflict"] = sync_conflict

        # Add user info if available (would come from Auth Service in production)
        # For now, just include IDs
        response_data["created_by"] = str(page.created_by)
        response_data["updated_by"] = str(page.updated_by)

        return jsonify(response_data), 200

    except Exception as e:
        if format_type == "html":
            return f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>", 500
        return jsonify({"error": str(e)}), 500


@page_bp.route("/pages", methods=["POST"])
@require_auth
@require_role(["writer", "admin"])
def create_page():
    """
    Create a new page.

    Requires: Writer or Admin role
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body required"}), 400

        # Validate required fields
        title = data.get("title")
        if not title:
            return jsonify({"error": "Title is required"}), 400

        content = data.get("content", "")
        slug = data.get("slug")
        parent_id_str = data.get("parent_id")
        section = data.get("section")
        order = data.get("order")
        status = data.get("status", "published")

        # Validate status
        if status not in ["published", "draft"]:
            return jsonify({"error": 'Status must be "published" or "draft"'}), 400

        # Parse parent_id if provided
        parent_id = None
        if parent_id_str:
            try:
                parent_id = uuid.UUID(parent_id_str)
            except ValueError:
                return jsonify({"error": "Invalid parent_id format"}), 400

        # Get user ID from request (set by require_auth)
        user_id = request.user_id

        # Create page
        try:
            page = PageService.create_page(
                title=title,
                content=content,
                user_id=user_id,
                slug=slug,
                parent_id=parent_id,
                section=section,
                status=status,
                is_public=True,
            )

            # Set order if provided
            if order is not None:
                page.order_index = order
                db.session.commit()

            # Update links
            LinkService.update_page_links(page.id, page.content)

            # Index page for search
            SearchIndexService.index_page(page.id, page.content)

            return (
                jsonify(
                    {
                        "id": str(page.id),
                        "title": page.title,
                        "slug": page.slug,
                        "content": page.content,  # Return content with frontmatter (for AI system)
                        "created_at": (
                            page.created_at.isoformat() if page.created_at else None
                        ),
                    }
                ),
                201,
            )

        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@page_bp.route("/pages/<page_id>", methods=["PUT"])
@require_auth
@require_role(["writer", "admin"])
def update_page(page_id):
    """
    Update an existing page.

    Requires: Writer or Admin role
    Writers can only update their own pages unless they're admins.
    """
    try:
        page_id_uuid = uuid.UUID(page_id)
    except ValueError:
        return jsonify({"error": "Invalid page ID format"}), 400

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body required"}), 400

        # Get user ID and role from request
        user_id = request.user_id
        user_role = request.user_role

        # Check if user can edit this page
        page = db.session.get(Page, page_id_uuid)
        if not page:
            return jsonify({"error": "Page not found"}), 404

        if not PageService.can_edit(page, user_role, user_id):
            return (
                jsonify(
                    {"error": "Insufficient permissions", "required_role": "writer"}
                ),
                403,
            )

        # Extract update fields
        title = data.get("title")
        content = data.get("content")
        slug = data.get("slug")
        parent_id_str = data.get("parent_id")
        section = data.get("section")
        order = data.get("order")
        status = data.get("status")

        # Validate status if provided
        if status and status not in ["published", "draft", "archived"]:
            return (
                jsonify(
                    {"error": 'Status must be "published", "draft", or "archived"'}
                ),
                400,
            )

        # Parse parent_id if provided
        parent_id = None
        if parent_id_str:
            try:
                parent_id = uuid.UUID(parent_id_str)
            except ValueError:
                return jsonify({"error": "Invalid parent_id format"}), 400

        # Track if slug changed (for link updates)
        old_slug = page.slug

        # Update page
        try:
            page = PageService.update_page(
                page_id=page_id_uuid,
                user_id=user_id,
                title=title,
                content=content,
                slug=slug,
                parent_id=parent_id,
                section=section,
                status=status,
            )

            # Set order if provided
            if order is not None:
                page.order_index = order
                db.session.commit()

            # Update links if content changed
            if content is not None:
                # Get old content before update for cache invalidation
                old_content = None
                old_markdown = None
                old_page = db.session.get(Page, page_id_uuid)
                if old_page:
                    old_content = old_page.content
                    # Parse frontmatter to get markdown for cache invalidation
                    _, old_markdown = parse_frontmatter(old_content)

                LinkService.update_page_links(page.id, page.content)
                # Re-index for search
                SearchIndexService.index_page(page.id, page.content)
                # Invalidate cache for both old and new content (using markdown without frontmatter)
                if old_markdown:
                    CacheService.invalidate_cache(old_markdown)
                _, new_markdown = parse_frontmatter(page.content)
                CacheService.invalidate_cache(new_markdown)

            # Handle slug change (update links in other pages)
            if slug and slug != old_slug:
                LinkService.handle_slug_change(old_slug, slug, page.id)

            # Refresh page object to get updated data
            db.session.refresh(page)

            # Check for sync conflicts after update
            sync_conflict = PageService.check_sync_conflict(page)

            response_data = {
                "id": str(page.id),
                "title": page.title,
                "content": page.content,  # Return content with frontmatter (for AI system)
                "updated_at": (
                    page.updated_at.isoformat() if page.updated_at else None
                ),
                "version": page.version,
            }

            # Add sync conflict information if present
            if sync_conflict:
                response_data["sync_conflict"] = sync_conflict

            return jsonify(response_data), 200

        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@page_bp.route("/pages/<page_id>", methods=["DELETE"])
@require_auth
@require_role(["writer", "admin"])
def delete_page(page_id):
    """
    Delete a page.

    Requires: Writer (own pages) or Admin (any page)
    If page has children, they are moved to orphanage.
    """
    try:
        page_id_uuid = uuid.UUID(page_id)
    except ValueError:
        return jsonify({"error": "Invalid page ID format"}), 400

    try:
        # Get user ID and role from request
        user_id = request.user_id
        user_role = request.user_role

        # Check if page exists
        page = db.session.get(Page, page_id_uuid)
        if not page:
            return jsonify({"error": "Page not found"}), 404

        # Check if user can delete this page
        if not PageService.can_delete(page, user_role, user_id):
            return (
                jsonify(
                    {"error": "Insufficient permissions", "required_role": "writer"}
                ),
                403,
            )

        # Delete page (returns info about orphaned children)
        # Note: PageService.delete_page already calls LinkService.handle_page_deletion
        result = PageService.delete_page(page_id_uuid, user_id)

        # Build response
        orphaned_pages_list = result.get("orphaned_pages", [])
        response_data = {
            "message": "Page deleted successfully",
            "orphaned_count": len(orphaned_pages_list),
            "reassign_option": True,
        }

        # Add orphaned pages info (always include, even if empty)
        # orphaned_pages_list contains dicts from PageService.delete_page
        response_data["orphaned_pages"] = [
            {"id": p["id"], "title": p["title"], "moved_to_orphanage": True}
            for p in orphaned_pages_list
        ]

        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@page_bp.route("/pages/<page_id>/archive", methods=["POST"])
@require_auth
@require_role(["writer", "admin"])
def archive_page(page_id):
    """
    Archive a page (set status to 'archived').

    Requires: Writer (own pages) or Admin (any page)
    Archived pages are hidden from normal views but can be restored.
    """
    try:
        page_id_uuid = uuid.UUID(page_id)
    except ValueError:
        return jsonify({"error": "Invalid page ID format"}), 400

    try:
        # Get user ID and role from request
        user_id = request.user_id
        user_role = request.user_role

        # Check if page exists
        page = db.session.get(Page, page_id_uuid)
        if not page:
            return jsonify({"error": "Page not found"}), 404

        # Check if user can archive this page
        if not PageService.can_archive(page, user_role, user_id):
            return (
                jsonify(
                    {"error": "Insufficient permissions", "required_role": "writer"}
                ),
                403,
            )

        # Check if already archived
        if page.status == "archived":
            return jsonify({"error": "Page is already archived"}), 400

        # Archive the page
        page.status = "archived"
        page.updated_by = user_id
        page.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        # Invalidate cache
        _, markdown_content = parse_frontmatter(page.content)
        CacheService.invalidate_cache(markdown_content)

        # Re-index for search (archived pages should be excluded from search)
        SearchIndexService.index_page(page.id, page.content, page.title)

        return (
            jsonify(
                {
                    "message": "Page archived successfully",
                    "page": {
                        "id": str(page.id),
                        "title": page.title,
                        "slug": page.slug,
                        "status": page.status,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@page_bp.route("/pages/<page_id>/archive", methods=["DELETE"])
@require_auth
@require_role(["writer", "admin"])
def unarchive_page(page_id):
    """
    Unarchive a page (restore from archived status).

    Requires: Writer (own pages) or Admin (any page)
    Restores page to 'published' status.
    """
    try:
        page_id_uuid = uuid.UUID(page_id)
    except ValueError:
        return jsonify({"error": "Invalid page ID format"}), 400

    try:
        # Get user ID and role from request
        user_id = request.user_id
        user_role = request.user_role

        # Check if page exists
        page = db.session.get(Page, page_id_uuid)
        if not page:
            return jsonify({"error": "Page not found"}), 404

        # Check if user can archive this page (same permission as archive)
        if not PageService.can_archive(page, user_role, user_id):
            return (
                jsonify(
                    {"error": "Insufficient permissions", "required_role": "writer"}
                ),
                403,
            )

        # Check if not archived
        if page.status != "archived":
            return jsonify({"error": "Page is not archived"}), 400

        # Unarchive the page (restore to published)
        page.status = "published"
        page.updated_by = user_id
        page.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        # Invalidate cache
        _, markdown_content = parse_frontmatter(page.content)
        CacheService.invalidate_cache(markdown_content)

        # Re-index for search
        SearchIndexService.index_page(page.id, page.content, page.title)

        return (
            jsonify(
                {
                    "message": "Page unarchived successfully",
                    "page": {
                        "id": str(page.id),
                        "title": page.title,
                        "slug": page.slug,
                        "status": page.status,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500
