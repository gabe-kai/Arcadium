"""Additional tests for version history API endpoints - edge cases and validation"""

from app import db
from app.models.page import Page
from app.models.page_version import PageVersion
from app.services.version_service import VersionService
from tests.test_api.conftest import auth_headers, mock_auth


def test_get_version_history_ordering(client, app, test_user_id):
    """Test that version history is ordered newest first"""
    with app.app_context():
        page = Page(
            title="Test Page",
            slug="test-page",
            content="# Test",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            file_path="test-page.md",
        )
        db.session.add(page)
        db.session.flush()

        # Create versions in order
        for i in range(1, 6):
            version = PageVersion(
                page_id=page.id,
                version=i,
                title="Test Page",
                content=f"# Version {i}",
                changed_by=test_user_id,
                change_summary=f"Version {i}",
            )
            db.session.add(version)
        db.session.commit()
        page_id = str(page.id)

    response = client.get(f"/api/pages/{page_id}/versions")
    assert response.status_code == 200
    data = response.get_json()
    versions = data["versions"]

    # Should be ordered newest first (5, 4, 3, 2, 1)
    assert len(versions) == 5
    assert versions[0]["version"] == 5
    assert versions[4]["version"] == 1


def test_get_version_history_with_diff_stats(client, app, test_user_id):
    """Test version history includes diff statistics"""
    with app.app_context():
        page = Page(
            title="Test Page",
            slug="test-page",
            content="# Test",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            file_path="test-page.md",
        )
        db.session.add(page)
        db.session.flush()

        version = PageVersion(
            page_id=page.id,
            version=1,
            title="Test Page",
            content="# Test",
            changed_by=test_user_id,
            diff_data={"added_lines": 10, "removed_lines": 5, "char_diff": 50},
        )
        db.session.add(version)
        db.session.commit()
        page_id = str(page.id)

    response = client.get(f"/api/pages/{page_id}/versions")
    assert response.status_code == 200
    data = response.get_json()
    version_data = data["versions"][0]

    assert "diff_stats" in version_data
    assert version_data["diff_stats"]["added_lines"] == 10
    assert version_data["diff_stats"]["removed_lines"] == 5
    assert version_data["diff_stats"]["char_diff"] == 50


def test_get_version_history_without_diff_stats(client, app, test_user_id):
    """Test version history handles missing diff data gracefully"""
    with app.app_context():
        page = Page(
            title="Test Page",
            slug="test-page",
            content="# Test",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            file_path="test-page.md",
        )
        db.session.add(page)
        db.session.flush()

        version = PageVersion(
            page_id=page.id,
            version=1,
            title="Test Page",
            content="# Test",
            changed_by=test_user_id,
            diff_data=None,
        )
        db.session.add(version)
        db.session.commit()
        page_id = str(page.id)

    response = client.get(f"/api/pages/{page_id}/versions")
    assert response.status_code == 200
    data = response.get_json()
    version_data = data["versions"][0]

    assert "diff_stats" in version_data
    assert version_data["diff_stats"]["added_lines"] == 0
    assert version_data["diff_stats"]["removed_lines"] == 0
    assert version_data["diff_stats"]["char_diff"] == 0


def test_get_specific_version_html_content(client, app, test_user_id):
    """Test that specific version includes HTML content"""
    with app.app_context():
        page = Page(
            title="Test Page",
            slug="test-page",
            content="# Test",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            file_path="test-page.md",
        )
        db.session.add(page)
        db.session.flush()

        version = PageVersion(
            page_id=page.id,
            version=1,
            title="Test Page",
            content="# Test Heading\n\nSome **bold** text.",
            changed_by=test_user_id,
        )
        db.session.add(version)
        db.session.commit()
        page_id = str(page.id)

    response = client.get(f"/api/pages/{page_id}/versions/1")
    assert response.status_code == 200
    data = response.get_json()
    assert "html_content" in data
    assert "<h1>" in data["html_content"] or "Test Heading" in data["html_content"]


def test_compare_versions_same_version(client, app, test_user_id):
    """Test comparing a version to itself"""
    with app.app_context():
        page = Page(
            title="Test Page",
            slug="test-page",
            content="# Test",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            file_path="test-page.md",
        )
        db.session.add(page)
        db.session.flush()

        version = PageVersion(
            page_id=page.id,
            version=1,
            title="Test Page",
            content="# Test",
            changed_by=test_user_id,
        )
        db.session.add(version)
        db.session.commit()
        page_id = str(page.id)

    response = client.get(f"/api/pages/{page_id}/versions/compare?from=1&to=1")
    assert response.status_code == 200
    data = response.get_json()
    assert "diff" in data
    # Should have no changes
    assert data["diff"]["added_lines"] == 0
    assert data["diff"]["removed_lines"] == 0


def test_compare_versions_reversed_order(client, app, test_user_id):
    """Test comparing versions in reverse order (newer to older)"""
    with app.app_context():
        page = Page(
            title="Test Page",
            slug="test-page",
            content="# Test",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            file_path="test-page.md",
        )
        db.session.add(page)
        db.session.flush()

        version1 = PageVersion(
            page_id=page.id,
            version=1,
            title="Test Page",
            content="# Old",
            changed_by=test_user_id,
        )
        version2 = PageVersion(
            page_id=page.id,
            version=2,
            title="Test Page",
            content="# New",
            changed_by=test_user_id,
        )
        db.session.add(version1)
        db.session.add(version2)
        db.session.commit()
        page_id = str(page.id)

    # Compare newer to older (2 to 1)
    response = client.get(f"/api/pages/{page_id}/versions/compare?from=2&to=1")
    assert response.status_code == 200
    data = response.get_json()
    assert data["from_version"] == 2
    assert data["to_version"] == 1
    assert "diff" in data


def test_restore_version_creates_new_version(client, app, test_user_id):
    """Test that restoring a version creates a new version entry"""
    with app.app_context():
        page = Page(
            title="Test Page",
            slug="test-page",
            content="# Current",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            file_path="test-page.md",
        )
        db.session.add(page)
        db.session.flush()

        version = PageVersion(
            page_id=page.id,
            version=1,
            title="Test Page",
            content="# Old",
            changed_by=test_user_id,
        )
        db.session.add(version)
        db.session.commit()
        page_id = str(page.id)

        # Count versions before restore
        initial_count = VersionService.get_version_count(page.id)

    with mock_auth(test_user_id, "writer"):
        response = client.post(
            f"/api/pages/{page_id}/versions/1/restore",
            headers=auth_headers(test_user_id, "writer"),
        )
        assert response.status_code == 200

    # Verify new versions were created (pre-rollback snapshot + rollback version)
    with app.app_context():
        final_count = VersionService.get_version_count(page.id)
        # Should have at least 2 more versions (pre-rollback + rollback)
        assert final_count >= initial_count + 2


def test_restore_version_updates_page_content(client, app, test_user_id):
    """Test that restoring a version updates the page content"""
    with app.app_context():
        page = Page(
            title="Test Page",
            slug="test-page",
            content="# Current Content",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            file_path="test-page.md",
        )
        db.session.add(page)
        db.session.flush()

        old_content = "# Old Content"
        version = PageVersion(
            page_id=page.id,
            version=1,
            title="Test Page",
            content=old_content,
            changed_by=test_user_id,
        )
        db.session.add(version)
        db.session.commit()
        page_id = str(page.id)

    with mock_auth(test_user_id, "writer"):
        response = client.post(
            f"/api/pages/{page_id}/versions/1/restore",
            headers=auth_headers(test_user_id, "writer"),
        )
        assert response.status_code == 200

    # Verify page content was updated
    with app.app_context():
        updated_page = db.session.get(Page, page_id)
        assert updated_page.content == old_content


def test_restore_version_response_structure(client, app, test_user_id):
    """Test that restore response matches API spec structure"""
    with app.app_context():
        page = Page(
            title="Test Page",
            slug="test-page",
            content="# Current",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            file_path="test-page.md",
        )
        db.session.add(page)
        db.session.flush()

        version = PageVersion(
            page_id=page.id,
            version=1,
            title="Test Page",
            content="# Old",
            changed_by=test_user_id,
        )
        db.session.add(version)
        db.session.commit()
        page_id = str(page.id)

    with mock_auth(test_user_id, "writer"):
        response = client.post(
            f"/api/pages/{page_id}/versions/1/restore",
            headers=auth_headers(test_user_id, "writer"),
        )
        assert response.status_code == 200
        data = response.get_json()

        assert "message" in data
        assert "new_version" in data
        assert "page" in data
        assert "id" in data["page"]
        assert "title" in data["page"]
        assert "version" in data["page"]


def test_get_version_history_large_list(client, app, test_user_id):
    """Test version history with many versions"""
    with app.app_context():
        page = Page(
            title="Test Page",
            slug="test-page",
            content="# Test",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            file_path="test-page.md",
        )
        db.session.add(page)
        db.session.flush()

        # Create 20 versions
        for i in range(1, 21):
            version = PageVersion(
                page_id=page.id,
                version=i,
                title="Test Page",
                content=f"# Version {i}",
                changed_by=test_user_id,
            )
            db.session.add(version)
        db.session.commit()
        page_id = str(page.id)

    response = client.get(f"/api/pages/{page_id}/versions")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data["versions"]) == 20
    # Should be ordered newest first
    assert data["versions"][0]["version"] == 20
    assert data["versions"][19]["version"] == 1
