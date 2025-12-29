"""Test Page model"""

import uuid

from app import db
from app.models.page import Page


def test_page_creation(app):
    """Test creating a page"""
    with app.app_context():
        page = Page(
            title="Test Page",
            slug="test-page",
            file_path="data/pages/test-page.md",
            content="# Test Page\n\nContent here",
            created_by=uuid.uuid4(),
            updated_by=uuid.uuid4(),
        )
        db.session.add(page)
        db.session.commit()

        assert page.id is not None
        assert page.title == "Test Page"
        assert page.slug == "test-page"
        assert page.status == "published"
        assert page.version == 1


def test_slug_uniqueness(app):
    """Test that slugs must be unique"""
    with app.app_context():
        user_id = uuid.uuid4()

        page1 = Page(
            title="Page 1",
            slug="test-slug",
            file_path="data/pages/test-slug.md",
            content="Content",
            created_by=user_id,
            updated_by=user_id,
        )
        db.session.add(page1)
        db.session.commit()

        page2 = Page(
            title="Page 2",
            slug="test-slug",  # Duplicate slug
            file_path="data/pages/test-slug-2.md",
            content="Content",
            created_by=user_id,
            updated_by=user_id,
        )
        db.session.add(page2)

        # Should raise integrity error
        import pytest
        from sqlalchemy.exc import IntegrityError

        with pytest.raises(IntegrityError):
            db.session.commit()


def test_parent_child_relationship(app):
    """Test parent-child relationship"""
    with app.app_context():
        user_id = uuid.uuid4()

        parent = Page(
            title="Parent Page",
            slug="parent",
            file_path="data/pages/parent.md",
            content="Parent content",
            created_by=user_id,
            updated_by=user_id,
        )
        db.session.add(parent)
        db.session.commit()

        child = Page(
            title="Child Page",
            slug="child",
            file_path="data/pages/child.md",
            content="Child content",
            parent_id=parent.id,
            created_by=user_id,
            updated_by=user_id,
        )
        db.session.add(child)
        db.session.commit()

        assert child.parent_id == parent.id
        assert child in parent.children


def test_section_independence(app):
    """Test that section and parent are independent"""
    with app.app_context():
        user_id = uuid.uuid4()

        page = Page(
            title="Test Page",
            slug="test",
            file_path="data/pages/test.md",
            content="Content",
            section="game-mechanics",
            created_by=user_id,
            updated_by=user_id,
        )
        db.session.add(page)
        db.session.commit()

        # Section can be different from parent's section
        assert page.section == "game-mechanics"
        assert page.parent_id is None  # No parent, but has section
