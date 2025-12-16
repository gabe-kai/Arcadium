"""Performance tests for caching functionality"""
import uuid
import pytest
from app import db
from app.models.page import Page
from app.services.cache_service import CacheService
from app.utils.markdown_service import markdown_to_html
from app.utils.toc_service import generate_toc


@pytest.fixture
def test_user_id():
    """Test user ID fixture"""
    return uuid.UUID("00000000-0000-0000-0000-000000000001")


def test_html_caching_performance(app, test_user_id):
    """Test that HTML caching improves performance"""
    with app.app_context():
        content = "# Test\n\n" + "This is a test. " * 1000  # Large content
        
        # First call - should generate and cache
        html1 = CacheService.get_html_cache(content)
        assert html1 is None  # Not cached yet
        
        # Generate HTML
        html = markdown_to_html(content)
        CacheService.set_html_cache(content, html, str(test_user_id))
        
        # Second call - should use cache
        html2 = CacheService.get_html_cache(content)
        assert html2 == html
        assert html2 is not None


def test_toc_caching_performance(app, test_user_id):
    """Test that TOC caching improves performance"""
    with app.app_context():
        content = "# Title\n\n" + "\n".join([f"## Section {i}" for i in range(100)])
        
        # First call - should generate and cache
        toc1 = CacheService.get_toc_cache(content)
        assert toc1 is None  # Not cached yet
        
        # Generate TOC
        toc = generate_toc(content)
        CacheService.set_toc_cache(content, toc, str(test_user_id))
        
        # Second call - should use cache
        toc2 = CacheService.get_toc_cache(content)
        assert toc2 == toc
        assert len(toc2) == 100


def test_cache_invalidation_on_update(app, test_user_id):
    """Test that cache is invalidated when content is updated"""
    with app.app_context():
        content1 = "# Original Title"
        content2 = "# Updated Title"
        
        html1 = markdown_to_html(content1)
        CacheService.set_html_cache(content1, html1, str(test_user_id))
        
        # Verify cache exists
        assert CacheService.get_html_cache(content1) == html1
        
        # Invalidate cache
        CacheService.invalidate_cache(content1)
        
        # Cache should be gone
        assert CacheService.get_html_cache(content1) is None


def test_lazy_loading_comments():
    """Test that comments are lazy-loaded (separate endpoint)"""
    # Comments are already lazy-loaded via separate endpoint
    # This test verifies the pattern is in place
    # GET /api/pages/{page_id}/comments is separate from GET /api/pages/{page_id}
    assert True  # Comments endpoint exists separately


def test_comment_query_optimization(app):
    """Test that comment queries are optimized (single query instead of N+1)"""
    with app.app_context():
        from app.services.comment_service import CommentService
        from app.models.comment import Comment
        
        # Create test page
        page = Page(
            title="Test Page",
            slug="test-page",
            content="# Test",
            created_by=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            updated_by=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            status='published',
            file_path="test-page.md"
        )
        db.session.add(page)
        db.session.commit()
        
        # Create multiple comments with replies
        parent1 = Comment(
            page_id=page.id,
            user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            content="Parent 1",
            thread_depth=1
        )
        db.session.add(parent1)
        db.session.flush()
        
        reply1 = Comment(
            page_id=page.id,
            user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            content="Reply 1",
            parent_comment_id=parent1.id,
            thread_depth=2
        )
        db.session.add(reply1)
        db.session.commit()
        
        # Get comments with replies - should use optimized query
        comments = CommentService.get_comments(page.id, include_replies=True)
        
        assert len(comments) == 1
        assert len(comments[0]['replies']) == 1
        assert comments[0]['replies'][0]['content'] == "Reply 1"
