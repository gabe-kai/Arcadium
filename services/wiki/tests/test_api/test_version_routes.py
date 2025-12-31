"""Tests for version history API endpoints"""

import uuid

from app import db
from app.models.page import Page
from app.models.page_version import PageVersion
from tests.test_api.conftest import auth_headers, mock_auth


def test_get_version_history_empty(client, app, test_user_id):
    """Test getting version history for page with no versions"""
    with app.app_context():
        page = Page(
            title="New Page",
            slug="new-page",
            content="# New Page",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            file_path="new-page.md",
        )
        db.session.add(page)
        db.session.commit()
        page_id = str(page.id)

    response = client.get(f"/api/pages/{page_id}/versions")
    assert response.status_code == 200
    data = response.get_json()
    assert "versions" in data
    assert len(data["versions"]) == 0


def test_get_version_history_with_versions(client, app, test_user_id):
    """Test getting version history for page with versions"""
    with app.app_context():
        page = Page(
            title="Test Page",
            slug="test-page",
            content="# Test",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            file_path="test-page.md",
        )
        db.session.add(page)
        db.session.flush()

        # Create versions
        version1 = PageVersion(
            page_id=page.id,
            version=1,
            title="Test Page",
            content="# Test v1",
            changed_by=test_user_id,
            change_summary="Initial version",
        )
        version2 = PageVersion(
            page_id=page.id,
            version=2,
            title="Test Page",
            content="# Test v2",
            changed_by=test_user_id,
            change_summary="Updated content",
        )
        db.session.add(version1)
        db.session.add(version2)
        db.session.commit()
        page_id = str(page.id)

    response = client.get(f"/api/pages/{page_id}/versions")
    assert response.status_code == 200
    data = response.get_json()
    assert "versions" in data
    assert len(data["versions"]) == 2
    # Should be ordered newest first
    assert data["versions"][0]["version"] == 2
    assert data["versions"][1]["version"] == 1


def test_get_version_history_response_structure(client, app, test_user_id):
    """Test that version history response matches API spec structure"""
    with app.app_context():
        page = Page(
            title="Test Page",
            slug="test-page",
            content="# Test",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
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
            change_summary="Initial version",
            diff_data={"added_lines": 5, "removed_lines": 0, "char_diff": 10},
        )
        db.session.add(version)
        db.session.commit()
        page_id = str(page.id)

    response = client.get(f"/api/pages/{page_id}/versions")
    assert response.status_code == 200
    data = response.get_json()
    assert "versions" in data
    assert len(data["versions"]) == 1

    version_data = data["versions"][0]
    assert "version" in version_data
    assert "title" in version_data
    assert "changed_by" in version_data
    assert "change_summary" in version_data
    assert "created_at" in version_data
    assert "diff_stats" in version_data
    assert "added_lines" in version_data["diff_stats"]
    assert "removed_lines" in version_data["diff_stats"]


def test_get_version_history_page_not_found(client):
    """Test getting version history for non-existent page"""
    fake_id = str(uuid.uuid4())
    response = client.get(f"/api/pages/{fake_id}/versions")
    assert response.status_code == 404
    data = response.get_json()
    assert "error" in data


def test_get_specific_version(client, app, test_user_id):
    """Test getting a specific version"""
    with app.app_context():
        page = Page(
            title="Test Page",
            slug="test-page",
            content="# Test",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            file_path="test-page.md",
        )
        db.session.add(page)
        db.session.flush()

        version = PageVersion(
            page_id=page.id,
            version=1,
            title="Test Page",
            content="# Test Content",
            changed_by=test_user_id,
            change_summary="Initial version",
        )
        db.session.add(version)
        db.session.commit()
        page_id = str(page.id)

    response = client.get(f"/api/pages/{page_id}/versions/1")
    assert response.status_code == 200
    data = response.get_json()
    assert data["version"] == 1
    assert data["title"] == "Test Page"
    assert data["content"] == "# Test Content"
    assert "html_content" in data
    assert "changed_by" in data
    assert "created_at" in data


def test_get_specific_version_not_found(client, app, test_user_id):
    """Test getting non-existent version"""
    with app.app_context():
        page = Page(
            title="Test Page",
            slug="test-page",
            content="# Test",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            file_path="test-page.md",
        )
        db.session.add(page)
        db.session.commit()
        page_id = str(page.id)

    response = client.get(f"/api/pages/{page_id}/versions/999")
    assert response.status_code == 404
    data = response.get_json()
    assert "error" in data


def test_get_specific_version_page_not_found(client):
    """Test getting version for non-existent page"""
    fake_id = str(uuid.uuid4())
    response = client.get(f"/api/pages/{fake_id}/versions/1")
    assert response.status_code == 404
    data = response.get_json()
    assert "error" in data


def test_compare_versions(client, app, test_user_id):
    """Test comparing two versions"""
    with app.app_context():
        page = Page(
            title="Test Page",
            slug="test-page",
            content="# Test",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            file_path="test-page.md",
        )
        db.session.add(page)
        db.session.flush()

        version1 = PageVersion(
            page_id=page.id,
            version=1,
            title="Test Page",
            content="# Old Content",
            changed_by=test_user_id,
        )
        version2 = PageVersion(
            page_id=page.id,
            version=2,
            title="Test Page",
            content="# New Content",
            changed_by=test_user_id,
        )
        db.session.add(version1)
        db.session.add(version2)
        db.session.commit()
        page_id = str(page.id)

    response = client.get(f"/api/pages/{page_id}/versions/compare?from=1&to=2")
    assert response.status_code == 200
    data = response.get_json()
    assert "from_version" in data
    assert "to_version" in data
    assert data["from_version"] == 1
    assert data["to_version"] == 2
    assert "version1" in data
    assert "version2" in data
    assert "diff" in data


def test_compare_versions_missing_params(client, app, test_user_id):
    """Test comparing versions with missing parameters"""
    with app.app_context():
        page = Page(
            title="Test Page",
            slug="test-page",
            content="# Test",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            file_path="test-page.md",
        )
        db.session.add(page)
        db.session.commit()
        page_id = str(page.id)

    # Missing 'from' parameter
    response = client.get(f"/api/pages/{page_id}/versions/compare?to=2")
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data

    # Missing 'to' parameter
    response = client.get(f"/api/pages/{page_id}/versions/compare?from=1")
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


def test_compare_versions_invalid_version_numbers(client, app, test_user_id):
    """Test comparing versions with invalid version numbers"""
    with app.app_context():
        page = Page(
            title="Test Page",
            slug="test-page",
            content="# Test",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            file_path="test-page.md",
        )
        db.session.add(page)
        db.session.commit()
        page_id = str(page.id)

    response = client.get(f"/api/pages/{page_id}/versions/compare?from=invalid&to=2")
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


def test_compare_versions_not_found(client, app, test_user_id):
    """Test comparing non-existent versions"""
    with app.app_context():
        page = Page(
            title="Test Page",
            slug="test-page",
            content="# Test",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            file_path="test-page.md",
        )
        db.session.add(page)
        db.session.commit()
        page_id = str(page.id)

    response = client.get(f"/api/pages/{page_id}/versions/compare?from=1&to=2")
    assert response.status_code == 404
    data = response.get_json()
    assert "error" in data


def test_restore_version_requires_auth(client, app, test_user_id):
    """Test that restore version requires authentication"""
    with app.app_context():
        page = Page(
            title="Test Page",
            slug="test-page",
            content="# Test",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            file_path="test-page.md",
        )
        db.session.add(page)
        db.session.flush()

        version = PageVersion(
            page_id=page.id,
            version=1,
            title="Test Page",
            content="# Old Content",
            changed_by=test_user_id,
        )
        db.session.add(version)
        db.session.commit()
        page_id = str(page.id)

    response = client.post(f"/api/pages/{page_id}/versions/1/restore")
    assert response.status_code == 401


def test_restore_version_viewer_forbidden(client, app, test_user_id):
    """Test that viewers cannot restore versions"""
    with app.app_context():
        page = Page(
            title="Test Page",
            slug="test-page",
            content="# Test",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            file_path="test-page.md",
        )
        db.session.add(page)
        db.session.flush()

        version = PageVersion(
            page_id=page.id,
            version=1,
            title="Test Page",
            content="# Old Content",
            changed_by=test_user_id,
        )
        db.session.add(version)
        db.session.commit()
        page_id = str(page.id)

    with mock_auth(test_user_id, "viewer"):
        response = client.post(
            f"/api/pages/{page_id}/versions/1/restore",
            headers=auth_headers(test_user_id, "viewer"),
        )
        assert response.status_code == 403


def test_restore_version_success(client, app, test_user_id):
    """Test successfully restoring a version"""
    with app.app_context():
        page = Page(
            title="Test Page",
            slug="test-page",
            content="# Current Content",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            file_path="test-page.md",
        )
        db.session.add(page)
        db.session.flush()

        version = PageVersion(
            page_id=page.id,
            version=1,
            title="Test Page",
            content="# Old Content",
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
        assert data["message"] == "Version restored successfully"


def test_restore_version_wrong_owner(client, app, test_user_id, test_writer_id):
    """Test that writers cannot restore pages they didn't create"""
    with app.app_context():
        page = Page(
            title="Test Page",
            slug="test-page",
            content="# Test",
            created_by=test_user_id,  # Created by different user
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            file_path="test-page.md",
        )
        db.session.add(page)
        db.session.flush()

        version = PageVersion(
            page_id=page.id,
            version=1,
            title="Test Page",
            content="# Old Content",
            changed_by=test_user_id,
        )
        db.session.add(version)
        db.session.commit()
        page_id = str(page.id)

    with mock_auth(test_writer_id, "writer"):
        response = client.post(
            f"/api/pages/{page_id}/versions/1/restore",
            headers=auth_headers(test_writer_id, "writer"),
        )
        assert response.status_code == 403
        data = response.get_json()
        assert "error" in data


def test_restore_version_admin_can_restore_any(
    client, app, test_user_id, test_admin_id
):
    """Test that admins can restore any page"""
    with app.app_context():
        page = Page(
            title="Test Page",
            slug="test-page",
            content="# Current Content",
            created_by=test_user_id,  # Created by different user
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            file_path="test-page.md",
        )
        db.session.add(page)
        db.session.flush()

        version = PageVersion(
            page_id=page.id,
            version=1,
            title="Test Page",
            content="# Old Content",
            changed_by=test_user_id,
        )
        db.session.add(version)
        db.session.commit()
        page_id = str(page.id)

    with mock_auth(test_admin_id, "admin"):
        response = client.post(
            f"/api/pages/{page_id}/versions/1/restore",
            headers=auth_headers(test_admin_id, "admin"),
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "message" in data
        assert data["message"] == "Version restored successfully"


def test_restore_version_not_found(client, app, test_user_id):
    """Test restoring non-existent version"""
    with app.app_context():
        page = Page(
            title="Test Page",
            slug="test-page",
            content="# Test",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            file_path="test-page.md",
        )
        db.session.add(page)
        db.session.commit()
        page_id = str(page.id)

    with mock_auth(test_user_id, "writer"):
        response = client.post(
            f"/api/pages/{page_id}/versions/999/restore",
            headers=auth_headers(test_user_id, "writer"),
        )
        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data
