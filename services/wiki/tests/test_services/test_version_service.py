"""Test version service"""

import uuid

from app.services.page_service import PageService
from app.services.version_service import VersionService


def test_create_version(app):
    """Test creating a version"""
    with app.app_context():
        user_id = uuid.uuid4()

        # Create a page (PageService automatically creates version 1)
        page = PageService.create_page(
            title="Test Page",
            content="Original content",
            user_id=user_id,
            slug="test-page",
            section="Regression-Testing",
        )

        # PageService already created version 1, so next version should be 2
        # Create another version
        version = VersionService.create_version(
            page_id=page.id, user_id=user_id, change_summary="Second version"
        )

        assert version is not None
        assert version.page_id == page.id
        assert version.version == 2  # Second version (first was created by PageService)
        assert version.title == "Test Page"
        assert version.content == "Original content"
        assert version.changed_by == user_id
        assert version.change_summary == "Second version"


def test_create_multiple_versions(app):
    """Test creating multiple versions"""
    with app.app_context():
        user_id = uuid.uuid4()

        # Create a page (PageService automatically creates version 1)
        page = PageService.create_page(
            title="Test Page",
            content="Version 1",
            user_id=user_id,
            slug="test-page",
            section="Regression-Testing",
        )

        # PageService already created version 1, so next is version 2
        version2 = VersionService.create_version(page_id=page.id, user_id=user_id)
        assert version2.version == 2

        # Update page (PageService creates version 3)
        PageService.update_page(page_id=page.id, user_id=user_id, content="Version 2")

        # Create another version manually
        version4 = VersionService.create_version(page_id=page.id, user_id=user_id)
        assert version4.version == 4

        # Update page again (PageService creates version 5)
        PageService.update_page(page_id=page.id, user_id=user_id, content="Version 3")

        # Verify we have 5 versions total
        count = VersionService.get_version_count(page.id)
        assert count == 5


def test_get_version(app):
    """Test getting a specific version"""
    with app.app_context():
        user_id = uuid.uuid4()

        # Create a page (PageService creates version 1)
        page = PageService.create_page(
            title="Test Page",
            content="Version 1",
            user_id=user_id,
            slug="test-page",
            section="Regression-Testing",
        )

        # Update page (PageService creates version 2)
        PageService.update_page(page_id=page.id, user_id=user_id, content="Version 2")

        # Get version 1
        version1 = VersionService.get_version(page.id, 1)
        assert version1 is not None
        assert version1.content == "Version 1"

        # Get version 2
        version2 = VersionService.get_version(page.id, 2)
        assert version2 is not None
        assert version2.content == "Version 2"


def test_get_all_versions(app):
    """Test getting all versions"""
    with app.app_context():
        user_id = uuid.uuid4()

        # Create a page (PageService creates version 1)
        page = PageService.create_page(
            title="Test Page",
            content="Version 1",
            user_id=user_id,
            slug="test-page",
            section="Regression-Testing",
        )

        # Update page multiple times (PageService creates versions automatically)
        PageService.update_page(page_id=page.id, user_id=user_id, content="Version 2")
        PageService.update_page(page_id=page.id, user_id=user_id, content="Version 3")

        # Get all versions
        versions = VersionService.get_all_versions(page.id)

        assert len(versions) == 3
        # Should be ordered newest first
        assert versions[0].version == 3
        assert versions[1].version == 2
        assert versions[2].version == 1


def test_get_latest_version(app):
    """Test getting the latest version"""
    with app.app_context():
        user_id = uuid.uuid4()

        # Create a page (PageService creates version 1)
        page = PageService.create_page(
            title="Test Page",
            content="Version 1",
            user_id=user_id,
            slug="test-page",
            section="Regression-Testing",
        )

        # Update page (PageService creates versions automatically)
        PageService.update_page(page_id=page.id, user_id=user_id, content="Version 2")
        PageService.update_page(page_id=page.id, user_id=user_id, content="Version 3")

        # Get latest version
        latest = VersionService.get_latest_version(page.id)
        assert latest is not None
        assert latest.version == 3
        assert latest.content == "Version 3"


def test_calculate_diff(app):
    """Test diff calculation"""
    with app.app_context():
        user_id = uuid.uuid4()

        # Create a page (PageService creates version 1)
        page = PageService.create_page(
            title="Test Page",
            content="Line 1\nLine 2\nLine 3",
            user_id=user_id,
            slug="test-page",
        )

        # Update page (PageService creates version 2 with diff)
        PageService.update_page(
            page_id=page.id,
            user_id=user_id,
            content="Line 1\nLine 2 Modified\nLine 3\nLine 4",
        )

        # Get version 2 (should have diff)
        version2 = VersionService.get_version(page.id, 2)

        assert version2 is not None
        assert version2.diff_data is not None
        assert (
            "lines_added" in version2.diff_data or "added_lines" in version2.diff_data
        )
        assert (
            "lines_removed" in version2.diff_data
            or "removed_lines" in version2.diff_data
        )
        # Check that there were changes
        added = version2.diff_data.get(
            "lines_added", version2.diff_data.get("added_lines", 0)
        )
        removed = version2.diff_data.get(
            "lines_removed", version2.diff_data.get("removed_lines", 0)
        )
        assert added > 0 or removed > 0


def test_compare_versions(app):
    """Test comparing two versions"""
    with app.app_context():
        user_id = uuid.uuid4()

        # Create a page (PageService creates version 1)
        page = PageService.create_page(
            title="Test Page",
            content="Version 1 content",
            user_id=user_id,
            slug="test-page",
            section="Regression-Testing",
        )

        # Update page (PageService creates version 2)
        PageService.update_page(
            page_id=page.id, user_id=user_id, content="Version 2 content"
        )

        # Compare versions
        comparison = VersionService.compare_versions(page.id, 1, 2)

        assert comparison is not None
        assert "version1" in comparison
        assert "version2" in comparison
        assert "diff" in comparison
        assert comparison["version1"]["content"] == "Version 1 content"
        assert comparison["version2"]["content"] == "Version 2 content"


def test_rollback_to_version_admin(app):
    """Test rollback by admin"""
    with app.app_context():
        user_id = uuid.uuid4()
        admin_id = uuid.uuid4()

        # Create a page (PageService creates version 1)
        page = PageService.create_page(
            title="Test Page",
            content="Version 1",
            user_id=user_id,
            slug="test-page",
            section="Regression-Testing",
        )

        # Update page (PageService creates versions automatically)
        PageService.update_page(page_id=page.id, user_id=user_id, content="Version 2")
        PageService.update_page(page_id=page.id, user_id=user_id, content="Version 3")

        # Rollback to version 1 as admin
        rolled_back = VersionService.rollback_to_version(
            page_id=page.id, version=1, user_id=admin_id, user_role="admin"
        )

        assert rolled_back.content == "Version 1"

        # Should have created new versions (pre-rollback snapshot + rollback version)
        versions = VersionService.get_all_versions(page.id)
        assert len(versions) >= 5  # Original 3 + pre-rollback + rollback


def test_rollback_to_version_writer_own_page(app):
    """Test rollback by writer on their own page"""
    with app.app_context():
        writer_id = uuid.uuid4()

        # Create a page (PageService creates version 1)
        page = PageService.create_page(
            title="Test Page",
            content="Version 1",
            user_id=writer_id,
            slug="test-page",
            section="Regression-Testing",
        )

        # Update page (PageService creates version 2)
        PageService.update_page(page_id=page.id, user_id=writer_id, content="Version 2")

        # Rollback to version 1 as writer (own page)
        rolled_back = VersionService.rollback_to_version(
            page_id=page.id, version=1, user_id=writer_id, user_role="writer"
        )

        assert rolled_back.content == "Version 1"


def test_rollback_to_version_writer_other_page(app):
    """Test rollback by writer on someone else's page (should fail)"""
    with app.app_context():
        user_id = uuid.uuid4()
        writer_id = uuid.uuid4()

        # Create a page (PageService creates version 1)
        page = PageService.create_page(
            title="Test Page",
            content="Version 1",
            user_id=user_id,
            slug="test-page",
            section="Regression-Testing",
        )

        # Try to rollback as different writer (should fail)
        import pytest

        with pytest.raises(PermissionError):
            VersionService.rollback_to_version(
                page_id=page.id, version=1, user_id=writer_id, user_role="writer"
            )


def test_rollback_to_version_viewer(app):
    """Test rollback by viewer (should fail)"""
    with app.app_context():
        user_id = uuid.uuid4()
        viewer_id = uuid.uuid4()

        # Create a page (PageService creates version 1)
        page = PageService.create_page(
            title="Test Page",
            content="Version 1",
            user_id=user_id,
            slug="test-page",
            section="Regression-Testing",
        )

        # Try to rollback as viewer (should fail)
        import pytest

        with pytest.raises(PermissionError):
            VersionService.rollback_to_version(
                page_id=page.id, version=1, user_id=viewer_id, user_role="viewer"
            )


def test_get_version_history_summary(app):
    """Test getting version history summary"""
    with app.app_context():
        user_id = uuid.uuid4()

        # Create a page (PageService creates version 1 with default summary)
        page = PageService.create_page(
            title="Test Page",
            content="Version 1",
            user_id=user_id,
            slug="test-page",
            section="Regression-Testing",
        )

        # Update page (PageService creates version 2)
        PageService.update_page(page_id=page.id, user_id=user_id, content="Version 2")

        # Get summary
        summary = VersionService.get_version_history_summary(page.id)

        assert len(summary) == 2
        assert summary[0]["version"] == 2  # Newest first
        assert summary[1]["version"] == 1


def test_get_version_count(app):
    """Test getting version count"""
    with app.app_context():
        user_id = uuid.uuid4()

        # Create a page (PageService creates version 1)
        page = PageService.create_page(
            title="Test Page",
            content="Version 1",
            user_id=user_id,
            slug="test-page",
            section="Regression-Testing",
        )

        # Update page (PageService creates versions automatically)
        PageService.update_page(page_id=page.id, user_id=user_id, content="Version 2")
        PageService.update_page(page_id=page.id, user_id=user_id, content="Version 3")

        # Get count
        count = VersionService.get_version_count(page.id)
        assert count == 3


def test_version_retention(app):
    """Test that all versions are kept indefinitely"""
    with app.app_context():
        user_id = uuid.uuid4()

        # Create a page (PageService creates version 1)
        page = PageService.create_page(
            title="Test Page",
            content="Version 1",
            user_id=user_id,
            slug="test-page",
            section="Regression-Testing",
        )

        # Create many versions by updating the page
        for i in range(9):  # 9 more updates = 10 total versions
            PageService.update_page(
                page_id=page.id, user_id=user_id, content=f"Version {i+2}"
            )

        # All versions should still exist
        count = VersionService.get_version_count(page.id)
        assert count == 10

        # Should be able to access any version
        version1 = VersionService.get_version(page.id, 1)
        version5 = VersionService.get_version(page.id, 5)
        version10 = VersionService.get_version(page.id, 10)

        assert version1 is not None
        assert version5 is not None
        assert version10 is not None
