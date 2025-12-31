"""Tests for page CRUD endpoints"""

import uuid

from app import db
from app.models.page import Page

# Import app and client from parent conftest
# Import API-specific fixtures and helpers
from tests.test_api.conftest import auth_headers, mock_auth


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert data["service"] == "wiki"


def test_list_pages_empty(client):
    """Test listing pages when none exist"""
    response = client.get("/api/pages")
    assert response.status_code == 200
    data = response.get_json()
    assert data["pages"] == []
    assert data["total"] == 0


def test_list_pages_with_page(client, test_page):
    """Test listing pages with existing page"""
    response = client.get("/api/pages")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data["pages"]) >= 1
    # Find our test page
    page_data = next((p for p in data["pages"] if p["slug"] == "test-page"), None)
    assert page_data is not None
    assert page_data["title"] == "Test Page"


def test_list_pages_with_filters(client, test_page):
    """Test listing pages with filters"""
    # Test filtering by section
    response = client.get("/api/pages?section=test")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data["pages"], list)

    # Test pagination
    response = client.get("/api/pages?limit=10&offset=0")
    assert response.status_code == 200
    data = response.get_json()
    assert "limit" in data
    assert "offset" in data


def test_get_page(client, test_page):
    """Test getting a single page"""
    page_id = str(test_page.id)
    response = client.get(f"/api/pages/{page_id}")
    assert response.status_code == 200
    data = response.get_json()
    assert data["title"] == "Test Page"
    assert data["slug"] == "test-page"
    assert "content" in data
    assert "html_content" in data
    assert "table_of_contents" in data
    assert "forward_links" in data
    assert "backlinks" in data


def test_get_page_with_code_blocks(client, test_writer_id):
    """Test that code blocks are properly converted to HTML in page response"""
    with mock_auth(test_writer_id, "writer"):
        # Create a page with code blocks
        content = """# Test Page

Here is some text.

```python
def hello():
    print("Hello")
    return True
```

More text here.
"""
        response = client.post(
            "/api/pages",
            json={
                "title": "Code Block Test",
                "slug": "code-block-test",
                "content": content,
                "status": "published",
            },
            headers=auth_headers(test_writer_id, "writer"),
        )
        assert response.status_code == 201
        page_data = response.get_json()
        page_id = page_data["id"]

        # Get the page and check HTML content
        response = client.get(f"/api/pages/{page_id}")
        assert response.status_code == 200
        data = response.get_json()

        # Check that HTML contains code block
        html_content = data["html_content"]
        assert "<pre><code" in html_content
        assert 'class="language-python"' in html_content
        assert "def hello():" in html_content
        assert 'print("Hello")' in html_content
        assert "return True" in html_content

        # Check that code block is not wrapped in paragraph
        # The code block should be standalone, not inside <p> tags
        pre_index = html_content.find("<pre>")
        if pre_index > 0:
            before_pre = html_content[:pre_index]
            # Should end with </p> or be empty/newline, not have unclosed <p>
            assert (
                before_pre.endswith("</p>")
                or before_pre.strip() == ""
                or before_pre.endswith("\n")
            )


def test_get_page_not_found(client):
    """Test getting a non-existent page"""
    fake_id = str(uuid.uuid4())
    response = client.get(f"/api/pages/{fake_id}")
    assert response.status_code == 404
    data = response.get_json()
    assert "error" in data


def test_get_page_draft_visibility(client, test_draft_page, test_user_id):
    """Test that draft pages are hidden from non-creators"""
    page_id = str(test_draft_page.id)

    # As viewer (no auth), should get 404
    response = client.get(f"/api/pages/{page_id}")
    assert response.status_code == 404

    # As creator, should be able to see it
    with mock_auth(test_user_id, "writer"):
        response = client.get(
            f"/api/pages/{page_id}", headers=auth_headers(test_user_id, "writer")
        )
        assert response.status_code == 200


def test_create_page_requires_auth(client):
    """Test that creating a page requires authentication"""
    response = client.post(
        "/api/pages", json={"title": "New Page", "content": "# Content"}
    )
    assert response.status_code == 401
    data = response.get_json()
    assert "error" in data


def test_create_page_success(client, app, test_writer_id):
    """Test successfully creating a page"""
    with mock_auth(test_writer_id, "writer"):
        response = client.post(
            "/api/pages",
            json={"title": "New Page", "content": "# Content", "status": "published"},
            headers=auth_headers(test_writer_id, "writer"),
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["title"] == "New Page"
        assert "id" in data
        assert "slug" in data


def test_create_page_with_frontmatter(client, app, test_writer_id):
    """Test creating a page with frontmatter (preserved for AI system)"""
    with mock_auth(test_writer_id, "writer"):
        content_with_frontmatter = """---
title: Test Page
slug: test-page
tags: [ai, content]
author: AI Assistant
---
# Content here
"""
        response = client.post(
            "/api/pages",
            json={
                "title": "Test Page",
                "content": content_with_frontmatter,
                "status": "published",
            },
            headers=auth_headers(test_writer_id, "writer"),
        )
        assert response.status_code == 201
        data = response.get_json()
        # Content should be returned with frontmatter preserved
        assert "---" in data["content"]
        assert "tags: [ai, content]" in data["content"] or "tags:" in data["content"]
        assert "author: AI Assistant" in data["content"] or "author:" in data["content"]


def test_update_page_preserves_custom_frontmatter(client, app, test_writer_id):
    """Test that updating a page preserves custom frontmatter fields"""

    # Create a page owned by the test writer
    original_content = """---
title: Test Page
slug: test-page-frontmatter
tags: [ai, content]
author: AI Assistant
---
# Original content
"""
    page = Page(
        title="Test Page",
        slug="test-page-frontmatter",
        content=original_content,
        status="published",
        created_by=test_writer_id,
        updated_by=test_writer_id,
        file_path="test-page-frontmatter.md",
    )
    from app import db

    with app.app_context():
        db.session.add(page)
        db.session.commit()
        page_id = str(page.id)

    with mock_auth(test_writer_id, "writer"):
        # Update page content (frontend would strip frontmatter, then add it back)
        updated_content = """---
title: Updated Title
slug: test-page-frontmatter
tags: [ai, content]
author: AI Assistant
status: published
---
# Updated content
"""
        response = client.put(
            f"/api/pages/{page_id}",
            json={"title": "Updated Title", "content": updated_content},
            headers=auth_headers(test_writer_id, "writer"),
        )
        assert response.status_code == 200
        data = response.get_json()
        # Custom fields should be preserved
        assert "tags:" in data["content"] or "tags: [ai, content]" in data["content"]
        assert "author: AI Assistant" in data["content"] or "author:" in data["content"]


def test_create_page_missing_title(client, test_writer_id):
    """Test creating page without title"""
    with mock_auth(test_writer_id, "writer"):
        response = client.post(
            "/api/pages",
            json={"content": "# Content"},
            headers=auth_headers(test_writer_id, "writer"),
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data


def test_create_page_viewer_forbidden(client, test_user_id):
    """Test that viewers cannot create pages"""
    with mock_auth(test_user_id, "viewer"):
        response = client.post(
            "/api/pages",
            json={"title": "New Page", "content": "# Content"},
            headers=auth_headers(test_user_id, "viewer"),
        )
        assert response.status_code == 403


def test_update_page_requires_auth(client, test_page):
    """Test that updating a page requires authentication"""
    page_id = str(test_page.id)
    response = client.put(f"/api/pages/{page_id}", json={"title": "Updated Title"})
    assert response.status_code == 401


def test_update_page_success(client, app, test_writer_id):
    """Test successfully updating a page"""
    # Create a page owned by the writer
    with app.app_context():
        page = Page(
            title="Page to Update",
            slug="page-to-update",
            content="# Content",
            created_by=test_writer_id,
            updated_by=test_writer_id,
            status="published",
            file_path="page-to-update.md",
        )
        db.session.add(page)
        db.session.commit()
        page_id = str(page.id)

    with mock_auth(test_writer_id, "writer"):
        response = client.put(
            f"/api/pages/{page_id}",
            json={"title": "Updated Title"},
            headers=auth_headers(test_writer_id, "writer"),
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["title"] == "Updated Title"


def test_update_page_wrong_owner(client, app, test_page, test_writer_id, test_user_id):
    """Test that writers cannot update pages they didn't create"""
    # Page is created by test_user_id, but we're trying to update as test_writer_id
    with mock_auth(test_writer_id, "writer"):
        page_id = str(test_page.id)
        response = client.put(
            f"/api/pages/{page_id}",
            json={"title": "Updated Title"},
            headers=auth_headers(test_writer_id, "writer"),
        )
        assert response.status_code == 403


def test_update_page_admin_can_edit_any(client, test_page, test_admin_id):
    """Test that admins can update any page"""
    with mock_auth(test_admin_id, "admin"):
        page_id = str(test_page.id)
        response = client.put(
            f"/api/pages/{page_id}",
            json={"title": "Admin Updated Title"},
            headers=auth_headers(test_admin_id, "admin"),
        )
        assert response.status_code == 200


def test_delete_page_requires_auth(client, test_page):
    """Test that deleting a page requires authentication"""
    page_id = str(test_page.id)
    response = client.delete(f"/api/pages/{page_id}")
    assert response.status_code == 401


def test_delete_page_success(client, app, test_writer_id):
    """Test successfully deleting a page"""
    # Create a page owned by the writer
    with app.app_context():
        page = Page(
            title="Page to Delete",
            slug="page-to-delete",
            content="# Content",
            created_by=test_writer_id,
            updated_by=test_writer_id,
            status="published",
            file_path="page-to-delete.md",
        )
        db.session.add(page)
        db.session.commit()
        page_id = str(page.id)

    with mock_auth(test_writer_id, "writer"):
        response = client.delete(
            f"/api/pages/{page_id}", headers=auth_headers(test_writer_id, "writer")
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "message" in data


def test_delete_page_with_children(client, app, test_writer_id):
    """Test deleting a page with children moves them to orphanage"""
    with app.app_context():
        # Create parent page
        parent = Page(
            title="Parent Page",
            slug="parent-page",
            content="# Parent",
            created_by=test_writer_id,
            updated_by=test_writer_id,
            status="published",
            file_path="parent-page.md",
        )
        db.session.add(parent)
        db.session.flush()

        # Create child page
        child = Page(
            title="Child Page",
            slug="child-page",
            content="# Child",
            created_by=test_writer_id,
            updated_by=test_writer_id,
            status="published",
            parent_id=parent.id,
            file_path="child-page.md",
        )
        db.session.add(child)
        db.session.commit()
        parent_id = str(parent.id)

    with mock_auth(test_writer_id, "writer"):
        response = client.delete(
            f"/api/pages/{parent_id}", headers=auth_headers(test_writer_id, "writer")
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "orphaned_pages" in data
        # Check that we have at least one orphaned page
        # Note: orphaned_count might be 0 if OrphanageService fails silently
        # but orphaned_pages should still be in the response
        assert (
            len(data.get("orphaned_pages", [])) >= 1
        ), f"Expected at least 1 orphaned page, got {data.get('orphaned_count', 0)}. Response: {data}"
        assert data["orphaned_count"] >= 1


def test_get_page_unauthenticated_creates_cache(client, app, test_page):
    """Test that unauthenticated page access creates cache with SYSTEM_USER_ID"""
    from app import db
    from app.models.wiki_config import WikiConfig
    from app.services.cache_service import SYSTEM_USER_ID, CacheService

    page_id = str(test_page.id)

    with app.app_context():
        # Clear any existing cache
        CacheService.invalidate_cache(test_page.content)

        # Make unauthenticated request (no auth headers)
        response = client.get(f"/api/pages/{page_id}")
        assert response.status_code == 200
        data = response.get_json()
        assert data["title"] == test_page.title

        # Verify cache was created with SYSTEM_USER_ID
        cache_key_html = CacheService._generate_cache_key(test_page.content, "html")
        cache_key_toc = CacheService._generate_cache_key(test_page.content, "toc")

        html_config = db.session.query(WikiConfig).filter_by(key=cache_key_html).first()
        toc_config = db.session.query(WikiConfig).filter_by(key=cache_key_toc).first()

        assert html_config is not None, "HTML cache should be created"
        assert (
            html_config.updated_by == SYSTEM_USER_ID
        ), "HTML cache should use SYSTEM_USER_ID"
        assert toc_config is not None, "TOC cache should be created"
        assert (
            toc_config.updated_by == SYSTEM_USER_ID
        ), "TOC cache should use SYSTEM_USER_ID"


def test_cors_headers_present(client, test_page):
    """Test that CORS headers are present in API responses"""
    page_id = str(test_page.id)
    response = client.get(f"/api/pages/{page_id}")

    assert response.status_code == 200

    # Check for CORS headers
    assert "Access-Control-Allow-Origin" in response.headers
    # CORS should allow localhost:3000 (React dev server) - can be http://127.0.0.1:3000 or http://localhost:3000
    origin_header = response.headers.get("Access-Control-Allow-Origin", "")
    assert (
        "localhost:3000" in origin_header
        or "127.0.0.1:3000" in origin_header
        or "*" in origin_header
        or origin_header == "http://localhost:3000"
        or origin_header == "http://127.0.0.1:3000"
    )


def test_archive_page_success(client, app, test_writer_id):
    """Test successfully archiving a page"""
    with app.app_context():
        page = Page(
            title="Page to Archive",
            slug="page-to-archive",
            content="# Content",
            created_by=test_writer_id,
            updated_by=test_writer_id,
            status="published",
            file_path="page-to-archive.md",
        )
        db.session.add(page)
        db.session.commit()
        page_id = str(page.id)

    with mock_auth(test_writer_id, "writer"):
        response = client.post(
            f"/api/pages/{page_id}/archive",
            headers=auth_headers(test_writer_id, "writer"),
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "message" in data
        assert "Page archived successfully" in data["message"]
        assert data["page"]["status"] == "archived"

        # Verify page is archived in database
        with app.app_context():
            archived_page = db.session.get(Page, page_id)
            assert archived_page.status == "archived"


def test_archive_page_requires_auth(client, app, test_page):
    """Test that archiving requires authentication"""
    page_id = str(test_page.id)
    response = client.post(f"/api/pages/{page_id}/archive")
    assert response.status_code == 401


def test_archive_page_insufficient_permissions(
    client, app, test_writer_id, test_user_id
):
    """Test that writers cannot archive pages they didn't create"""
    with app.app_context():
        # Create page by another user
        page = Page(
            title="Other User's Page",
            slug="other-user-page",
            content="# Content",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            file_path="other-user-page.md",
        )
        db.session.add(page)
        db.session.commit()
        page_id = str(page.id)

    with mock_auth(test_writer_id, "writer"):
        response = client.post(
            f"/api/pages/{page_id}/archive",
            headers=auth_headers(test_writer_id, "writer"),
        )
        assert response.status_code == 403
        data = response.get_json()
        assert "Insufficient permissions" in data["error"]


def test_admin_can_archive_any_page(client, app, test_admin_id, test_writer_id):
    """Test that admins can archive any page"""
    with app.app_context():
        page = Page(
            title="Writer's Page",
            slug="writers-page",
            content="# Content",
            created_by=test_writer_id,
            updated_by=test_writer_id,
            status="published",
            file_path="writers-page.md",
        )
        db.session.add(page)
        db.session.commit()
        page_id = str(page.id)

    # Import here to avoid circular import issues
    from tests.test_api.conftest import auth_headers, mock_auth

    with mock_auth(test_admin_id, "admin"):
        response = client.post(
            f"/api/pages/{page_id}/archive",
            headers=auth_headers(test_admin_id, "admin"),
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["page"]["status"] == "archived"


def test_unarchive_page_success(client, app, test_writer_id):
    """Test successfully unarchiving a page"""
    with app.app_context():
        page = Page(
            title="Archived Page",
            slug="archived-page",
            content="# Content",
            created_by=test_writer_id,
            updated_by=test_writer_id,
            status="archived",
            file_path="archived-page.md",
        )
        db.session.add(page)
        db.session.commit()
        page_id = str(page.id)

    with mock_auth(test_writer_id, "writer"):
        response = client.delete(
            f"/api/pages/{page_id}/archive",
            headers=auth_headers(test_writer_id, "writer"),
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "message" in data
        assert "Page unarchived successfully" in data["message"]
        assert data["page"]["status"] == "published"

        # Verify page is unarchived in database
        with app.app_context():
            unarchived_page = db.session.get(Page, page_id)
            assert unarchived_page.status == "published"


def test_archive_already_archived_page(client, app, test_writer_id):
    """Test that archiving an already archived page returns error"""
    with app.app_context():
        page = Page(
            title="Already Archived",
            slug="already-archived",
            content="# Content",
            created_by=test_writer_id,
            updated_by=test_writer_id,
            status="archived",
            file_path="already-archived.md",
        )
        db.session.add(page)
        db.session.commit()
        page_id = str(page.id)

    with mock_auth(test_writer_id, "writer"):
        response = client.post(
            f"/api/pages/{page_id}/archive",
            headers=auth_headers(test_writer_id, "writer"),
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "already archived" in data["error"].lower()


def test_unarchive_not_archived_page(client, app, test_writer_id):
    """Test that unarchiving a non-archived page returns error"""
    with app.app_context():
        page = Page(
            title="Published Page",
            slug="published-page",
            content="# Content",
            created_by=test_writer_id,
            updated_by=test_writer_id,
            status="published",
            file_path="published-page.md",
        )
        db.session.add(page)
        db.session.commit()
        page_id = str(page.id)

    with mock_auth(test_writer_id, "writer"):
        response = client.delete(
            f"/api/pages/{page_id}/archive",
            headers=auth_headers(test_writer_id, "writer"),
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "not archived" in data["error"].lower()


def test_get_page_includes_permission_flags(client, app, test_writer_id):
    """Test that get_page includes can_delete and can_archive flags"""
    with app.app_context():
        page = Page(
            title="Test Page",
            slug="test-page",
            content="# Content",
            created_by=test_writer_id,
            updated_by=test_writer_id,
            status="published",
            file_path="test-page.md",
        )
        db.session.add(page)
        db.session.commit()
        page_id = str(page.id)

    with mock_auth(test_writer_id, "writer"):
        response = client.get(
            f"/api/pages/{page_id}", headers=auth_headers(test_writer_id, "writer")
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "can_delete" in data
        assert "can_archive" in data
        assert data["can_delete"] is True  # Writer can delete own page
        assert data["can_archive"] is True  # Writer can archive own page


def test_archived_page_hidden_from_list(client, app, test_writer_id):
    """Test that archived pages are hidden from list_pages"""
    with app.app_context():
        # Create published and archived pages
        published_page = Page(
            title="Published Page",
            slug="published-page",
            content="# Content",
            created_by=test_writer_id,
            updated_by=test_writer_id,
            status="published",
            file_path="published-page.md",
        )
        archived_page = Page(
            title="Archived Page",
            slug="archived-page",
            content="# Content",
            created_by=test_writer_id,
            updated_by=test_writer_id,
            status="archived",
            file_path="archived-page.md",
        )
        db.session.add(published_page)
        db.session.add(archived_page)
        db.session.commit()

    # List pages (unauthenticated)
    response = client.get("/api/pages")
    assert response.status_code == 200
    data = response.get_json()
    pages = data["pages"]
    slugs = [p["slug"] for p in pages]
    assert "published-page" in slugs
    assert "archived-page" not in slugs  # Archived should be hidden

    # Check for other CORS headers if present
    if "Access-Control-Allow-Methods" in response.headers:
        assert "GET" in response.headers["Access-Control-Allow-Methods"]
    if "Access-Control-Allow-Headers" in response.headers:
        assert (
            "Authorization" in response.headers["Access-Control-Allow-Headers"]
            or "Content-Type" in response.headers["Access-Control-Allow-Headers"]
        )
