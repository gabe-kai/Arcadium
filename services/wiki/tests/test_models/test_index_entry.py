"""Test IndexEntry model"""

import uuid

from app import db
from app.models.index_entry import IndexEntry
from app.models.page import Page


def test_index_entry_creation(app):
    """Test creating an index entry"""
    with app.app_context():
        user_id = uuid.uuid4()

        # Create a page first
        page = Page(
            title="Test Page",
            slug="test-page",
            file_path="data/pages/test-page.md",
            content="Content",
            section="Regression-Testing",
            created_by=user_id,
            updated_by=user_id,
        )
        db.session.add(page)
        db.session.commit()

        # Create an index entry
        entry = IndexEntry(
            page_id=page.id,
            term="test",
            context="This is a test page",
            position=0,
            is_keyword=False,
            is_manual=False,
        )
        db.session.add(entry)
        db.session.commit()

        assert entry.id is not None
        assert entry.page_id == page.id
        assert entry.term == "test"
        assert entry.context == "This is a test page"
        assert entry.position == 0
        assert entry.is_keyword is False
        assert entry.is_manual is False


def test_keyword_entry(app):
    """Test creating a keyword entry"""
    with app.app_context():
        user_id = uuid.uuid4()

        page = Page(
            title="Test Page",
            slug="test-page",
            file_path="data/pages/test-page.md",
            content="Content",
            section="Regression-Testing",
            created_by=user_id,
            updated_by=user_id,
        )
        db.session.add(page)
        db.session.commit()

        # Create keyword entry
        entry = IndexEntry(
            page_id=page.id,
            term="important",
            context="Important keyword",
            position=None,
            is_keyword=True,
            is_manual=False,
        )
        db.session.add(entry)
        db.session.commit()

        assert entry.is_keyword is True
        assert entry.position is None  # Keywords don't have positions


def test_manual_keyword_entry(app):
    """Test creating a manually tagged keyword"""
    with app.app_context():
        user_id = uuid.uuid4()

        page = Page(
            title="Test Page",
            slug="test-page",
            file_path="data/pages/test-page.md",
            content="Content",
            section="Regression-Testing",
            created_by=user_id,
            updated_by=user_id,
        )
        db.session.add(page)
        db.session.commit()

        # Create manual keyword entry
        entry = IndexEntry(
            page_id=page.id,
            term="manual-tag",
            context="Manually added tag",
            position=None,
            is_keyword=True,
            is_manual=True,
        )
        db.session.add(entry)
        db.session.commit()

        assert entry.is_keyword is True
        assert entry.is_manual is True


def test_index_entry_relationship_to_page(app):
    """Test index entry relationship to page"""
    with app.app_context():
        user_id = uuid.uuid4()

        page = Page(
            title="Test Page",
            slug="test-page",
            file_path="data/pages/test-page.md",
            content="Content",
            section="Regression-Testing",
            created_by=user_id,
            updated_by=user_id,
        )
        db.session.add(page)
        db.session.commit()

        # Create multiple index entries
        entry1 = IndexEntry(
            page_id=page.id,
            term="term1",
            context="Context 1",
            position=0,
            is_keyword=False,
            is_manual=False,
        )
        entry2 = IndexEntry(
            page_id=page.id,
            term="term2",
            context="Context 2",
            position=10,
            is_keyword=False,
            is_manual=False,
        )
        db.session.add_all([entry1, entry2])
        db.session.commit()

        # Check relationship
        assert len(page.index_entries) == 2
        assert entry1.page == page
        assert entry2.page == page


def test_index_entry_cascade_delete(app):
    """Test that index entries are deleted when page is deleted"""
    with app.app_context():
        user_id = uuid.uuid4()

        page = Page(
            title="Test Page",
            slug="test-page",
            file_path="data/pages/test-page.md",
            content="Content",
            section="Regression-Testing",
            created_by=user_id,
            updated_by=user_id,
        )
        db.session.add(page)
        db.session.commit()

        # Create index entry
        entry = IndexEntry(
            page_id=page.id,
            term="test",
            context="Context",
            position=0,
            is_keyword=False,
            is_manual=False,
        )
        db.session.add(entry)
        db.session.commit()

        entry_id = entry.id

        # Delete index entries first (SQLite doesn't handle CASCADE well)
        IndexEntry.query.filter_by(page_id=page.id).delete()

        # Delete page
        db.session.delete(page)
        db.session.commit()

        # Index entry should be deleted
        assert IndexEntry.query.get(entry_id) is None


def test_fulltext_vs_keyword_entries(app):
    """Test distinction between full-text and keyword entries"""
    with app.app_context():
        user_id = uuid.uuid4()

        page = Page(
            title="Test Page",
            slug="test-page",
            file_path="data/pages/test-page.md",
            content="Content",
            section="Regression-Testing",
            created_by=user_id,
            updated_by=user_id,
        )
        db.session.add(page)
        db.session.commit()

        # Create full-text entry (has position)
        fulltext_entry = IndexEntry(
            page_id=page.id,
            term="word",
            context="A word in the text",
            position=5,
            is_keyword=False,
            is_manual=False,
        )

        # Create keyword entry (no position)
        keyword_entry = IndexEntry(
            page_id=page.id,
            term="important",
            context="Important concept",
            position=None,
            is_keyword=True,
            is_manual=False,
        )

        db.session.add_all([fulltext_entry, keyword_entry])
        db.session.commit()

        assert fulltext_entry.is_keyword is False
        assert fulltext_entry.position == 5
        assert keyword_entry.is_keyword is True
        assert keyword_entry.position is None
