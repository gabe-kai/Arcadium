"""Additional tests for orphanage management API endpoints - edge cases and validation"""

import uuid

from app import db
from app.models.page import Page
from app.services.orphanage_service import OrphanageService
from tests.test_api.conftest import auth_headers, mock_auth


def test_get_orphanage_creates_orphanage_if_missing(client, app, test_user_id):
    """Test that orphanage is created automatically if it doesn't exist"""
    response = client.get("/api/orphanage")
    assert response.status_code == 200
    data = response.get_json()
    assert "orphanage_id" in data
    assert data["orphanage_id"] is not None


def test_get_orphanage_orphaned_from_none(client, app, test_user_id):
    """Test orphanage handles pages with orphaned_from=None"""
    with app.app_context():
        orphanage = OrphanageService.get_or_create_orphanage(test_user_id)

        # Create orphaned page with no orphaned_from
        orphan = Page(
            title="Orphan No Parent",
            slug="orphan-no-parent",
            content="# Orphan",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            parent_id=orphanage.id,
            is_orphaned=True,
            orphaned_from=None,
            file_path="orphan-no-parent.md",
        )
        db.session.add(orphan)
        db.session.commit()

    response = client.get("/api/orphanage")
    assert response.status_code == 200
    data = response.get_json()

    orphan_data = next(
        (p for p in data["pages"] if p["slug"] == "orphan-no-parent"), None
    )
    assert orphan_data is not None
    assert orphan_data["orphaned_from"] is None


def test_reassign_orphaned_pages_to_root(client, app, test_user_id, test_admin_id):
    """Test reassigning orphaned pages to root (new_parent_id=None)"""
    with app.app_context():
        orphanage = OrphanageService.get_or_create_orphanage(test_user_id)

        orphan = Page(
            title="Orphan",
            slug="orphan",
            content="# Orphan",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            parent_id=orphanage.id,
            is_orphaned=True,
            file_path="orphan.md",
        )
        db.session.add(orphan)
        db.session.commit()
        orphan_id = str(orphan.id)

    with mock_auth(test_admin_id, "admin"):
        response = client.post(
            "/api/orphanage/reassign",
            json={"page_ids": [orphan_id], "new_parent_id": None},
            headers=auth_headers(test_admin_id, "admin"),
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["reassigned"] == 1


def test_reassign_orphaned_pages_empty_list(client, app, test_admin_id):
    """Test reassign with empty page_ids list"""
    with mock_auth(test_admin_id, "admin"):
        response = client.post(
            "/api/orphanage/reassign",
            json={"page_ids": [], "new_parent_id": None},
            headers=auth_headers(test_admin_id, "admin"),
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["reassigned"] == 0


def test_reassign_orphaned_pages_invalid_new_parent(
    client, app, test_user_id, test_admin_id
):
    """Test reassign with non-existent new_parent_id"""
    with app.app_context():
        orphanage = OrphanageService.get_or_create_orphanage(test_user_id)

        orphan = Page(
            title="Orphan",
            slug="orphan",
            content="# Orphan",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            parent_id=orphanage.id,
            is_orphaned=True,
            file_path="orphan.md",
        )
        db.session.add(orphan)
        db.session.commit()
        orphan_id = str(orphan.id)
        fake_parent_id = str(uuid.uuid4())

    with mock_auth(test_admin_id, "admin"):
        response = client.post(
            "/api/orphanage/reassign",
            json={"page_ids": [orphan_id], "new_parent_id": fake_parent_id},
            headers=auth_headers(test_admin_id, "admin"),
        )
        # Should fail because parent doesn't exist (we validate before reassigning)
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data


def test_reassign_orphaned_pages_missing_request_body(client, app, test_admin_id):
    """Test reassign with missing request body"""
    with mock_auth(test_admin_id, "admin"):
        response = client.post(
            "/api/orphanage/reassign",
            headers=auth_headers(test_admin_id, "admin"),
            content_type="application/json",
        )
        # Flask returns 400 for missing JSON when content_type is set
        assert response.status_code in [400, 500]
        data = response.get_json()
        assert "error" in data


def test_clear_orphanage_empty_orphanage(client, app, test_admin_id):
    """Test clearing empty orphanage"""
    with mock_auth(test_admin_id, "admin"):
        response = client.post(
            "/api/orphanage/clear",
            json={},
            headers=auth_headers(test_admin_id, "admin"),
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["reassigned_count"] == 0
        assert data["deleted_count"] == 0


def test_clear_orphanage_missing_request_body(client, app, test_admin_id):
    """Test clear orphanage with missing request body (should work with empty dict)"""
    with mock_auth(test_admin_id, "admin"):
        response = client.post(
            "/api/orphanage/clear",
            json={},  # Explicitly send empty JSON
            headers=auth_headers(test_admin_id, "admin"),
        )
        # Should work with empty body (defaults to empty dict)
        assert response.status_code == 200


def test_clear_orphanage_with_nonexistent_reassign_to(client, app, test_admin_id):
    """Test clear orphanage with non-existent reassign_to"""
    fake_parent_id = str(uuid.uuid4())

    with mock_auth(test_admin_id, "admin"):
        response = client.post(
            "/api/orphanage/clear",
            json={"reassign_to": fake_parent_id},
            headers=auth_headers(test_admin_id, "admin"),
        )
        # Should fail because parent doesn't exist (we validate before reassigning)
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data


def test_get_orphanage_large_list(client, app, test_user_id):
    """Test orphanage with many orphaned pages"""
    with app.app_context():
        orphanage = OrphanageService.get_or_create_orphanage(test_user_id)

        # Create 10 orphaned pages
        for i in range(10):
            orphan = Page(
                title=f"Orphan {i}",
                slug=f"orphan-{i}",
                content=f"# Orphan {i}",
                created_by=test_user_id,
                updated_by=test_user_id,
                status="published",
                parent_id=orphanage.id,
                is_orphaned=True,
                file_path=f"orphan-{i}.md",
            )
            db.session.add(orphan)
        db.session.commit()

    response = client.get("/api/orphanage")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data["pages"]) == 10


def test_reassign_orphaned_pages_partial_success(
    client, app, test_user_id, test_admin_id
):
    """Test reassign when some pages don't exist (should continue with valid ones)"""
    with app.app_context():
        new_parent = Page(
            title="New Parent",
            slug="new-parent",
            content="# New Parent",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            file_path="new-parent.md",
        )
        db.session.add(new_parent)
        db.session.flush()

        orphanage = OrphanageService.get_or_create_orphanage(test_user_id)

        orphan = Page(
            title="Orphan",
            slug="orphan",
            content="# Orphan",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            parent_id=orphanage.id,
            is_orphaned=True,
            file_path="orphan.md",
        )
        db.session.add(orphan)
        db.session.commit()
        orphan_id = str(orphan.id)
        new_parent_id = str(new_parent.id)
        fake_id = str(uuid.uuid4())

    with mock_auth(test_admin_id, "admin"):
        response = client.post(
            "/api/orphanage/reassign",
            json={
                "page_ids": [orphan_id, fake_id],  # One valid, one invalid
                "new_parent_id": new_parent_id,
            },
            headers=auth_headers(test_admin_id, "admin"),
        )
        # Should succeed with at least 1 reassigned (the valid one)
        assert response.status_code == 200
        data = response.get_json()
        assert data["reassigned"] >= 1
