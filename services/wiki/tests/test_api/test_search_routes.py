"""Tests for search and index API endpoints"""

from app import db
from app.models.page import Page
from app.services.search_index_service import SearchIndexService
from tests.test_api.conftest import auth_headers, mock_auth


def test_search_missing_query(client):
    """Test search without query parameter"""
    response = client.get("/api/search")
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
    assert "required" in data["error"].lower()


def test_search_empty_query(client):
    """Test search with empty query"""
    response = client.get("/api/search?q=")
    assert response.status_code == 200
    data = response.get_json()
    assert "results" in data
    assert len(data["results"]) == 0


def test_search_no_results(client, app, test_page):
    """Test search with no matching results"""
    response = client.get("/api/search?q=nonexistentterm12345")
    assert response.status_code == 200
    data = response.get_json()
    assert "results" in data
    assert len(data["results"]) == 0
    assert data["query"] == "nonexistentterm12345"


def test_search_with_results(client, app, test_page, test_user_id):
    """Test search with matching results"""
    with app.app_context():
        # Index the test page
        SearchIndexService.index_page(test_page.id, test_page.content, test_page.title)

    # Search for a term that should match
    response = client.get("/api/search?q=test")
    assert response.status_code == 200
    data = response.get_json()
    assert "results" in data
    assert "total" in data
    assert "query" in data
    assert data["query"] == "test"


def test_search_with_limit(client, app, test_page, test_user_id):
    """Test search with limit parameter"""
    with app.app_context():
        # Index the test page
        SearchIndexService.index_page(test_page.id, test_page.content, test_page.title)

    response = client.get("/api/search?q=test&limit=5")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data["results"]) <= 5


def test_search_section_filter(client, app, test_user_id):
    """Test search with section filter"""
    with app.app_context():
        # Create a page with a section
        page = Page(
            title="Section Page",
            slug="section-page",
            content="# Section Content\n\nThis is in a section.",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing/test-section",
            file_path="section-page.md",
        )
        db.session.add(page)
        db.session.commit()

        # Index the page
        SearchIndexService.index_page(page.id, page.content, page.title)

    # Search with section filter
    response = client.get(
        "/api/search?q=section&section=Regression-Testing/test-section"
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "results" in data
    # Results should only include pages from the specified section
    for result in data["results"]:
        assert result.get("section") == "Regression-Testing/test-section"


def test_search_draft_filtering_viewer(client, app, test_user_id):
    """Test that viewers cannot see drafts in search results"""
    with app.app_context():
        # Create a draft page
        draft_page = Page(
            title="Draft Page",
            slug="draft-page",
            content="# Draft Content",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="draft",
            section="Regression-Testing",
            file_path="draft-page.md",
        )
        db.session.add(draft_page)
        db.session.commit()

        # Index the draft page
        SearchIndexService.index_page(
            draft_page.id, draft_page.content, draft_page.title
        )

    # Search without include_drafts (should exclude drafts)
    response = client.get("/api/search?q=draft")
    assert response.status_code == 200
    data = response.get_json()
    # Draft should not appear in results for viewers
    for result in data["results"]:
        assert result.get("status") != "draft"


def test_search_include_drafts_creator(client, app, test_user_id):
    """Test that creators can see their own drafts when include_drafts=true"""
    with app.app_context():
        # Create a draft page
        draft_page = Page(
            title="My Draft",
            slug="my-draft",
            content="# Draft Content",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="draft",
            section="Regression-Testing",
            file_path="my-draft.md",
        )
        db.session.add(draft_page)
        db.session.commit()

        # Index the draft page
        SearchIndexService.index_page(
            draft_page.id, draft_page.content, draft_page.title
        )

    with mock_auth(test_user_id, "writer"):
        # Search with include_drafts=true
        response = client.get(
            "/api/search?q=draft&include_drafts=true",
            headers=auth_headers(test_user_id, "writer"),
        )
        assert response.status_code == 200
        data = response.get_json()
        # Should be able to see own draft
        draft_found = any(r.get("slug") == "my-draft" for r in data["results"])
        assert draft_found


def test_search_include_drafts_admin(client, app, test_user_id, test_admin_id):
    """Test that admins can see all drafts when include_drafts=true"""
    with app.app_context():
        # Create a draft page by another user
        draft_page = Page(
            title="Other User Draft",
            slug="other-draft",
            content="# Draft Content",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="draft",
            section="Regression-Testing",
            file_path="other-draft.md",
        )
        db.session.add(draft_page)
        db.session.commit()

        # Index the draft page
        SearchIndexService.index_page(
            draft_page.id, draft_page.content, draft_page.title
        )

    with mock_auth(test_admin_id, "admin"):
        # Search with include_drafts=true
        response = client.get(
            "/api/search?q=draft&include_drafts=true",
            headers=auth_headers(test_admin_id, "admin"),
        )
        assert response.status_code == 200
        data = response.get_json()
        # Admin should be able to see all drafts
        draft_found = any(r.get("slug") == "other-draft" for r in data["results"])
        assert draft_found


def test_search_with_pagination(client, app, test_user_id):
    """Test search with pagination (offset and limit)"""
    with app.app_context():
        from app import db
        from app.models.page import Page

        # Create multiple pages for testing
        pages = []
        for i in range(5):
            page = Page(
                title=f"Test Page {i}",
                slug=f"test-page-{i}",
                content=f"Content for page {i} with test term",
                status="published",
                created_by=test_user_id,
                updated_by=test_user_id,
                section="Regression-Testing",
                file_path=f"test-page-{i}.md",
            )
            db.session.add(page)
            pages.append(page)
        db.session.commit()

        # Index pages
        from app.services.search_index_service import SearchIndexService

        for page in pages:
            SearchIndexService.index_page(page.id, page.content, page.title)

    # Test pagination - first page
    response = client.get("/api/search?q=test&limit=2&offset=0")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data["results"]) <= 2
    assert data["total"] >= 5
    assert "limit" in data
    assert "offset" in data
    assert data["limit"] == 2
    assert data["offset"] == 0

    # Test second page
    response = client.get("/api/search?q=test&limit=2&offset=2")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data["results"]) <= 2
    assert "offset" in data
    assert data["offset"] == 2


def test_search_pagination_edge_cases(client, app, test_user_id):
    """Test pagination edge cases"""
    with app.app_context():
        from app import db
        from app.models.page import Page
        from app.services.search_index_service import SearchIndexService

        # Create a few pages
        for i in range(3):
            page = Page(
                title=f"Test Page {i}",
                slug=f"test-page-{i}",
                content=f"Content for page {i} with test term",
                status="published",
                created_by=test_user_id,
                updated_by=test_user_id,
                section="Regression-Testing",
                file_path=f"test-page-{i}.md",
            )
            db.session.add(page)
        db.session.commit()

        # Index pages
        pages = Page.query.filter_by(status="published").all()
        for page in pages:
            SearchIndexService.index_page(page.id, page.content, page.title)

    # Test negative offset (should default to 0)
    response = client.get("/api/search?q=test&limit=10&offset=-5")
    assert response.status_code == 200
    data = response.get_json()
    assert data["offset"] == 0

    # Test offset beyond total results
    response = client.get("/api/search?q=test&limit=10&offset=1000")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data["results"]) == 0
    assert data["offset"] == 1000

    # Test invalid offset (non-numeric)
    response = client.get("/api/search?q=test&limit=10&offset=invalid")
    assert response.status_code == 200
    data = response.get_json()
    assert data["offset"] == 0  # Should default to 0

    # Test zero offset
    response = client.get("/api/search?q=test&limit=10&offset=0")
    assert response.status_code == 200
    data = response.get_json()
    assert data["offset"] == 0
    assert len(data["results"]) >= 0


def test_search_response_structure(client, app, test_page, test_user_id):
    """Test that search response matches API spec structure"""
    with app.app_context():
        # Index the test page
        SearchIndexService.index_page(test_page.id, test_page.content, test_page.title)

    response = client.get("/api/search?q=test")
    assert response.status_code == 200
    data = response.get_json()

    # Check response structure
    assert "results" in data
    assert "total" in data
    assert "query" in data

    if len(data["results"]) > 0:
        result = data["results"][0]
        # Check result structure from API spec
        assert "page_id" in result
        assert "title" in result
        assert "slug" in result
        assert "section" in result
        assert "status" in result
        assert "snippet" in result
        assert "relevance_score" in result
        assert 0 <= result["relevance_score"] <= 1


def test_get_master_index(client, app, test_user_id):
    """Test getting master index"""
    with app.app_context():
        # Create pages with different starting letters
        page_a = Page(
            title="Apple Page",
            slug="apple-page",
            content="# Apple",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            file_path="apple-page.md",
        )
        page_b = Page(
            title="Banana Page",
            slug="banana-page",
            content="# Banana",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            file_path="banana-page.md",
        )
        db.session.add(page_a)
        db.session.add(page_b)
        db.session.commit()

    response = client.get("/api/index")
    assert response.status_code == 200
    data = response.get_json()
    assert "index" in data
    assert isinstance(data["index"], dict)

    # Check that pages are organized by letter
    if "A" in data["index"]:
        assert any(p["title"] == "Apple Page" for p in data["index"]["A"])
    if "B" in data["index"]:
        assert any(p["title"] == "Banana Page" for p in data["index"]["B"])


def test_get_master_index_letter_filter(client, app, test_user_id):
    """Test getting master index filtered by letter"""
    with app.app_context():
        # Create pages with different starting letters
        page_a = Page(
            title="Apple Page",
            slug="apple-page",
            content="# Apple",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            file_path="apple-page.md",
        )
        page_b = Page(
            title="Banana Page",
            slug="banana-page",
            content="# Banana",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            file_path="banana-page.md",
        )
        db.session.add(page_a)
        db.session.add(page_b)
        db.session.commit()

    # Filter by letter 'A'
    response = client.get("/api/index?letter=A")
    assert response.status_code == 200
    data = response.get_json()
    assert "index" in data

    # Should only have 'A' entries
    if "A" in data["index"]:
        assert any(p["title"] == "Apple Page" for p in data["index"]["A"])
    # Should not have 'B' entries
    assert "B" not in data["index"] or len(data["index"].get("B", [])) == 0


def test_get_master_index_section_filter(client, app, test_user_id):
    """Test getting master index filtered by section"""
    with app.app_context():
        # Create pages in different sections
        page1 = Page(
            title="Section A Page",
            slug="section-a-page",
            content="# Content",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            file_path="section-a-page.md",
        )
        page2 = Page(
            title="Section B Page",
            slug="section-b-page",
            content="# Content",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            file_path="section-b-page.md",
        )
        db.session.add(page1)
        db.session.add(page2)
        db.session.commit()

    # Filter by section
    response = client.get("/api/index?section=Regression-Testing")
    assert response.status_code == 200
    data = response.get_json()
    assert "index" in data

    # All results should be from Regression-Testing
    for letter, pages in data["index"].items():
        for page in pages:
            assert page.get("section") == "Regression-Testing"


def test_get_master_index_excludes_drafts(client, app, test_user_id):
    """Test that master index excludes draft pages"""
    with app.app_context():
        # Create a draft page
        draft_page = Page(
            title="Draft Page",
            slug="draft-page",
            content="# Draft",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="draft",
            section="Regression-Testing",
            file_path="draft-page.md",
        )
        db.session.add(draft_page)
        db.session.commit()

    response = client.get("/api/index")
    assert response.status_code == 200
    data = response.get_json()

    # Draft should not appear in index
    for letter, pages in data["index"].items():
        for page in pages:
            assert page.get("slug") != "draft-page"


def test_get_master_index_response_structure(client, app, test_user_id):
    """Test that master index response matches API spec structure"""
    with app.app_context():
        page = Page(
            title="Test Page",
            slug="test-page",
            content="# Test",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            file_path="test-page.md",
        )
        db.session.add(page)
        db.session.commit()

    response = client.get("/api/index")
    assert response.status_code == 200
    data = response.get_json()
    assert "index" in data
    assert isinstance(data["index"], dict)

    # Check structure of entries
    for letter, pages in data["index"].items():
        assert isinstance(letter, str)
        assert len(letter) == 1  # Single letter
        assert isinstance(pages, list)
        for page in pages:
            assert "page_id" in page
            assert "title" in page
            assert "slug" in page
            assert "section" in page
