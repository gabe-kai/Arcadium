"""Tests for sync utility error handling and edge cases"""

import os
import tempfile
import uuid

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


def test_read_file_not_found(temp_pages_dir, app, sync_utility):
    """Test reading non-existent file raises FileNotFoundError"""
    with app.app_context():
        with pytest.raises(FileNotFoundError):
            sync_utility.read_file("nonexistent.md")


def test_read_file_malformed_yaml(temp_pages_dir, app, sync_utility):
    """Test reading file with malformed YAML frontmatter"""
    with app.app_context():
        file_path = os.path.join(temp_pages_dir, "malformed.md")
        content = """---
title: "Test"
slug: "test"
invalid: [unclosed
---
# Content
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        # Should not raise, but return empty frontmatter
        frontmatter, markdown = sync_utility.read_file("malformed.md")

        # Malformed YAML should result in empty frontmatter (graceful fallback)
        assert frontmatter == {} or "title" not in frontmatter
        assert "# Content" in markdown


def test_sync_file_missing_file(temp_pages_dir, app, sync_utility):
    """Test syncing non-existent file raises FileNotFoundError"""
    with app.app_context():
        with pytest.raises(FileNotFoundError):
            sync_utility.sync_file("nonexistent.md")


def test_sync_file_invalid_slug(temp_pages_dir, app, sync_utility, admin_user_id):
    """Test syncing file with invalid slug"""
    with app.app_context():
        file_path = os.path.join(temp_pages_dir, "invalid.md")
        content = """---
title: "Test"
slug: "invalid slug with spaces"
---
# Test
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        # Should raise ValueError from PageService
        with pytest.raises(ValueError, match="Invalid slug"):
            sync_utility.sync_file("invalid.md")


def test_sync_file_duplicate_slug(temp_pages_dir, app, sync_utility, admin_user_id):
    """Test syncing file with duplicate slug"""
    with app.app_context():
        # Create existing page
        existing = Page(
            title="Existing",
            slug="duplicate-slug",
            content="# Existing",
            section="Regression-Testing",
            created_by=admin_user_id,
            updated_by=admin_user_id,
            file_path="existing.md",
        )
        db.session.add(existing)
        db.session.commit()

        # Try to sync file with same slug but different title
        file_path = os.path.join(temp_pages_dir, "duplicate.md")
        content = """---
title: "New Title"
slug: "duplicate-slug"
---
# New
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        # Should update existing page, not create new one
        page, status = sync_utility.sync_file("duplicate.md", force=True)

        assert status is False  # Updated
        assert page.id == existing.id
        assert page.title == "New Title"


def test_sync_file_missing_title(temp_pages_dir, app, sync_utility, admin_user_id):
    """Test syncing file without title generates one"""
    with app.app_context():
        file_path = os.path.join(temp_pages_dir, "no-title.md")
        content = """---
slug: "no-title"
---
# Content without title in frontmatter
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        # Should use "Untitled" as default title
        page, status = sync_utility.sync_file("no-title.md")

        assert status is True
        assert page.title == "Untitled"
        assert page.slug == "no-title"


def test_sync_file_parent_slug_not_found(
    temp_pages_dir, app, sync_utility, admin_user_id
):
    """Test syncing file with parent_slug that doesn't exist"""
    with app.app_context():
        file_path = os.path.join(temp_pages_dir, "orphan.md")
        content = """---
title: "Orphan Page"
slug: "orphan-page"
parent_slug: "nonexistent-parent"
---
# Orphan
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        # Should create page with parent_id=None (graceful handling)
        page, status = sync_utility.sync_file("orphan.md")

        assert status is True
        assert page.parent_id is None


def test_sync_all_handles_errors(temp_pages_dir, app, sync_utility, admin_user_id):
    """Test sync_all handles errors gracefully"""
    with app.app_context():
        # Create mix of valid and invalid files
        os.makedirs(os.path.join(temp_pages_dir, "section"), exist_ok=True)

        # Valid file
        with open(os.path.join(temp_pages_dir, "valid.md"), "w", encoding="utf-8") as f:
            f.write('---\ntitle: "Valid"\nslug: "valid"\n---\n\n# Valid')

        # Invalid file (missing slug, will generate one)
        with open(
            os.path.join(temp_pages_dir, "no-slug.md"), "w", encoding="utf-8"
        ) as f:
            f.write('---\ntitle: "No Slug"\n---\n\n# No Slug')

        # File that will cause error (invalid slug format)
        with open(
            os.path.join(temp_pages_dir, "bad-slug.md"), "w", encoding="utf-8"
        ) as f:
            f.write('---\ntitle: "Bad"\nslug: "bad slug"\n---\n\n# Bad')

        stats = sync_utility.sync_all()

        # Should have processed valid files and recorded errors
        assert stats["total_files"] == 3
        assert stats["created"] >= 1  # At least valid.md was created
        assert stats["errors"] >= 1  # bad-slug.md should cause error


def test_sync_directory_invalid_directory(temp_pages_dir, app, sync_utility):
    """Test syncing invalid directory raises ValueError"""
    with app.app_context():
        with pytest.raises(ValueError, match="Directory not found"):
            sync_utility.sync_directory("nonexistent-section")


def test_sync_directory_empty_directory(temp_pages_dir, app, sync_utility):
    """Test syncing empty directory"""
    with app.app_context():
        os.makedirs(os.path.join(temp_pages_dir, "empty-section"), exist_ok=True)

        stats = sync_utility.sync_directory("empty-section")

        assert stats["total_files"] == 0
        assert stats["created"] == 0
        assert stats["updated"] == 0
        assert stats["errors"] == 0


def test_sync_directory_nested_subdirectories(
    temp_pages_dir, app, sync_utility, admin_user_id
):
    """Test syncing directory includes nested subdirectories"""
    with app.app_context():
        # Create nested structure
        os.makedirs(
            os.path.join(temp_pages_dir, "section1", "subsection"), exist_ok=True
        )

        # File in section1 root
        with open(
            os.path.join(temp_pages_dir, "section1", "root.md"), "w", encoding="utf-8"
        ) as f:
            f.write('---\ntitle: "Root"\nslug: "root"\n---\n\n# Root')

        # File in nested subsection
        with open(
            os.path.join(temp_pages_dir, "section1", "subsection", "nested.md"),
            "w",
            encoding="utf-8",
        ) as f:
            f.write('---\ntitle: "Nested"\nslug: "nested"\n---\n\n# Nested')

        stats = sync_utility.sync_directory("section1")

        assert stats["total_files"] == 2
        assert stats["created"] == 2


def test_sync_file_idempotence(temp_pages_dir, app, sync_utility, admin_user_id):
    """Test syncing same file twice without changes is idempotent"""
    with app.app_context():
        file_path = os.path.join(temp_pages_dir, "idempotent.md")
        content = """---
title: "Idempotent"
slug: "idempotent"
---
# Idempotent
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        # First sync - creates page
        page1, status1 = sync_utility.sync_file("idempotent.md")
        assert status1 is True

        # Second sync without file changes - should skip
        page2, status2 = sync_utility.sync_file("idempotent.md", force=False)
        assert status2 is None  # Skipped

        # Third sync with force - should update
        page3, status3 = sync_utility.sync_file("idempotent.md", force=True)
        assert status3 is False  # Updated

        # All should reference same page
        assert page1.id == page2.id == page3.id


def test_sync_all_idempotence(temp_pages_dir, app, sync_utility, admin_user_id):
    """Test sync_all is idempotent when files haven't changed"""
    with app.app_context():
        # Create files
        files_content = [
            ("page1.md", 'title: "Page 1"\nslug: "page-1"'),
            ("page2.md", 'title: "Page 2"\nslug: "page-2"'),
        ]

        for filename, frontmatter in files_content:
            full_path = os.path.join(temp_pages_dir, filename)
            content = f"---\n{frontmatter}\n---\n\n# Content"
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

        # First sync - creates pages
        stats1 = sync_utility.sync_all()
        assert stats1["created"] == 2
        assert stats1["updated"] == 0
        assert stats1["skipped"] == 0

        # Second sync without changes - should skip all
        # Note: total_files might include files created by PageService, so we just check
        # that our original files were skipped
        stats2 = sync_utility.sync_all()
        assert stats2["created"] == 0
        assert stats2["updated"] == 0
        # The two files we created should be skipped (file not newer than DB)
        assert stats2["skipped"] >= 2  # At least our 2 files should be skipped


def test_admin_user_id_from_config(app, admin_user_id):
    """Test admin user ID can be set from config"""
    with app.app_context():
        # Set config
        app.config["SYNC_ADMIN_USER_ID"] = str(admin_user_id)

        sync = SyncUtility()
        assert sync.admin_user_id == admin_user_id


def test_admin_user_id_invalid_config_falls_back(app):
    """Test invalid admin user ID in config falls back to default"""
    with app.app_context():
        # Set invalid config
        app.config["SYNC_ADMIN_USER_ID"] = "not-a-uuid"

        sync = SyncUtility()
        # Should fall back to default admin ID
        assert sync.admin_user_id is not None
        assert isinstance(sync.admin_user_id, uuid.UUID)


def test_admin_user_id_explicit_override(app, admin_user_id):
    """Test explicitly passing admin_user_id overrides config"""
    with app.app_context():
        different_id = uuid.uuid4()
        app.config["SYNC_ADMIN_USER_ID"] = str(admin_user_id)

        sync = SyncUtility(admin_user_id=different_id)
        assert sync.admin_user_id == different_id
