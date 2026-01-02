"""Tests for Feature 5.2 and 5.4: Conflict Warnings and Sync Status Tracking"""

import os
import tempfile
import time
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from app import db
from app.models.page import Page
from app.services.page_service import PageService


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


def test_check_sync_conflict_no_file_path(app, admin_user_id):
    """Test check_sync_conflict returns None when page has empty file_path"""
    with app.app_context():
        page = Page(
            title="Test",
            slug="test",
            content="# Test",
            created_by=admin_user_id,
            updated_by=admin_user_id,
            file_path="",  # Empty string - file_path is NOT NULL in DB
        )
        db.session.add(page)
        db.session.commit()

        # Manually set file_path to None after creation to test the code path
        # (In practice, file_path is always set, but code checks for it defensively)
        page.file_path = None
        conflict = PageService.check_sync_conflict(page)
        assert conflict is None


def test_check_sync_conflict_file_not_exists(app, admin_user_id, temp_pages_dir):
    """Test check_sync_conflict returns None when file doesn't exist"""
    with app.app_context():
        page = Page(
            title="Test",
            slug="test",
            content="# Test",
            created_by=admin_user_id,
            updated_by=admin_user_id,
            file_path="nonexistent.md",
        )
        db.session.add(page)
        db.session.commit()

        conflict = PageService.check_sync_conflict(page)
        assert conflict is None


def test_check_sync_conflict_file_newer(app, admin_user_id, temp_pages_dir):
    """Test check_sync_conflict detects when file is newer than database"""
    with app.app_context():
        # Create page in database
        page = Page(
            title="Test",
            slug="test",
            content="# Test",
            created_by=admin_user_id,
            updated_by=admin_user_id,
            file_path="test.md",
            updated_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        db.session.add(page)
        db.session.commit()

        # Create file with newer timestamp
        file_path = os.path.join(temp_pages_dir, "test.md")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("# Updated Test")
        time.sleep(0.1)
        os.utime(file_path, None)

        conflict = PageService.check_sync_conflict(page)
        assert conflict is not None
        assert conflict["has_conflict"] is True
        assert conflict["file_newer"] is True
        assert "File has been modified more recently" in conflict["message"]


def test_check_sync_conflict_content_different(app, admin_user_id, temp_pages_dir):
    """Test check_sync_conflict detects when content differs"""
    with app.app_context():
        app.config["SYNC_ENABLE_CONTENT_COMPARISON"] = True

        # Create page in database
        db_content = """---
title: "Test"
slug: "test"
---
# Database Content
"""
        page = Page(
            title="Test",
            slug="test",
            content=db_content,
            created_by=admin_user_id,
            updated_by=admin_user_id,
            file_path="test.md",
            updated_at=datetime.now(timezone.utc),
        )
        db.session.add(page)
        db.session.commit()

        # Create file with different content
        file_content = """---
title: "Test"
slug: "test"
---
# File Content
"""
        file_path = os.path.join(temp_pages_dir, "test.md")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(file_content)

        # Set file timestamp to be same or older (content comparison should still catch it)
        file_time = datetime.now(timezone.utc).timestamp()
        os.utime(file_path, (file_time, file_time))

        conflict = PageService.check_sync_conflict(page)
        assert conflict is not None
        assert conflict["has_conflict"] is True
        assert conflict["content_different"] is True
        assert "File content differs" in conflict["message"]


def test_check_sync_conflict_grace_period(app, admin_user_id, temp_pages_dir):
    """Test check_sync_conflict includes grace period information"""
    with app.app_context():
        app.config["SYNC_CONFLICT_GRACE_PERIOD_SECONDS"] = 600

        # Create page recently updated
        page = Page(
            title="Test",
            slug="test",
            content="# Test",
            created_by=admin_user_id,
            updated_by=admin_user_id,
            file_path="test.md",
            updated_at=datetime.now(timezone.utc),
        )
        db.session.add(page)
        db.session.commit()

        # Create file with newer timestamp
        file_path = os.path.join(temp_pages_dir, "test.md")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("# Updated")
        time.sleep(0.1)
        os.utime(file_path, None)

        conflict = PageService.check_sync_conflict(page)
        assert conflict is not None
        assert "grace_period_remaining" in conflict
        if conflict["grace_period_remaining"]:
            assert conflict["grace_period_remaining"] > 0
            assert (
                "protected" in conflict["message"].lower()
                or "minutes" in conflict["message"]
            )


def test_get_sync_status_no_file_path(app, admin_user_id):
    """Test get_sync_status returns None when page has empty file_path"""
    with app.app_context():
        page = Page(
            title="Test",
            slug="test",
            content="# Test",
            created_by=admin_user_id,
            updated_by=admin_user_id,
            file_path="",  # Empty string - file_path is NOT NULL in DB
        )
        db.session.add(page)
        db.session.commit()

        # Manually set file_path to None after creation to test the code path
        # (In practice, file_path is always set, but code checks for it defensively)
        page.file_path = None
        status = PageService.get_sync_status(page)
        assert status is None


def test_get_sync_status_file_not_exists(app, admin_user_id, temp_pages_dir):
    """Test get_sync_status returns None when file doesn't exist"""
    with app.app_context():
        page = Page(
            title="Test",
            slug="test",
            content="# Test",
            created_by=admin_user_id,
            updated_by=admin_user_id,
            file_path="nonexistent.md",
        )
        db.session.add(page)
        db.session.commit()

        status = PageService.get_sync_status(page)
        assert status is None


def test_get_sync_status_file_newer(app, admin_user_id, temp_pages_dir):
    """Test get_sync_status when file is newer"""
    with app.app_context():
        # Create page in database
        page = Page(
            title="Test",
            slug="test",
            content="# Test",
            created_by=admin_user_id,
            updated_by=admin_user_id,
            file_path="test.md",
            updated_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        db.session.add(page)
        db.session.commit()

        # Create file with newer timestamp
        file_path = os.path.join(temp_pages_dir, "test.md")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("# Test")
        time.sleep(0.1)
        os.utime(file_path, None)

        status = PageService.get_sync_status(page)
        assert status is not None
        assert status["last_updated_source"] == "file"
        assert status["file_modification_time"] > status["database_updated_at"]
        assert status["is_synced"] is False
        assert status["time_difference_seconds"] > 0


def test_get_sync_status_database_newer(app, admin_user_id, temp_pages_dir):
    """Test get_sync_status when database is newer"""
    with app.app_context():
        # Create page in database with recent update
        page = Page(
            title="Test",
            slug="test",
            content="# Test",
            created_by=admin_user_id,
            updated_by=admin_user_id,
            file_path="test.md",
            updated_at=datetime.now(timezone.utc),
        )
        db.session.add(page)
        db.session.commit()

        # Create file with older timestamp
        file_path = os.path.join(temp_pages_dir, "test.md")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("# Test")
        old_time = (datetime.now(timezone.utc) - timedelta(hours=1)).timestamp()
        os.utime(file_path, (old_time, old_time))

        status = PageService.get_sync_status(page)
        assert status is not None
        assert status["last_updated_source"] == "database"
        assert status["database_updated_at"] > status["file_modification_time"]
        assert status["is_synced"] is False
        assert status["time_difference_seconds"] < 0


def test_get_sync_status_synced(app, admin_user_id, temp_pages_dir):
    """Test get_sync_status when file and database are synced"""
    with app.app_context():
        # Create page in database
        db_time = datetime.now(timezone.utc)
        page = Page(
            title="Test",
            slug="test",
            content="# Test",
            created_by=admin_user_id,
            updated_by=admin_user_id,
            file_path="test.md",
            updated_at=db_time,
        )
        db.session.add(page)
        db.session.commit()

        # Create file with matching timestamp
        file_path = os.path.join(temp_pages_dir, "test.md")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("# Test")
        file_time = db_time.timestamp()
        os.utime(file_path, (file_time, file_time))

        status = PageService.get_sync_status(page)
        assert status is not None
        assert status["last_updated_source"] == "synced"
        assert status["is_synced"] is True
        assert abs(status["time_difference_seconds"]) < 1.0


def test_get_sync_status_includes_timestamps(app, admin_user_id, temp_pages_dir):
    """Test get_sync_status includes all required timestamp fields"""
    with app.app_context():
        page = Page(
            title="Test",
            slug="test",
            content="# Test",
            created_by=admin_user_id,
            updated_by=admin_user_id,
            file_path="test.md",
            updated_at=datetime.now(timezone.utc),
        )
        db.session.add(page)
        db.session.commit()

        file_path = os.path.join(temp_pages_dir, "test.md")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("# Test")

        status = PageService.get_sync_status(page)
        assert status is not None
        assert "file_modification_time" in status
        assert "database_updated_at" in status
        assert "time_difference_seconds" in status
        assert isinstance(status["file_modification_time"], (int, float))
        assert isinstance(status["database_updated_at"], (int, float))
        assert isinstance(status["time_difference_seconds"], (int, float))
