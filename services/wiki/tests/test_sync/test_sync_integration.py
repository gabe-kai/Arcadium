"""Tests for sync utility integration with LinkService and SearchIndexService"""

import os
import tempfile
import uuid

import pytest
from app import db
from app.models.index_entry import IndexEntry
from app.models.page import Page
from app.models.page_link import PageLink
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


def test_sync_file_updates_links(temp_pages_dir, app, sync_utility, admin_user_id):
    """Test syncing file updates link tracking"""
    with app.app_context():
        # Create target page
        target = Page(
            title="Target Page",
            slug="target-page",
            content="# Target",
            created_by=admin_user_id,
            updated_by=admin_user_id,
            file_path="target-page.md",
        )
        db.session.add(target)
        db.session.commit()

        # Create source file with link to target
        file_path = os.path.join(temp_pages_dir, "source.md")
        content = """---
title: "Source Page"
slug: "source-page"
---
# Source Page

See [Target Page](target-page) for more info.
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        page, status = sync_utility.sync_file("source.md")

        assert status is True

        # Verify link was created
        link = (
            db.session.query(PageLink)
            .filter_by(from_page_id=page.id, to_page_id=target.id)
            .first()
        )

        assert link is not None
        assert link.link_text == "Target Page"


def test_sync_file_updates_search_index(
    temp_pages_dir, app, sync_utility, admin_user_id
):
    """Test syncing file updates search index"""
    with app.app_context():
        file_path = os.path.join(temp_pages_dir, "indexed.md")
        content = """---
title: "Indexed Page"
slug: "indexed-page"
---
# Indexed Page

This page contains keywords: python, flask, wiki.
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        page, status = sync_utility.sync_file("indexed.md")

        assert status is True

        # Verify index entries were created
        index_entries = db.session.query(IndexEntry).filter_by(page_id=page.id).all()

        assert len(index_entries) > 0

        # Check for full-text entry
        fulltext_entries = [e for e in index_entries if not e.is_keyword]
        assert len(fulltext_entries) > 0

        # Check for keyword entries
        keyword_entries = [e for e in index_entries if e.is_keyword]
        assert len(keyword_entries) > 0


def test_sync_file_creates_version_on_update(
    temp_pages_dir, app, sync_utility, admin_user_id
):
    """Test syncing existing file creates version history"""
    with app.app_context():
        # Create page in database
        page = Page(
            title="Original",
            slug="versioned",
            content="# Original",
            created_by=admin_user_id,
            updated_by=admin_user_id,
            file_path="versioned.md",
        )
        db.session.add(page)
        db.session.commit()

        # Get initial version count (should be 0 for manually created page)
        from app.models.page_version import PageVersion

        initial_versions = (
            db.session.query(PageVersion).filter_by(page_id=page.id).all()
        )
        initial_count = len(initial_versions)

        # Create updated file
        file_path = os.path.join(temp_pages_dir, "versioned.md")
        content = """---
title: "Updated"
slug: "versioned"
---
# Updated Content
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        import time

        time.sleep(0.1)
        os.utime(file_path, None)

        synced_page, status = sync_utility.sync_file("versioned.md", force=True)

        assert status is False  # Updated

        # Verify version was created
        from app.models.page_version import PageVersion

        versions = db.session.query(PageVersion).filter_by(page_id=page.id).all()

        # Should have one more version than before
        assert len(versions) == initial_count + 1

        # Find the "Synced from file" version
        synced_version = next(
            (v for v in versions if v.change_summary == "Synced from file"), None
        )
        assert synced_version is not None
        assert synced_version.change_summary == "Synced from file"


def test_sync_file_no_version_on_create(
    temp_pages_dir, app, sync_utility, admin_user_id
):
    """Test syncing new file - PageService creates initial version, sync utility doesn't add another"""
    with app.app_context():
        file_path = os.path.join(temp_pages_dir, "new.md")
        content = """---
title: "New Page"
slug: "new-page"
---
# New
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        page, status = sync_utility.sync_file("new.md")

        assert status is True  # Created

        # PageService.create_page creates an initial version, but sync utility
        # doesn't create an additional "Synced from file" version for new pages
        from app.models.page_version import PageVersion

        versions = db.session.query(PageVersion).filter_by(page_id=page.id).all()

        # Should have initial version from PageService, but not "Synced from file" version
        assert len(versions) >= 1  # At least initial version
        # Verify no "Synced from file" version was added by sync utility
        synced_versions = [
            v for v in versions if v.change_summary == "Synced from file"
        ]
        assert len(synced_versions) == 0


def test_sync_file_with_multiple_links(
    temp_pages_dir, app, sync_utility, admin_user_id
):
    """Test syncing file with multiple internal links"""
    with app.app_context():
        # Create target pages
        target1 = Page(
            title="Target 1",
            slug="target-1",
            content="# Target 1",
            created_by=admin_user_id,
            updated_by=admin_user_id,
            file_path="target-1.md",
        )
        target2 = Page(
            title="Target 2",
            slug="target-2",
            content="# Target 2",
            created_by=admin_user_id,
            updated_by=admin_user_id,
            file_path="target-2.md",
        )
        db.session.add_all([target1, target2])
        db.session.commit()

        # Create source file with multiple links
        file_path = os.path.join(temp_pages_dir, "multi-link.md")
        content = """---
title: "Multi Link Page"
slug: "multi-link"
---
# Multi Link Page

See [Target 1](target-1) and [Target 2](target-2).
Also check [[target-1]] and [[target-2]].
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        page, status = sync_utility.sync_file("multi-link.md")

        assert status is True

        # Verify all links were created
        links = db.session.query(PageLink).filter_by(from_page_id=page.id).all()

        assert len(links) >= 2

        # Check both targets are linked
        target_ids = {link.to_page_id for link in links}
        assert target1.id in target_ids
        assert target2.id in target_ids
