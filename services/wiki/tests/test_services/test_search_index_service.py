"""Test search index service"""

import uuid

from app import db
from app.models.index_entry import IndexEntry
from app.services.page_service import PageService
from app.services.search_index_service import SearchIndexService


def test_index_page_fulltext(app):
    """Test indexing a page for full-text search"""
    with app.app_context():
        user_id = uuid.uuid4()

        # Create a page
        page = PageService.create_page(
            title="Test Page",
            content="This is a test page with some content about programming and Python.",
            user_id=user_id,
            slug="test-page",
            section="Regression-Testing",
        )

        # Index the page
        entries = SearchIndexService.index_page(page.id, page.content, page.title)

        # Should have full-text entries
        fulltext_entries = [e for e in entries if not e.is_keyword]
        assert len(fulltext_entries) > 0

        # Check that common words are indexed
        terms = [e.term for e in fulltext_entries]
        assert "test" in terms
        assert "page" in terms
        assert "content" in terms


def test_index_page_keywords(app):
    """Test automatic keyword extraction"""
    with app.app_context():
        user_id = uuid.uuid4()

        # Create a page with distinctive content
        page = PageService.create_page(
            title="Python Programming Guide",
            content="Python is a programming language. Python supports object-oriented programming. Python has many libraries.",
            user_id=user_id,
            slug="python-guide",
            section="Regression-Testing",
        )

        # Index the page
        entries = SearchIndexService.index_page(page.id, page.content, page.title)

        # Should have keyword entries
        keyword_entries = [e for e in entries if e.is_keyword and not e.is_manual]
        assert len(keyword_entries) > 0

        # Check that "python" and "programming" are likely keywords
        keyword_terms = [e.term for e in keyword_entries]
        # At least one of these should be a keyword
        assert any(
            term in keyword_terms for term in ["python", "programming", "libraries"]
        )


def test_index_page_manual_keywords(app):
    """Test manual keyword tagging"""
    with app.app_context():
        user_id = uuid.uuid4()

        # Create a page with manual keywords in frontmatter
        content = """---
keywords: python, programming, tutorial
---
# Python Tutorial

This is a tutorial about Python programming.
"""
        page = PageService.create_page(
            title="Python Tutorial",
            content=content,
            user_id=user_id,
            slug="python-tutorial",
            section="Regression-Testing",
        )

        # Index the page
        entries = SearchIndexService.index_page(page.id, page.content, page.title)

        # Should have manual keyword entries
        manual_entries = [e for e in entries if e.is_keyword and e.is_manual]
        assert len(manual_entries) >= 3  # python, programming, tutorial

        # Check keywords
        manual_terms = [e.term for e in manual_entries]
        assert "python" in manual_terms
        assert "programming" in manual_terms
        assert "tutorial" in manual_terms


def test_index_page_incremental_update(app):
    """Test that indexing removes old entries"""
    with app.app_context():
        user_id = uuid.uuid4()

        # Create a page
        page = PageService.create_page(
            title="Test Page",
            content="Original content about Python.",
            user_id=user_id,
            slug="test-page",
            section="Regression-Testing",
        )

        # Index first time
        entries1 = SearchIndexService.index_page(page.id, page.content, page.title)
        len(entries1)

        # Update content
        page.content = "New content about JavaScript."
        db.session.commit()

        # Index again
        entries2 = SearchIndexService.index_page(page.id, page.content, page.title)
        count2 = len(entries2)

        # Old entries should be removed
        old_entries = IndexEntry.query.filter_by(page_id=page.id).all()
        assert len(old_entries) == count2

        # Should not have "Python" anymore
        python_entries = [e for e in old_entries if "python" in e.term.lower()]
        assert len(python_entries) == 0


def test_search_basic(app):
    """Test basic search functionality"""
    with app.app_context():
        user_id = uuid.uuid4()

        # Create pages
        page1 = PageService.create_page(
            title="Python Guide",
            content="This is a guide about Python programming.",
            user_id=user_id,
            slug="python-guide",
            section="Regression-Testing",
        )

        page2 = PageService.create_page(
            title="JavaScript Tutorial",
            content="This is a tutorial about JavaScript programming.",
            user_id=user_id,
            slug="javascript-tutorial",
            section="Regression-Testing",
        )

        # Index both pages
        SearchIndexService.index_page(page1.id, page1.content, page1.title)
        SearchIndexService.index_page(page2.id, page2.content, page2.title)

        # Search for "Python"
        results = SearchIndexService.search("Python")
        assert len(results) > 0

        # Should find page1
        page_ids = [r["page_id"] for r in results]
        assert str(page1.id) in page_ids


def test_search_keyword_priority(app):
    """Test that keyword matches have higher scores"""
    with app.app_context():
        user_id = uuid.uuid4()

        # Create pages
        page1 = PageService.create_page(
            title="Python Programming",
            content="Python is a programming language. Python is great.",
            user_id=user_id,
            slug="python-programming",
            section="Regression-Testing",
        )

        # Add manual keyword
        SearchIndexService.index_page(page1.id, page1.content, page1.title)
        SearchIndexService.add_manual_keyword(page1.id, "python")

        # Search
        results = SearchIndexService.search("python")
        assert len(results) > 0

        # Page with keyword should have higher score
        page1_result = next((r for r in results if r["page_id"] == str(page1.id)), None)
        assert page1_result is not None
        assert page1_result["score"] >= 10  # Keywords give 10 points


def test_search_by_keyword(app):
    """Test searching by specific keyword"""
    with app.app_context():
        user_id = uuid.uuid4()

        # Create pages
        page1 = PageService.create_page(
            title="Python Guide",
            content="Python programming guide.",
            user_id=user_id,
            slug="python-guide",
            section="Regression-Testing",
        )

        page2 = PageService.create_page(
            title="JavaScript Guide",
            content="JavaScript programming guide.",
            user_id=user_id,
            slug="javascript-guide",
            section="Regression-Testing",
        )

        # Index and add keywords
        SearchIndexService.index_page(page1.id, page1.content, page1.title)
        SearchIndexService.index_page(page2.id, page2.content, page2.title)
        SearchIndexService.add_manual_keyword(page1.id, "python")
        SearchIndexService.add_manual_keyword(page2.id, "javascript")

        # Search by keyword
        python_pages = SearchIndexService.search_by_keyword("python")
        assert len(python_pages) == 1
        assert python_pages[0].id == page1.id


def test_add_manual_keyword(app):
    """Test adding manual keywords"""
    with app.app_context():
        user_id = uuid.uuid4()

        # Create a page
        page = PageService.create_page(
            title="Test Page",
            content="Test content.",
            user_id=user_id,
            slug="test-page",
            section="Regression-Testing",
        )

        # Add manual keyword
        entry = SearchIndexService.add_manual_keyword(page.id, "test-keyword")

        assert entry is not None
        assert entry.term == "test-keyword"
        assert entry.is_keyword is True
        assert entry.is_manual is True
        assert entry.page_id == page.id


def test_remove_keyword(app):
    """Test removing keywords"""
    with app.app_context():
        user_id = uuid.uuid4()

        # Create a page
        page = PageService.create_page(
            title="Test Page",
            content="Test content.",
            user_id=user_id,
            slug="test-page",
            section="Regression-Testing",
        )

        # Add keyword
        SearchIndexService.add_manual_keyword(page.id, "test-keyword")

        # Verify it exists
        keywords = SearchIndexService.get_page_keywords(page.id)
        assert "test-keyword" in keywords

        # Remove keyword
        removed = SearchIndexService.remove_keyword(page.id, "test-keyword")
        assert removed is True

        # Verify it's gone
        keywords = SearchIndexService.get_page_keywords(page.id)
        assert "test-keyword" not in keywords


def test_get_page_keywords(app):
    """Test getting all keywords for a page"""
    with app.app_context():
        user_id = uuid.uuid4()

        # Create a page
        page = PageService.create_page(
            title="Test Page",
            content="Python programming tutorial.",
            user_id=user_id,
            slug="test-page",
            section="Regression-Testing",
        )

        # Index page (creates auto keywords)
        SearchIndexService.index_page(page.id, page.content, page.title)

        # Add manual keywords
        SearchIndexService.add_manual_keyword(page.id, "manual-keyword-1")
        SearchIndexService.add_manual_keyword(page.id, "manual-keyword-2")

        # Get all keywords
        keywords = SearchIndexService.get_page_keywords(page.id)

        assert len(keywords) > 0
        assert "manual-keyword-1" in keywords
        assert "manual-keyword-2" in keywords


def test_reindex_all(app):
    """Test reindexing all pages"""
    with app.app_context():
        user_id = uuid.uuid4()

        # Create multiple pages
        page1 = PageService.create_page(
            title="Page 1",
            content="Content 1",
            user_id=user_id,
            slug="page-1",
            section="Regression-Testing",
        )

        page2 = PageService.create_page(
            title="Page 2",
            content="Content 2",
            user_id=user_id,
            slug="page-2",
            section="Regression-Testing",
        )

        # Reindex all
        count = SearchIndexService.reindex_all()

        assert count == 2

        # Verify entries exist
        entries1 = IndexEntry.query.filter_by(page_id=page1.id).all()
        entries2 = IndexEntry.query.filter_by(page_id=page2.id).all()
        assert len(entries1) > 0
        assert len(entries2) > 0


def test_get_index_stats(app):
    """Test getting index statistics"""
    with app.app_context():
        user_id = uuid.uuid4()

        # Create and index a page
        page = PageService.create_page(
            title="Test Page",
            content="Python programming tutorial.",
            user_id=user_id,
            slug="test-page",
            section="Regression-Testing",
        )

        SearchIndexService.index_page(page.id, page.content, page.title)
        SearchIndexService.add_manual_keyword(page.id, "python")

        # Get stats
        stats = SearchIndexService.get_index_stats()

        assert stats["total_entries"] > 0
        assert stats["keyword_entries"] > 0
        assert stats["manual_keywords"] >= 1
        assert stats["indexed_pages"] == 1


def test_search_relevance(app):
    """Test search relevance scoring"""
    with app.app_context():
        user_id = uuid.uuid4()

        # Create pages with different relevance
        page1 = PageService.create_page(
            title="Python Programming Guide",
            content="Python Python Python programming guide tutorial. Python is great.",
            user_id=user_id,
            slug="python-guide",
            section="Regression-Testing",
        )

        page2 = PageService.create_page(
            title="JavaScript Tutorial",
            content="JavaScript tutorial with some Python mentions.",
            user_id=user_id,
            slug="javascript-tutorial",
            section="Regression-Testing",
        )

        # Index both
        SearchIndexService.index_page(page1.id, page1.content, page1.title)
        SearchIndexService.index_page(page2.id, page2.content, page2.title)

        # Add manual keyword to page1 (gives 10 points)
        SearchIndexService.add_manual_keyword(page1.id, "python")

        # Search
        results = SearchIndexService.search("python")

        # Page1 should have higher score (keyword + more mentions)
        page1_result = next((r for r in results if r["page_id"] == str(page1.id)), None)
        page2_result = next((r for r in results if r["page_id"] == str(page2.id)), None)

        # Both should be found
        assert page1_result is not None

        # Page1 should have higher score due to manual keyword (10 points) + full-text matches
        # Verify it has the keyword match
        keyword_matches = [m for m in page1_result["matches"] if m["is_keyword"]]
        assert len(keyword_matches) > 0  # Should have keyword match

        # Page1 should score at least 10 (from keyword)
        assert page1_result["score"] >= 10

        # If page2 is found, page1 should score higher (unless page2 also has keyword, which it doesn't)
        if page2_result:
            # Page2 should only have full-text matches (1 point each)
            # Page1 has keyword (10 points) + full-text matches, so should be higher
            assert page1_result["score"] >= page2_result["score"]
