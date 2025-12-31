"""Test fixtures and helpers for API tests"""

import contextlib
import shutil
import tempfile
import uuid
from unittest.mock import patch

import pytest
from app import db
from app.models.comment import Comment
from app.models.page import Page

# Note: app and client fixtures are inherited from tests/conftest.py
# This file only provides API-specific fixtures and helpers


@pytest.fixture(autouse=True)
def setup_test_data_dir(app):
    """Automatically set up temporary directory for test data files"""
    import os

    # Store original values
    original_data_dir = app.config.get("WIKI_DATA_DIR")
    original_pages_dir = app.config.get("WIKI_PAGES_DIR")
    original_uploads_dir = app.config.get("WIKI_UPLOADS_DIR")

    temp_dir = tempfile.mkdtemp()
    app.config["WIKI_DATA_DIR"] = temp_dir
    app.config["WIKI_PAGES_DIR"] = os.path.join(temp_dir, "pages")
    app.config["WIKI_UPLOADS_DIR"] = os.path.join(temp_dir, "uploads", "images")

    # Create directories
    os.makedirs(app.config["WIKI_PAGES_DIR"], exist_ok=True)
    os.makedirs(app.config["WIKI_UPLOADS_DIR"], exist_ok=True)

    yield

    # Clean up temp directory
    try:
        shutil.rmtree(temp_dir)
    except Exception:
        pass

    # Restore original values (though app is being torn down anyway)
    if original_data_dir:
        app.config["WIKI_DATA_DIR"] = original_data_dir
    if original_pages_dir:
        app.config["WIKI_PAGES_DIR"] = original_pages_dir
    if original_uploads_dir:
        app.config["WIKI_UPLOADS_DIR"] = original_uploads_dir


@pytest.fixture
def test_user_id():
    """Create a test user ID"""
    return uuid.uuid4()


@pytest.fixture
def test_writer_id():
    """Create a test writer user ID"""
    return uuid.uuid4()


@pytest.fixture
def test_viewer_id():
    """Create a test viewer user ID"""
    return uuid.uuid4()


@pytest.fixture
def test_admin_id():
    """Create a test admin user ID"""
    return uuid.uuid4()


@pytest.fixture
def test_page(app, test_user_id):
    """Create a test page"""
    with app.app_context():
        # Ensure deterministic slug across tests; remove any leftover
        db.session.query(Page).filter(Page.slug == "test-page").delete(
            synchronize_session=False
        )
        db.session.commit()

        page = Page(
            title="Test Page",
            slug="test-page",
            content="# Test Content\n\nThis is test content.",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            file_path="test-page.md",
        )
        db.session.add(page)
        db.session.commit()
        # Ensure attributes remain available after session cleanup
        db.session.refresh(page)
        db.session.expunge(page)
        return page


@pytest.fixture
def test_draft_page(app, test_user_id):
    """Create a test draft page"""
    with app.app_context():
        db.session.query(Page).filter(Page.slug == "draft-page").delete(
            synchronize_session=False
        )
        db.session.commit()

        page = Page(
            title="Draft Page",
            slug="draft-page",
            content="# Draft Content",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="draft",
            section="Regression-Testing",
            file_path="draft-page.md",
        )
        db.session.add(page)
        db.session.commit()
        db.session.refresh(page)
        db.session.expunge(page)
        return page


@pytest.fixture
def test_comment(app, test_page, test_user_id):
    """Create a test comment"""
    with app.app_context():
        comment = Comment(
            page_id=test_page.id,
            user_id=test_user_id,
            content="This is a test comment",
            is_recommendation=False,
            thread_depth=1,
        )
        db.session.add(comment)
        db.session.commit()
        return comment


@contextlib.contextmanager
def mock_auth(user_id, role="viewer", username="testuser"):
    """
    Context manager to mock authentication for tests.

    Usage:
        with mock_auth(user_id, 'writer'):
            response = client.post('/api/pages', ...)
    """

    def _get_user_from_token(token):
        # Always return the user for any token when mocked
        if token:  # If any token is provided, return the user
            return {"user_id": str(user_id), "role": role, "username": username}
        return None

    # Patch get_user_from_token to always return our mock user when token exists
    with patch(
        "app.middleware.auth.get_user_from_token", side_effect=_get_user_from_token
    ):
        yield


def auth_headers(user_id, role="viewer"):
    """Generate auth headers for testing"""
    # For now, we'll use a mock token
    # In real implementation, this would be a JWT
    return {"Authorization": f"Bearer mock-token-{user_id}-{role}"}
