"""Test PageLink model"""

import uuid

from app import db
from app.models.page import Page
from app.models.page_link import PageLink


def test_link_creation(app):
    """Test creating a link between pages"""
    with app.app_context():
        user_id = uuid.uuid4()

        # Create two pages
        page1 = Page(
            title="Page 1",
            slug="page-1",
            file_path="data/pages/page-1.md",
            content="Content 1",
            created_by=user_id,
            updated_by=user_id,
        )
        page2 = Page(
            title="Page 2",
            slug="page-2",
            file_path="data/pages/page-2.md",
            content="Content 2",
            created_by=user_id,
            updated_by=user_id,
        )
        db.session.add_all([page1, page2])
        db.session.commit()

        # Create link
        link = PageLink(
            from_page_id=page1.id, to_page_id=page2.id, link_text="Link to Page 2"
        )
        db.session.add(link)
        db.session.commit()

        assert link.from_page_id == page1.id
        assert link.to_page_id == page2.id
        assert link.link_text == "Link to Page 2"


def test_bidirectional_tracking(app):
    """Test bidirectional link tracking"""
    with app.app_context():
        user_id = uuid.uuid4()

        page1 = Page(
            title="Page 1",
            slug="page-1",
            file_path="data/pages/page-1.md",
            content="Content 1",
            created_by=user_id,
            updated_by=user_id,
        )
        page2 = Page(
            title="Page 2",
            slug="page-2",
            file_path="data/pages/page-2.md",
            content="Content 2",
            created_by=user_id,
            updated_by=user_id,
        )
        db.session.add_all([page1, page2])
        db.session.commit()

        # Create link from page1 to page2
        link = PageLink(
            from_page_id=page1.id, to_page_id=page2.id, link_text="Link text"
        )
        db.session.add(link)
        db.session.commit()

        # Check outgoing links from page1
        assert len(page1.outgoing_links) == 1
        assert page1.outgoing_links[0].to_page_id == page2.id

        # Check incoming links to page2
        assert len(page2.incoming_links) == 1
        assert page2.incoming_links[0].from_page_id == page1.id


def test_unique_link_constraint(app):
    """Test that duplicate links are prevented"""
    with app.app_context():
        user_id = uuid.uuid4()

        page1 = Page(
            title="Page 1",
            slug="page-1",
            file_path="data/pages/page-1.md",
            content="Content 1",
            created_by=user_id,
            updated_by=user_id,
        )
        page2 = Page(
            title="Page 2",
            slug="page-2",
            file_path="data/pages/page-2.md",
            content="Content 2",
            created_by=user_id,
            updated_by=user_id,
        )
        db.session.add_all([page1, page2])
        db.session.commit()

        # Create first link
        link1 = PageLink(from_page_id=page1.id, to_page_id=page2.id, link_text="Link 1")
        db.session.add(link1)
        db.session.commit()

        # Try to create duplicate link
        link2 = PageLink(from_page_id=page1.id, to_page_id=page2.id, link_text="Link 2")
        db.session.add(link2)

        # Should raise integrity error
        import pytest
        from sqlalchemy.exc import IntegrityError

        with pytest.raises(IntegrityError):
            db.session.commit()
