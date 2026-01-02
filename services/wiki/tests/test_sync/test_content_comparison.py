"""Tests for Feature 5.1: Content Comparison for Sync Decisions"""

import os
import tempfile
import time
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from app import db
from app.models.page import Page
from app.sync.sync_utility import SyncUtility


@pytest.fixture
def temp_pages_dir(app):
    """Create temporary pages directory"""
    temp_dir = tempfile.mkdtemp()
    original_pages_dir = app.config.get("WIKI_PAGES_DIR")
    app.config["WIKI_PAGES_DIR"] = temp_dir

    yield temp_dir

    app.config["WIKI_PAGES_DIR"] = original_pages_dir
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def admin_user_id():
    """Admin user ID for testing"""
    return uuid.uuid4()


@pytest.fixture
def sync_utility(app, admin_user_id):
    """Create sync utility instance"""
    with app.app_context():
        yield SyncUtility(admin_user_id=admin_user_id)


def test_should_sync_file_identical_content_skips_sync(
    temp_pages_dir, app, sync_utility, admin_user_id
):
    """Test that sync is skipped when file and database content are identical (hash match)"""
    with app.app_context():
        # Enable content comparison (default)
        app.config["SYNC_ENABLE_CONTENT_COMPARISON"] = True

        # Create page in database
        page_content = """---
title: "Test Page"
slug: "test-page"
section: "test"
---
# Test Page

Content here.
"""
        page = Page(
            title="Test Page",
            slug="test-page",
            content=page_content,
            section="test",
            created_by=admin_user_id,
            updated_by=admin_user_id,
            file_path="test-page.md",
            updated_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        db.session.add(page)
        db.session.commit()

        # Create file with identical content
        file_path = os.path.join(temp_pages_dir, "test-page.md")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(page_content)

        # Make file newer (to trigger sync check)
        time.sleep(0.1)
        os.utime(file_path, None)

        # Should skip sync because content is identical
        should_sync = sync_utility.should_sync_file("test-page.md", page)
        assert should_sync is False


def test_should_sync_file_different_content_syncs(
    temp_pages_dir, app, sync_utility, admin_user_id
):
    """Test that sync proceeds when file and database content differ"""
    with app.app_context():
        # Enable content comparison (default)
        app.config["SYNC_ENABLE_CONTENT_COMPARISON"] = True

        # Create page in database
        db_content = """---
title: "Test Page"
slug: "test-page"
section: "test"
---
# Test Page

Original content.
"""
        page = Page(
            title="Test Page",
            slug="test-page",
            content=db_content,
            section="test",
            created_by=admin_user_id,
            updated_by=admin_user_id,
            file_path="test-page.md",
            updated_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        db.session.add(page)
        db.session.commit()

        # Create file with different content
        file_content = """---
title: "Test Page"
slug: "test-page"
section: "test"
---
# Test Page

Updated content.
"""
        file_path = os.path.join(temp_pages_dir, "test-page.md")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(file_content)

        # Make file newer
        time.sleep(0.1)
        os.utime(file_path, None)

        # Should sync because content differs
        should_sync = sync_utility.should_sync_file("test-page.md", page)
        assert should_sync is True


def test_should_sync_file_content_comparison_disabled(
    temp_pages_dir, app, sync_utility, admin_user_id
):
    """Test that content comparison can be disabled via config"""
    with app.app_context():
        # Disable content comparison
        app.config["SYNC_ENABLE_CONTENT_COMPARISON"] = False

        # Create page in database
        page_content = """---
title: "Test Page"
slug: "test-page"
---
# Test Page

Content.
"""
        page = Page(
            title="Test Page",
            slug="test-page",
            content=page_content,
            created_by=admin_user_id,
            updated_by=admin_user_id,
            file_path="test-page.md",
            updated_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        db.session.add(page)
        db.session.commit()

        # Create file with identical content
        file_path = os.path.join(temp_pages_dir, "test-page.md")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(page_content)

        # Make file newer
        time.sleep(0.1)
        os.utime(file_path, None)

        # Should sync because content comparison is disabled (uses timestamp check only)
        should_sync = sync_utility.should_sync_file("test-page.md", page)
        assert should_sync is True


def test_should_sync_file_content_comparison_different_content_file_newer(
    temp_pages_dir, app, sync_utility, admin_user_id
):
    """Test that content comparison works when content differs and file is newer"""
    with app.app_context():
        app.config["SYNC_ENABLE_CONTENT_COMPARISON"] = True

        # Create page in database
        db_content = """---
title: "Test Page"
slug: "test-page"
---
# Test Page

Original content.
"""
        page = Page(
            title="Test Page",
            slug="test-page",
            content=db_content,
            created_by=admin_user_id,
            updated_by=admin_user_id,
            file_path="test-page.md",
            updated_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        db.session.add(page)
        db.session.commit()

        # Create file with different content and newer timestamp
        file_content = """---
title: "Test Page"
slug: "test-page"
---
# Test Page

Different content.
"""
        file_path = os.path.join(temp_pages_dir, "test-page.md")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(file_content)

        # Make file newer
        time.sleep(0.1)
        os.utime(file_path, None)

        # Content differs and file is newer, so should sync
        should_sync = sync_utility.should_sync_file("test-page.md", page)
        assert should_sync is True


def test_compute_content_hash(app, sync_utility):
    """Test content hash computation"""
    with app.app_context():
        content1 = "Test content"
        content2 = "Test content"
        content3 = "Different content"

        hash1 = sync_utility._compute_content_hash(content1)
        hash2 = sync_utility._compute_content_hash(content2)
        hash3 = sync_utility._compute_content_hash(content3)

        # Same content should produce same hash
        assert hash1 == hash2

        # Different content should produce different hash
        assert hash1 != hash3

        # Hash should be a hexadecimal string
        assert len(hash1) == 64  # SHA256 produces 64 hex characters
        assert all(c in "0123456789abcdef" for c in hash1)


def test_get_file_content_hash(temp_pages_dir, app, sync_utility):
    """Test getting content hash from file"""
    with app.app_context():
        file_content = """---
title: "Test"
slug: "test"
---
# Content
"""
        file_path = os.path.join(temp_pages_dir, "test.md")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(file_content)

        hash1 = sync_utility._get_file_content_hash("test.md")
        assert hash1 is not None
        assert len(hash1) == 64

        # Hash should be consistent
        hash2 = sync_utility._get_file_content_hash("test.md")
        assert hash1 == hash2

        # Non-existent file should return None
        hash3 = sync_utility._get_file_content_hash("nonexistent.md")
        assert hash3 is None
