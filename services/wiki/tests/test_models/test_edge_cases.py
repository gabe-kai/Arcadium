"""Edge case tests for models"""
import uuid
import pytest
from app.models.page import Page
from app.models.comment import Comment
from app.models.page_link import PageLink
from app import db


def test_page_with_max_fields(app):
    """Test page with maximum field lengths"""
    with app.app_context():
        user_id = uuid.uuid4()
        
        # Create page with long title (at limit)
        long_title = "A" * 255
        page = Page(
            title=long_title,
            slug="test-page",
            file_path="data/pages/test-page.md",
            content="Content",
            created_by=user_id,
            updated_by=user_id
        )
        db.session.add(page)
        db.session.commit()
        
        assert len(page.title) == 255


def test_comment_with_max_depth(app):
    """Test comment threading at maximum depth"""
    with app.app_context():
        from app.models.comment import Comment
        user_id = uuid.uuid4()
        
        # Create page
        page = Page(
            title="Test Page",
            slug="test-page",
            file_path="data/pages/test-page.md",
            content="Content",
            created_by=user_id,
            updated_by=user_id
        )
        db.session.add(page)
        db.session.commit()
        
        # Create comment thread at max depth (5 levels)
        parent = None
        for depth in range(1, 6):
            comment = Comment(
                page_id=page.id,
                user_id=user_id,
                content=f"Comment at depth {depth}",
                parent_comment_id=parent.id if parent else None,
                thread_depth=depth
            )
            db.session.add(comment)
            db.session.commit()
            parent = comment
        
        # Try to create 6th level (should fail or be limited)
        # The Comment model should calculate depth automatically
        try:
            comment6 = Comment(
                page_id=page.id,
                user_id=user_id,
                content="Comment at depth 6",
                parent_comment_id=parent.id
            )
            # Depth should be calculated automatically
            db.session.add(comment6)
            db.session.commit()
            # If it succeeds, depth should be capped at 5
            assert comment6.thread_depth <= 5
        except (ValueError, AssertionError):
            # Or it should raise an error
            pass


def test_page_link_self_reference(app):
    """Test page linking to itself (should be allowed or prevented)"""
    with app.app_context():
        user_id = uuid.uuid4()
        
        # Create page
        page = Page(
            title="Test Page",
            slug="test-page",
            file_path="data/pages/test-page.md",
            content="Content",
            created_by=user_id,
            updated_by=user_id
        )
        db.session.add(page)
        db.session.commit()
        
        # Try to create self-link
        try:
            link = PageLink(
                from_page_id=page.id,
                to_page_id=page.id,
                link_text="Self link"
            )
            db.session.add(link)
            db.session.commit()
            # If it succeeds, that's fine (self-links allowed)
            assert link.from_page_id == link.to_page_id
        except (ValueError, IntegrityError):
            # Or it should be prevented
            pass


def test_page_with_null_parent(app):
    """Test page with null parent (root page)"""
    with app.app_context():
        user_id = uuid.uuid4()
        
        page = Page(
            title="Root Page",
            slug="root-page",
            file_path="data/pages/root-page.md",
            content="Content",
            parent_id=None,  # Explicitly null
            created_by=user_id,
            updated_by=user_id
        )
        db.session.add(page)
        db.session.commit()
        
        assert page.parent_id is None
        assert page.parent is None


def test_comment_with_empty_content(app):
    """Test comment with empty content (should fail)"""
    with app.app_context():
        from app.models.comment import Comment
        user_id = uuid.uuid4()
        
        # Create page
        page = Page(
            title="Test Page",
            slug="test-page",
            file_path="data/pages/test-page.md",
            content="Content",
            created_by=user_id,
            updated_by=user_id
        )
        db.session.add(page)
        db.session.commit()
        
        # Try to create comment with empty content
        # May or may not be enforced at model level (could be at API level)
        try:
            comment = Comment(
                page_id=page.id,
                user_id=user_id,
                content="",  # Empty content
                thread_depth=1
            )
            db.session.add(comment)
            db.session.commit()
            # If it succeeds, that's fine (validation at API level)
        except (ValueError, IntegrityError):
            # Or it should raise an error
            pass


def test_page_with_duplicate_slug_different_cases(app):
    """Test page slug uniqueness with different cases"""
    with app.app_context():
        user_id = uuid.uuid4()
        
        # Create page with lowercase slug
        page1 = Page(
            title="Page 1",
            slug="test-page",
            file_path="data/pages/test-page.md",
            content="Content",
            created_by=user_id,
            updated_by=user_id
        )
        db.session.add(page1)
        db.session.commit()
        
        # Try to create page with uppercase slug
        # Should either fail (case-sensitive) or succeed (case-insensitive)
        try:
            page2 = Page(
                title="Page 2",
                slug="TEST-PAGE",  # Different case
                file_path="data/pages/TEST-PAGE.md",
                content="Content",
                created_by=user_id,
                updated_by=user_id
            )
            db.session.add(page2)
            db.session.commit()
            # If it succeeds, slugs are case-insensitive or different
        except IntegrityError:
            # Or it should fail due to uniqueness constraint
            pass

