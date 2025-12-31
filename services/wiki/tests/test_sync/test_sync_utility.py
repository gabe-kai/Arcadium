"""Tests for sync utility"""

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


def test_resolve_parent_slug_exists(app, sync_utility, admin_user_id):
    """Test resolving parent slug that exists"""
    with app.app_context():
        # Create parent page
        parent = Page(
            title="Parent Page",
            slug="parent-page",
            content="# Parent",
            section="Regression-Testing",
            created_by=admin_user_id,
            updated_by=admin_user_id,
            file_path="parent-page.md",
        )
        db.session.add(parent)
        db.session.commit()

        parent_id = sync_utility.resolve_parent_slug("parent-page")
        assert parent_id == parent.id


def test_resolve_parent_slug_not_exists(app, sync_utility):
    """Test resolving parent slug that doesn't exist"""
    with app.app_context():
        parent_id = sync_utility.resolve_parent_slug("nonexistent-slug")
        assert parent_id is None


def test_resolve_parent_slug_none(app, sync_utility):
    """Test resolving None parent slug"""
    with app.app_context():
        parent_id = sync_utility.resolve_parent_slug(None)
        assert parent_id is None


def test_read_file(temp_pages_dir, app, sync_utility):
    """Test reading and parsing markdown file"""
    with app.app_context():
        # Create test file with frontmatter
        file_path = os.path.join(temp_pages_dir, "test.md")
        content = """---
title: "Test Page"
slug: "test-page"
section: "test"
---
# Test Page

This is test content.
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        frontmatter, markdown = sync_utility.read_file("test.md")

        assert frontmatter["title"] == "Test Page"
        assert frontmatter["slug"] == "test-page"
        assert frontmatter["section"] == "test"
        assert "# Test Page" in markdown
        assert "This is test content" in markdown


def test_read_file_no_frontmatter(temp_pages_dir, app, sync_utility):
    """Test reading file without frontmatter"""
    with app.app_context():
        file_path = os.path.join(temp_pages_dir, "test.md")
        content = "# Test Page\n\nContent here."
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        frontmatter, markdown = sync_utility.read_file("test.md")

        assert frontmatter == {}
        assert "# Test Page" in markdown


def test_should_sync_file_new_file(temp_pages_dir, app, sync_utility):
    """Test should sync new file"""
    with app.app_context():
        file_path = os.path.join(temp_pages_dir, "new.md")
        with open(file_path, "w") as f:
            f.write("# New")

        should_sync = sync_utility.should_sync_file("new.md", None)
        assert should_sync is True


def test_should_sync_file_newer_than_db(
    temp_pages_dir, app, sync_utility, admin_user_id
):
    """Test should sync when file is newer than database"""
    with app.app_context():
        # Create page in database
        page = Page(
            title="Test",
            slug="test",
            content="# Test",
            section="Regression-Testing",
            created_by=admin_user_id,
            updated_by=admin_user_id,
            file_path="test.md",
            updated_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        db.session.add(page)
        db.session.commit()

        # Create file with current timestamp
        file_path = os.path.join(temp_pages_dir, "test.md")
        with open(file_path, "w") as f:
            f.write("# Updated Test")

        # Wait a moment and update file timestamp to ensure it's newer
        time.sleep(0.1)
        os.utime(file_path, None)  # Update file timestamp to current time

        should_sync = sync_utility.should_sync_file("test.md", page)
        assert should_sync is True


def test_should_sync_file_older_than_db(
    temp_pages_dir, app, sync_utility, admin_user_id
):
    """Test should not sync when file is older than database"""
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

        # Create file
        file_path = os.path.join(temp_pages_dir, "test.md")
        with open(file_path, "w") as f:
            f.write("# Test")

        # Make file older than database
        old_time = (datetime.now(timezone.utc) - timedelta(hours=1)).timestamp()
        os.utime(file_path, (old_time, old_time))

        should_sync = sync_utility.should_sync_file("test.md", page)
        assert should_sync is False


def test_sync_file_create_new(temp_pages_dir, app, sync_utility, admin_user_id):
    """Test syncing new file creates page"""
    with app.app_context():
        # Create test file
        file_path = os.path.join(temp_pages_dir, "new-page.md")
        content = """---
title: "New Page"
slug: "new-page"
section: "test"
---
# New Page

Content here.
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        page, status = sync_utility.sync_file("new-page.md")

        assert status is True  # Created
        assert page is not None
        assert page.title == "New Page"
        assert page.slug == "new-page"
        assert page.section == "test"
        assert page.created_by == admin_user_id
        assert page.updated_by == admin_user_id


def test_sync_file_update_existing(temp_pages_dir, app, sync_utility, admin_user_id):
    """Test syncing existing file updates page"""
    with app.app_context():
        # Create page in database
        page = Page(
            title="Old Title",
            slug="test-page",
            content="# Old Content",
            section="Regression-Testing",
            created_by=admin_user_id,
            updated_by=admin_user_id,
            file_path="test-page.md",
        )
        db.session.add(page)
        db.session.commit()

        # Create updated file
        file_path = os.path.join(temp_pages_dir, "test-page.md")
        content = """---
title: "Updated Title"
slug: "test-page"
---
# Updated Content

New content here.
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        # Wait and update file timestamp
        time.sleep(0.1)
        os.utime(file_path, None)

        synced_page, status = sync_utility.sync_file("test-page.md", force=True)

        assert status is False  # Updated
        assert synced_page.id == page.id
        assert synced_page.title == "Updated Title"
        assert "Updated Content" in synced_page.content


def test_sync_file_with_parent_slug(temp_pages_dir, app, sync_utility, admin_user_id):
    """Test syncing file with parent_slug"""
    with app.app_context():
        # Create parent page
        parent = Page(
            title="Parent",
            slug="parent-page",
            content="# Parent",
            created_by=admin_user_id,
            updated_by=admin_user_id,
            file_path="parent-page.md",
        )
        db.session.add(parent)
        db.session.commit()

        # Create child file
        file_path = os.path.join(temp_pages_dir, "child.md")
        content = """---
title: "Child Page"
slug: "child-page"
parent_slug: "parent-page"
---
# Child Page

Content.
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        page, status = sync_utility.sync_file("child.md")

        assert status is True
        assert page.parent_id == parent.id


def test_sync_file_skip_not_newer(temp_pages_dir, app, sync_utility, admin_user_id):
    """Test syncing skips file that's not newer"""
    with app.app_context():
        # Create page in database
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

        # Create file (older than DB) with matching slug
        file_path = os.path.join(temp_pages_dir, "test.md")
        content = """---
slug: "test"
---
# Test
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        old_time = (datetime.now(timezone.utc) - timedelta(hours=1)).timestamp()
        os.utime(file_path, (old_time, old_time))

        synced_page, status = sync_utility.sync_file("test.md", force=False)

        assert status is None  # Skipped
        assert synced_page.id == page.id
        assert synced_page.title == "Test"  # Unchanged


def test_sync_file_force_update(temp_pages_dir, app, sync_utility, admin_user_id):
    """Test force sync updates even if file is not newer"""
    with app.app_context():
        # Create page in database
        page = Page(
            title="Old",
            slug="test",
            content="# Old",
            section="Regression-Testing",
            created_by=admin_user_id,
            updated_by=admin_user_id,
            file_path="test.md",
            updated_at=datetime.now(timezone.utc),
        )
        db.session.add(page)
        db.session.commit()

        # Create file (older than DB)
        file_path = os.path.join(temp_pages_dir, "test.md")
        content = """---
title: "Forced Update"
slug: "test"
---
# Forced
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        old_time = (datetime.now(timezone.utc) - timedelta(hours=1)).timestamp()
        os.utime(file_path, (old_time, old_time))

        synced_page, status = sync_utility.sync_file("test.md", force=True)

        assert status is False  # Updated (forced)
        assert synced_page.title == "Forced Update"


def test_sync_file_auto_generate_slug(temp_pages_dir, app, sync_utility, admin_user_id):
    """Test syncing file without slug generates one from title"""
    with app.app_context():
        file_path = os.path.join(temp_pages_dir, "auto-slug.md")
        content = """---
title: "Auto Slug Page"
---
# Auto Slug Page

Content.
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        page, status = sync_utility.sync_file("auto-slug.md")

        assert status is True
        assert page.title == "Auto Slug Page"
        assert page.slug == "auto-slug-page"  # Generated from title


def test_sync_all(temp_pages_dir, app, sync_utility, admin_user_id):
    """Test syncing all files"""
    with app.app_context():
        # Create multiple test files
        os.makedirs(os.path.join(temp_pages_dir, "section1"), exist_ok=True)

        files_content = [
            ("page1.md", 'title: "Page 1"\nslug: "page-1"'),
            ("section1/page2.md", 'title: "Page 2"\nslug: "page-2"'),
            ("page3.md", 'title: "Page 3"\nslug: "page-3"'),
        ]

        for rel_path, frontmatter in files_content:
            full_path = os.path.join(temp_pages_dir, rel_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            content = f"---\n{frontmatter}\n---\n\n# Content"
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

        stats = sync_utility.sync_all()

        assert stats["total_files"] == 3
        assert stats["created"] == 3
        assert stats["updated"] == 0
        assert stats["errors"] == 0

        # Verify pages were created
        pages = db.session.query(Page).all()
        assert len(pages) == 3


def test_sync_directory(temp_pages_dir, app, sync_utility, admin_user_id):
    """Test syncing specific directory"""
    with app.app_context():
        # Create directory structure
        os.makedirs(os.path.join(temp_pages_dir, "section1"), exist_ok=True)
        os.makedirs(os.path.join(temp_pages_dir, "section2"), exist_ok=True)

        # Files in section1
        with open(
            os.path.join(temp_pages_dir, "section1", "page1.md"), "w", encoding="utf-8"
        ) as f:
            f.write('---\ntitle: "Page 1"\nslug: "page-1"\n---\n\n# Page 1')

        # Files in section2 (should not be synced)
        with open(
            os.path.join(temp_pages_dir, "section2", "page2.md"), "w", encoding="utf-8"
        ) as f:
            f.write('---\ntitle: "Page 2"\nslug: "page-2"\n---\n\n# Page 2')

        stats = sync_utility.sync_directory("section1")

        assert stats["total_files"] == 1
        assert stats["created"] == 1

        # Verify only section1 page was created
        pages = db.session.query(Page).all()
        assert len(pages) == 1
        assert pages[0].slug == "page-1"
