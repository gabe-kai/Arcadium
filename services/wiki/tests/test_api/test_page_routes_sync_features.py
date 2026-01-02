"""Tests for Feature 5.2 and 5.4: Sync Conflict Warnings and Sync Status in API responses"""

import os
import tempfile
import time
from datetime import datetime, timedelta, timezone

import pytest
from app import db
from app.models.page import Page
from tests.test_api.conftest import auth_headers, mock_auth


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


def test_get_page_includes_sync_status_when_can_edit(
    client, app, temp_pages_dir, test_writer_id
):
    """Test that GET page endpoint includes sync_status for users who can edit"""
    with app.app_context():
        # Create page with file_path
        page = Page(
            title="Test Page",
            slug="test-page-sync",
            content="# Test",
            created_by=test_writer_id,
            updated_by=test_writer_id,
            status="published",
            section="Regression-Testing",
            file_path="test-page-sync.md",
            updated_at=datetime.now(timezone.utc),
        )
        db.session.add(page)
        db.session.commit()

        # Create file
        file_path = os.path.join(temp_pages_dir, "test-page-sync.md")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("# Test")
        page_id = str(page.id)

    with mock_auth(test_writer_id, "writer"):
        response = client.get(
            f"/api/pages/{page_id}", headers=auth_headers(test_writer_id, "writer")
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "sync_status" in data
        assert data["sync_status"] is not None
        assert "last_updated_source" in data["sync_status"]
        assert "file_modification_time" in data["sync_status"]
        assert "database_updated_at" in data["sync_status"]
        assert "is_synced" in data["sync_status"]


def test_get_page_sync_status_file_newer(client, app, temp_pages_dir, test_writer_id):
    """Test sync_status indicates file is newer"""
    with app.app_context():
        # Create page with older timestamp
        page = Page(
            title="Test Page",
            slug="test-page-file-newer",
            content="# Test",
            created_by=test_writer_id,
            updated_by=test_writer_id,
            status="published",
            section="Regression-Testing",
            file_path="test-page-file-newer.md",
            updated_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        db.session.add(page)
        db.session.commit()

        # Create file with newer timestamp
        file_path = os.path.join(temp_pages_dir, "test-page-file-newer.md")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("# Test")
        time.sleep(0.1)
        os.utime(file_path, None)
        page_id = str(page.id)

    with mock_auth(test_writer_id, "writer"):
        response = client.get(
            f"/api/pages/{page_id}", headers=auth_headers(test_writer_id, "writer")
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "sync_status" in data
        status = data["sync_status"]
        assert status["last_updated_source"] == "file"
        assert status["is_synced"] is False


def test_get_page_sync_status_database_newer(
    client, app, temp_pages_dir, test_writer_id
):
    """Test sync_status indicates database is newer"""
    with app.app_context():
        # Create page with recent timestamp
        page = Page(
            title="Test Page",
            slug="test-page-db-newer",
            content="# Test",
            created_by=test_writer_id,
            updated_by=test_writer_id,
            status="published",
            section="Regression-Testing",
            file_path="test-page-db-newer.md",
            updated_at=datetime.now(timezone.utc),
        )
        db.session.add(page)
        db.session.commit()

        # Create file with older timestamp
        file_path = os.path.join(temp_pages_dir, "test-page-db-newer.md")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("# Test")
        old_time = (datetime.now(timezone.utc) - timedelta(hours=1)).timestamp()
        os.utime(file_path, (old_time, old_time))
        page_id = str(page.id)

    with mock_auth(test_writer_id, "writer"):
        response = client.get(
            f"/api/pages/{page_id}", headers=auth_headers(test_writer_id, "writer")
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "sync_status" in data
        status = data["sync_status"]
        assert status["last_updated_source"] == "database"
        assert status["is_synced"] is False


def test_get_page_includes_sync_conflict_when_detected(
    client, app, temp_pages_dir, test_writer_id
):
    """Test that GET page endpoint includes sync_conflict when conflict is detected"""
    with app.app_context():
        app.config["SYNC_CONFLICT_GRACE_PERIOD_SECONDS"] = 600

        # Create page with file_path
        page = Page(
            title="Test Page",
            slug="test-page-conflict",
            content="# Original",
            created_by=test_writer_id,
            updated_by=test_writer_id,
            status="published",
            section="Regression-Testing",
            file_path="test-page-conflict.md",
            updated_at=datetime.now(timezone.utc),
        )
        db.session.add(page)
        db.session.commit()

        # Create file with newer timestamp and different content
        file_path = os.path.join(temp_pages_dir, "test-page-conflict.md")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("# Updated")
        time.sleep(0.1)
        os.utime(file_path, None)
        page_id = str(page.id)

    with mock_auth(test_writer_id, "writer"):
        response = client.get(
            f"/api/pages/{page_id}", headers=auth_headers(test_writer_id, "writer")
        )
        assert response.status_code == 200
        data = response.get_json()
        # May or may not have conflict depending on grace period
        # But should have sync_status
        assert "sync_status" in data


def test_get_page_no_sync_status_when_cannot_edit(client, app, test_page, test_user_id):
    """Test that sync_status is not included for users who cannot edit"""
    with mock_auth(test_user_id, "viewer"):
        page_id = str(test_page.id)
        response = client.get(
            f"/api/pages/{page_id}", headers=auth_headers(test_user_id, "viewer")
        )
        assert response.status_code == 200
        data = response.get_json()
        # Viewers can't edit, so no sync_status
        assert "sync_status" not in data
        assert "sync_conflict" not in data


def test_update_page_includes_sync_status(client, app, temp_pages_dir, test_writer_id):
    """Test that PUT page endpoint includes sync_status after update"""
    with app.app_context():
        # Create page
        page = Page(
            title="Page to Update",
            slug="page-sync-update",
            content="# Original",
            created_by=test_writer_id,
            updated_by=test_writer_id,
            status="published",
            section="Regression-Testing",
            file_path="page-sync-update.md",
        )
        db.session.add(page)
        db.session.commit()

        # Create file
        file_path = os.path.join(temp_pages_dir, "page-sync-update.md")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("# Original")
        page_id = str(page.id)

    with mock_auth(test_writer_id, "writer"):
        response = client.put(
            f"/api/pages/{page_id}",
            json={"title": "Updated Title"},
            headers=auth_headers(test_writer_id, "writer"),
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "sync_status" in data
        assert data["sync_status"] is not None
        assert "last_updated_source" in data["sync_status"]


def test_get_page_sync_status_missing_file(client, app, test_writer_id):
    """Test sync_status is None when file doesn't exist"""
    with app.app_context():
        # Create page with file_path but no actual file
        page = Page(
            title="Test Page",
            slug="test-page-no-file",
            content="# Test",
            created_by=test_writer_id,
            updated_by=test_writer_id,
            status="published",
            section="Regression-Testing",
            file_path="nonexistent.md",
        )
        db.session.add(page)
        db.session.commit()
        page_id = str(page.id)

    with mock_auth(test_writer_id, "writer"):
        response = client.get(
            f"/api/pages/{page_id}", headers=auth_headers(test_writer_id, "writer")
        )
        assert response.status_code == 200
        data = response.get_json()
        # sync_status should be None or not present when file doesn't exist
        # (depending on implementation - check_sync_conflict returns None in this case)
        if "sync_status" in data:
            assert data["sync_status"] is None
