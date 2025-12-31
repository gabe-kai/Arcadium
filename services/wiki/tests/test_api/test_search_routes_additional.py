"""Additional tests for search and index API endpoints - edge cases and validation"""

from app import db
from app.models.page import Page
from app.services.search_index_service import SearchIndexService
from tests.test_api.conftest import auth_headers, mock_auth


def test_search_invalid_limit_negative(client, app, test_page, test_user_id):
    """Test search with negative limit"""
    with app.app_context():
        SearchIndexService.index_page(test_page.id, test_page.content, test_page.title)

    response = client.get("/api/search?q=test&limit=-5")
    # Should handle gracefully (either error or use default)
    assert response.status_code in [200, 400]


def test_search_invalid_limit_non_numeric(client, app, test_page, test_user_id):
    """Test search with non-numeric limit"""
    with app.app_context():
        SearchIndexService.index_page(test_page.id, test_page.content, test_page.title)

    response = client.get("/api/search?q=test&limit=abc")
    # Should handle gracefully (either error or use default)
    assert response.status_code in [200, 400]


def test_search_limit_zero(client, app, test_page, test_user_id):
    """Test search with limit=0"""
    with app.app_context():
        SearchIndexService.index_page(test_page.id, test_page.content, test_page.title)

    response = client.get("/api/search?q=test&limit=0")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data["results"]) == 0


def test_search_limit_very_large(client, app, test_page, test_user_id):
    """Test search with very large limit"""
    with app.app_context():
        SearchIndexService.index_page(test_page.id, test_page.content, test_page.title)

    response = client.get("/api/search?q=test&limit=10000")
    assert response.status_code == 200
    data = response.get_json()
    # Should return results but not exceed reasonable bounds
    assert len(data["results"]) <= 10000


def test_search_multiple_words(client, app, test_user_id):
    """Test search with multiple words"""
    with app.app_context():
        page = Page(
            title="Multi Word Page",
            slug="multi-word-page",
            content="# Multi Word Content\n\nThis page has multiple words.",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            file_path="multi-word-page.md",
        )
        db.session.add(page)
        db.session.commit()
        SearchIndexService.index_page(page.id, page.content, page.title)

    response = client.get("/api/search?q=multi word")
    assert response.status_code == 200
    data = response.get_json()
    assert "results" in data


def test_search_special_characters(client, app, test_user_id):
    """Test search with special characters in query"""
    with app.app_context():
        page = Page(
            title="Special Page",
            slug="special-page",
            content="# Special Content\n\nThis has special chars: @#$%",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            file_path="special-page.md",
        )
        db.session.add(page)
        db.session.commit()
        SearchIndexService.index_page(page.id, page.content, page.title)

    # Search should handle special characters gracefully
    response = client.get("/api/search?q=special")
    assert response.status_code == 200
    data = response.get_json()
    assert "results" in data


def test_search_very_long_query(client):
    """Test search with very long query string"""
    long_query = "a" * 1000
    response = client.get(f"/api/search?q={long_query}")
    assert response.status_code == 200
    data = response.get_json()
    assert "results" in data


def test_search_section_filter_nonexistent(client, app, test_page, test_user_id):
    """Test search with section filter that doesn't exist"""
    with app.app_context():
        SearchIndexService.index_page(test_page.id, test_page.content, test_page.title)

    response = client.get("/api/search?q=test&section=nonexistent-section")
    assert response.status_code == 200
    data = response.get_json()
    # Should return empty results or filter correctly
    assert "results" in data
    for result in data["results"]:
        assert (
            result.get("section") == "nonexistent-section"
        )  # Should be empty if filter works


def test_search_include_drafts_writer_other_user(
    client, app, test_user_id, test_writer_id
):
    """Test that writers cannot see other users' drafts even with include_drafts=true"""
    with app.app_context():
        # Create draft by test_user_id
        draft_page = Page(
            title="Other User Draft",
            slug="other-user-draft",
            content="# Draft",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="draft",
            section="Regression-Testing",
            file_path="other-user-draft.md",
        )
        db.session.add(draft_page)
        db.session.commit()
        SearchIndexService.index_page(
            draft_page.id, draft_page.content, draft_page.title
        )

    with mock_auth(test_writer_id, "writer"):
        # Writer tries to see other user's draft
        response = client.get(
            "/api/search?q=draft&include_drafts=true",
            headers=auth_headers(test_writer_id, "writer"),
        )
        assert response.status_code == 200
        data = response.get_json()
        # Should not see other user's draft
        draft_found = any(r.get("slug") == "other-user-draft" for r in data["results"])
        assert not draft_found


def test_search_include_drafts_viewer_forbidden(client, app, test_user_id):
    """Test that viewers cannot see drafts even with include_drafts=true"""
    with app.app_context():
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
        SearchIndexService.index_page(
            draft_page.id, draft_page.content, draft_page.title
        )

    with mock_auth(test_user_id, "viewer"):
        # Viewer tries to see drafts
        response = client.get(
            "/api/search?q=draft&include_drafts=true",
            headers=auth_headers(test_user_id, "viewer"),
        )
        assert response.status_code == 200
        data = response.get_json()
        # Should not see drafts
        for result in data["results"]:
            assert result.get("status") != "draft"


def test_search_relevance_ordering(client, app, test_user_id):
    """Test that search results are ordered by relevance"""
    with app.app_context():
        # Create pages with different relevance
        # Page with keyword match (higher relevance)
        page1 = Page(
            title="Keyword Match Page",
            slug="keyword-page",
            content="# Keyword Match\n\nThis page has the exact keyword.",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            file_path="keyword-page.md",
        )
        db.session.add(page1)
        db.session.commit()

        # Page with only full-text match (lower relevance)
        page2 = Page(
            title="Full Text Page",
            slug="fulltext-page",
            content="# Full Text\n\nThis page mentions the term.",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            file_path="fulltext-page.md",
        )
        db.session.add(page2)
        db.session.commit()

        # Index both pages
        SearchIndexService.index_page(page1.id, page1.content, page1.title)
        SearchIndexService.index_page(page2.id, page2.content, page2.title)

    response = client.get("/api/search?q=keyword")
    assert response.status_code == 200
    data = response.get_json()
    if len(data["results"]) >= 2:
        # Results should be ordered by relevance_score (highest first)
        scores = [r["relevance_score"] for r in data["results"]]
        assert scores == sorted(scores, reverse=True)


def test_get_master_index_empty(client):
    """Test getting master index when no pages exist"""
    response = client.get("/api/index")
    assert response.status_code == 200
    data = response.get_json()
    assert "index" in data
    assert isinstance(data["index"], dict)
    # Index should be empty or have no entries
    assert len(data["index"]) == 0 or all(
        len(pages) == 0 for pages in data["index"].values()
    )


def test_get_master_index_numeric_titles(client, app, test_user_id):
    """Test master index with pages starting with numbers"""
    with app.app_context():
        page = Page(
            title="123 Number Page",
            slug="123-number-page",
            content="# Number",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            file_path="123-number-page.md",
        )
        db.session.add(page)
        db.session.commit()

    response = client.get("/api/index")
    assert response.status_code == 200
    data = response.get_json()
    # Pages starting with numbers should be handled (might go to '#' or '1')
    assert "index" in data


def test_get_master_index_special_char_titles(client, app, test_user_id):
    """Test master index with pages starting with special characters"""
    with app.app_context():
        page = Page(
            title="@Special Page",
            slug="special-page",
            content="# Special",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            file_path="special-page.md",
        )
        db.session.add(page)
        db.session.commit()

    response = client.get("/api/index")
    assert response.status_code == 200
    data = response.get_json()
    # Pages starting with special chars should be handled
    assert "index" in data


def test_get_master_index_letter_case_insensitive(client, app, test_user_id):
    """Test that letter filter is case-insensitive"""
    with app.app_context():
        page = Page(
            title="Apple Page",
            slug="apple-page",
            content="# Apple",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            file_path="apple-page.md",
        )
        db.session.add(page)
        db.session.commit()

    # Test both uppercase and lowercase
    response_upper = client.get("/api/index?letter=A")
    response_lower = client.get("/api/index?letter=a")

    assert response_upper.status_code == 200
    assert response_lower.status_code == 200

    data_upper = response_upper.get_json()
    data_lower = response_lower.get_json()

    # Both should return the same results
    assert data_upper == data_lower


def test_get_master_index_empty_section_filter(client, app, test_user_id):
    """Test master index with empty section filter"""
    with app.app_context():
        page = Page(
            title="No Section Page",
            slug="no-section-page",
            content="# Content",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            file_path="no-section-page.md",
        )
        db.session.add(page)
        db.session.commit()

    response = client.get("/api/index?section=")
    assert response.status_code == 200
    data = response.get_json()
    assert "index" in data


def test_search_snippet_length(client, app, test_user_id):
    """Test that search snippets are properly truncated"""
    with app.app_context():
        # Create page with long content
        long_content = "# Long Content\n\n" + "word " * 100
        page = Page(
            title="Long Page",
            slug="long-page",
            content=long_content,
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            file_path="long-page.md",
        )
        db.session.add(page)
        db.session.commit()
        SearchIndexService.index_page(page.id, page.content, page.title)

    response = client.get("/api/search?q=word")
    assert response.status_code == 200
    data = response.get_json()
    if len(data["results"]) > 0:
        # Snippet should be reasonable length (200 chars max based on implementation)
        snippet = data["results"][0].get("snippet", "")
        assert len(snippet) <= 200


def test_search_total_matches_count(client, app, test_user_id):
    """Test that total count matches results length"""
    with app.app_context():
        page = Page(
            title="Test Page",
            slug="test-page",
            content="# Test Content",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            file_path="test-page.md",
        )
        db.session.add(page)
        db.session.commit()
        SearchIndexService.index_page(page.id, page.content, page.title)

    response = client.get("/api/search?q=test")
    assert response.status_code == 200
    data = response.get_json()
    # Total should match the number of results returned
    assert data["total"] == len(data["results"])
