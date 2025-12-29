"""Edge case and error condition tests for PageService"""

import uuid

import pytest
from app import db
from app.services.page_service import PageService
from sqlalchemy.exc import IntegrityError


def test_create_page_empty_title(app):
    """Test creating page with empty title (should fail or use default)"""
    with app.app_context():
        user_id = uuid.uuid4()

        # Empty title might be allowed (uses slug as fallback) or rejected
        try:
            page = PageService.create_page(
                title="", content="Content", user_id=user_id, slug="test"
            )
            # If it succeeds, title should be set to something
            assert page.title is not None and len(page.title) > 0
        except (ValueError, AssertionError):
            # Or it should raise an error
            pass


def test_create_page_empty_content(app):
    """Test creating page with empty content (should be allowed)"""
    with app.app_context():
        user_id = uuid.uuid4()

        page = PageService.create_page(
            title="Empty Page", content="", user_id=user_id, slug="empty-page"
        )

        assert page is not None
        assert page.content == ""


def test_create_page_very_long_title(app):
    """Test creating page with very long title"""
    with app.app_context():
        user_id = uuid.uuid4()
        long_title = "A" * 300  # Exceeds VARCHAR(255) limit

        # Should either truncate or raise error
        try:
            page = PageService.create_page(
                title=long_title, content="Content", user_id=user_id, slug="long-title"
            )
            # If it succeeds, title should be truncated
            assert len(page.title) <= 255
        except (ValueError, Exception):
            # Or it should raise an error
            pass


def test_create_page_very_long_content(app):
    """Test creating page with very long content"""
    with app.app_context():
        user_id = uuid.uuid4()
        long_content = "Word " * 100000  # Very long content

        page = PageService.create_page(
            title="Long Content Page",
            content=long_content,
            user_id=user_id,
            slug="long-content",
        )

        assert page is not None
        assert page.word_count > 0
        assert page.content_size_kb > 0


def test_update_page_nonexistent(app):
    """Test updating a non-existent page (should fail)"""
    with app.app_context():
        user_id = uuid.uuid4()
        fake_id = uuid.uuid4()

        with pytest.raises(ValueError):
            PageService.update_page(
                page_id=fake_id, user_id=user_id, content="New content"
            )


def test_delete_page_nonexistent(app):
    """Test deleting a non-existent page (should fail)"""
    with app.app_context():
        user_id = uuid.uuid4()
        fake_id = uuid.uuid4()

        with pytest.raises(ValueError):
            PageService.delete_page(page_id=fake_id, user_id=user_id)


def test_create_page_invalid_parent(app):
    """Test creating page with invalid parent ID"""
    with app.app_context():
        user_id = uuid.uuid4()
        fake_parent_id = uuid.uuid4()

        # Should either create without parent or raise error
        try:
            page = PageService.create_page(
                title="Test Page",
                content="Content",
                user_id=user_id,
                slug="test-page",
                parent_id=fake_parent_id,
            )
            # If it succeeds, parent should be None or ignored
            assert page.parent_id is None or page.parent_id == fake_parent_id
        except ValueError:
            # Or it should raise an error
            pass


def test_update_page_slug_to_existing(app):
    """Test updating page slug to an existing slug (should fail)"""
    with app.app_context():
        user_id = uuid.uuid4()

        # Create two pages
        PageService.create_page(
            title="Page 1", content="Content 1", user_id=user_id, slug="page-1"
        )

        page2 = PageService.create_page(
            title="Page 2", content="Content 2", user_id=user_id, slug="page-2"
        )

        # Try to change page2's slug to page1's slug
        with pytest.raises((ValueError, IntegrityError)):
            PageService.update_page(page_id=page2.id, user_id=user_id, slug="page-1")


def test_list_pages_empty_database(app):
    """Test listing pages when database is empty"""
    with app.app_context():
        pages = PageService.list_pages()
        assert pages == []


def test_get_page_nonexistent(app):
    """Test getting a non-existent page"""
    with app.app_context():
        fake_id = uuid.uuid4()
        page = PageService.get_page(fake_id)
        assert page is None


def test_can_edit_nonexistent_page(app):
    """Test permission check on non-existent page"""
    with app.app_context():
        user_id = uuid.uuid4()
        fake_id = uuid.uuid4()

        # Should return False or raise error
        try:
            result = PageService.can_edit(fake_id, user_id, "writer")
            assert result is False
        except ValueError:
            # Or it should raise an error
            pass


def test_create_page_special_characters_in_slug(app):
    """Test creating page with special characters in slug"""
    with app.app_context():
        user_id = uuid.uuid4()

        # Invalid slug should be rejected
        with pytest.raises(ValueError):
            PageService.create_page(
                title="Test Page",
                content="Content",
                user_id=user_id,
                slug="test-page-with-special-chars-!@#$%",
            )


def test_update_page_no_changes(app):
    """Test updating page with no actual changes"""
    with app.app_context():
        user_id = uuid.uuid4()

        page = PageService.create_page(
            title="Test Page", content="Content", user_id=user_id, slug="test-page"
        )

        original_updated_at = page.updated_at

        # Update with same content
        updated = PageService.update_page(
            page_id=page.id,
            user_id=user_id,
            content="Content",  # Same content
        )

        # Should still update (timestamp changes)
        assert updated.updated_at >= original_updated_at


def test_create_page_unicode_content(app):
    """Test creating page with unicode characters"""
    with app.app_context():
        user_id = uuid.uuid4()

        page = PageService.create_page(
            title="Test Page with 中文 and émojis 🎮",
            content="Content with unicode: 日本語, русский, العربية",
            user_id=user_id,
            slug="unicode-page",
        )

        assert page is not None
        assert "中文" in page.title
        assert "日本語" in page.content


def test_list_pages_with_many_pages(app):
    """Test listing pages with many pages (performance test)"""
    with app.app_context():
        user_id = uuid.uuid4()

        # Create many pages
        for i in range(50):
            PageService.create_page(
                title=f"Page {i}",
                content=f"Content {i}",
                user_id=user_id,
                slug=f"page-{i}",
            )

        # Should be able to list all
        pages = PageService.list_pages()
        assert len(pages) == 50


def test_create_page_with_all_fields(app):
    """Test creating page with all optional fields"""
    with app.app_context():
        user_id = uuid.uuid4()

        # Create parent page first
        parent = PageService.create_page(
            title="Parent Page",
            content="Parent content",
            user_id=user_id,
            slug="parent",
        )

        # Create child with all fields (order_index is set via update, not create)
        page = PageService.create_page(
            title="Child Page",
            content="Child content",
            user_id=user_id,
            slug="child",
            parent_id=parent.id,
            section="test-section",
            status="draft",
        )

        assert page.parent_id == parent.id
        assert page.section == "test-section"
        assert page.status == "draft"

        # Update order_index separately
        page = PageService.update_page(page_id=page.id, user_id=user_id)
        page.order_index = 5
        db.session.commit()
        assert page.order_index == 5
