"""Tests for orphanage management API endpoints"""

from app import db
from app.models.page import Page
from app.services.orphanage_service import OrphanageService
from tests.test_api.conftest import auth_headers, mock_auth


def test_get_orphanage_empty(client, app):
    """Test getting orphanage when no orphaned pages exist"""
    response = client.get("/api/orphanage")
    assert response.status_code == 200
    data = response.get_json()
    assert "orphanage_id" in data
    assert "pages" in data
    assert "grouped_by_parent" in data
    assert len(data["pages"]) == 0
    assert len(data["grouped_by_parent"]) == 0


def test_get_orphanage_with_orphaned_pages(client, app, test_user_id):
    """Test getting orphanage with orphaned pages"""
    with app.app_context():
        # Create parent page
        parent = Page(
            title="Parent Page",
            slug="parent-page",
            content="# Parent",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            file_path="parent-page.md",
        )
        db.session.add(parent)
        db.session.flush()
        parent_id = parent.id

        # Create orphaned page
        orphan = Page(
            title="Orphaned Page",
            slug="orphaned-page",
            content="# Orphan",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            parent_id=OrphanageService.get_or_create_orphanage(test_user_id).id,
            is_orphaned=True,
            orphaned_from=parent_id,
            file_path="orphaned-page.md",
        )
        db.session.add(orphan)
        db.session.commit()

    response = client.get("/api/orphanage")
    assert response.status_code == 200
    data = response.get_json()
    assert "orphanage_id" in data
    assert "pages" in data
    assert len(data["pages"]) >= 1

    # Find orphaned page
    orphan_data = next((p for p in data["pages"] if p["slug"] == "orphaned-page"), None)
    assert orphan_data is not None
    assert orphan_data["title"] == "Orphaned Page"
    assert "orphaned_from" in orphan_data


def test_get_orphanage_response_structure(client, app, test_user_id):
    """Test that orphanage response matches API spec structure"""
    with app.app_context():
        # Create orphaned page
        orphan = Page(
            title="Test Orphan",
            slug="test-orphan",
            content="# Test",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            parent_id=OrphanageService.get_or_create_orphanage(test_user_id).id,
            is_orphaned=True,
            file_path="test-orphan.md",
        )
        db.session.add(orphan)
        db.session.commit()

    response = client.get("/api/orphanage")
    assert response.status_code == 200
    data = response.get_json()
    assert "orphanage_id" in data
    assert "pages" in data
    assert "grouped_by_parent" in data

    if len(data["pages"]) > 0:
        page = data["pages"][0]
        assert "id" in page
        assert "title" in page
        assert "slug" in page
        assert "orphaned_from" in page
        assert "orphaned_at" in page


def test_get_orphanage_grouped_by_parent(client, app, test_user_id):
    """Test that orphanage groups pages by original parent"""
    with app.app_context():
        # Create two parent pages
        parent1 = Page(
            title="Parent 1",
            slug="parent-1",
            content="# Parent 1",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            file_path="parent-1.md",
        )
        parent2 = Page(
            title="Parent 2",
            slug="parent-2",
            content="# Parent 2",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            file_path="parent-2.md",
        )
        db.session.add(parent1)
        db.session.add(parent2)
        db.session.flush()

        # Store parent IDs before committing
        parent1_id = parent1.id
        parent2_id = parent2.id

        orphanage = OrphanageService.get_or_create_orphanage(test_user_id)

        # Create orphaned pages from different parents
        orphan1 = Page(
            title="Orphan 1",
            slug="orphan-1",
            content="# Orphan 1",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            parent_id=orphanage.id,
            is_orphaned=True,
            orphaned_from=parent1_id,
            file_path="orphan-1.md",
        )
        orphan2 = Page(
            title="Orphan 2",
            slug="orphan-2",
            content="# Orphan 2",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            parent_id=orphanage.id,
            is_orphaned=True,
            orphaned_from=parent1_id,  # Same parent as orphan1
            file_path="orphan-2.md",
        )
        orphan3 = Page(
            title="Orphan 3",
            slug="orphan-3",
            content="# Orphan 3",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            parent_id=orphanage.id,
            is_orphaned=True,
            orphaned_from=parent2_id,  # Different parent
            file_path="orphan-3.md",
        )
        db.session.add(orphan1)
        db.session.add(orphan2)
        db.session.add(orphan3)
        db.session.commit()

        # Store parent1_id_str before context closes
        parent1_id_str = str(parent1_id)

    response = client.get("/api/orphanage")
    assert response.status_code == 200
    data = response.get_json()
    assert "grouped_by_parent" in data

    # Should have 2 groups (one for parent1, one for parent2)
    grouped = data["grouped_by_parent"]
    assert len(grouped) >= 2

    # Find parent1 group
    if parent1_id_str in grouped:
        assert len(grouped[parent1_id_str]) >= 2  # orphan1 and orphan2


def test_reassign_orphaned_pages_requires_auth(client, app, test_user_id):
    """Test that reassign requires authentication"""
    response = client.post(
        "/api/orphanage/reassign", json={"page_ids": [], "new_parent_id": None}
    )
    assert response.status_code == 401


def test_reassign_orphaned_pages_requires_admin(client, app, test_user_id):
    """Test that reassign requires admin role"""
    with mock_auth(test_user_id, "writer"):
        response = client.post(
            "/api/orphanage/reassign",
            json={"page_ids": [], "new_parent_id": None},
            headers=auth_headers(test_user_id, "writer"),
        )
        assert response.status_code == 403


def test_reassign_orphaned_pages_success(client, app, test_user_id, test_admin_id):
    """Test successfully reassigning orphaned pages"""
    with app.app_context():
        # Create new parent
        new_parent = Page(
            title="New Parent",
            slug="new-parent",
            content="# New Parent",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            file_path="new-parent.md",
        )
        db.session.add(new_parent)
        db.session.flush()

        orphanage = OrphanageService.get_or_create_orphanage(test_user_id)

        # Create orphaned page
        orphan = Page(
            title="Orphan",
            slug="orphan",
            content="# Orphan",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            parent_id=orphanage.id,
            is_orphaned=True,
            file_path="orphan.md",
        )
        db.session.add(orphan)
        db.session.commit()
        orphan_id = str(orphan.id)
        new_parent_id = str(new_parent.id)

    with mock_auth(test_admin_id, "admin"):
        response = client.post(
            "/api/orphanage/reassign",
            json={
                "page_ids": [orphan_id],
                "new_parent_id": new_parent_id,
                "reassign_all": False,
            },
            headers=auth_headers(test_admin_id, "admin"),
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "reassigned" in data
        assert "remaining_in_orphanage" in data
        assert data["reassigned"] == 1


def test_reassign_orphaned_pages_reassign_all(client, app, test_user_id, test_admin_id):
    """Test reassigning all orphaned pages"""
    with app.app_context():
        # Create new parent
        new_parent = Page(
            title="New Parent",
            slug="new-parent",
            content="# New Parent",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            file_path="new-parent.md",
        )
        db.session.add(new_parent)
        db.session.flush()

        orphanage = OrphanageService.get_or_create_orphanage(test_user_id)

        # Create multiple orphaned pages
        for i in range(3):
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
        new_parent_id = str(new_parent.id)

    with mock_auth(test_admin_id, "admin"):
        response = client.post(
            "/api/orphanage/reassign",
            json={
                "page_ids": [],  # Empty, but reassign_all is true
                "new_parent_id": new_parent_id,
                "reassign_all": True,
            },
            headers=auth_headers(test_admin_id, "admin"),
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["reassigned"] == 3
        assert data["remaining_in_orphanage"] == 0


def test_reassign_orphaned_pages_missing_page_ids(client, app, test_admin_id):
    """Test reassign with missing page_ids (should default to empty list)"""
    with mock_auth(test_admin_id, "admin"):
        response = client.post(
            "/api/orphanage/reassign",
            json={"new_parent_id": None},
            headers=auth_headers(test_admin_id, "admin"),
        )
        # Should succeed but reassign 0 pages
        assert response.status_code == 200
        data = response.get_json()
        assert data["reassigned"] == 0


def test_reassign_orphaned_pages_invalid_page_id(client, app, test_admin_id):
    """Test reassign with invalid page_id format"""
    with mock_auth(test_admin_id, "admin"):
        response = client.post(
            "/api/orphanage/reassign",
            json={"page_ids": ["invalid-uuid"], "new_parent_id": None},
            headers=auth_headers(test_admin_id, "admin"),
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data


def test_clear_orphanage_requires_auth(client):
    """Test that clear orphanage requires authentication"""
    response = client.post("/api/orphanage/clear", json={})
    assert response.status_code == 401


def test_clear_orphanage_requires_admin(client, app, test_user_id):
    """Test that clear orphanage requires admin role"""
    with mock_auth(test_user_id, "writer"):
        response = client.post(
            "/api/orphanage/clear",
            json={},
            headers=auth_headers(test_user_id, "writer"),
        )
        assert response.status_code == 403


def test_clear_orphanage_success(client, app, test_user_id, test_admin_id):
    """Test successfully clearing orphanage"""
    with app.app_context():
        orphanage = OrphanageService.get_or_create_orphanage(test_user_id)

        # Create orphaned pages
        for i in range(3):
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

    with mock_auth(test_admin_id, "admin"):
        response = client.post(
            "/api/orphanage/clear",
            json={},
            headers=auth_headers(test_admin_id, "admin"),
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "message" in data
        assert "reassigned_count" in data
        assert "deleted_count" in data
        assert data["message"] == "Orphanage cleared successfully"
        assert data["deleted_count"] == 0


def test_clear_orphanage_with_reassign_to(client, app, test_user_id, test_admin_id):
    """Test clearing orphanage with reassign_to parameter"""
    with app.app_context():
        # Create new parent
        new_parent = Page(
            title="New Parent",
            slug="new-parent",
            content="# New Parent",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            file_path="new-parent.md",
        )
        db.session.add(new_parent)
        db.session.flush()

        orphanage = OrphanageService.get_or_create_orphanage(test_user_id)

        # Create orphaned pages
        for i in range(2):
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
        new_parent_id = str(new_parent.id)

    with mock_auth(test_admin_id, "admin"):
        response = client.post(
            "/api/orphanage/clear",
            json={"reassign_to": new_parent_id},
            headers=auth_headers(test_admin_id, "admin"),
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["reassigned_count"] == 2
        assert data["deleted_count"] == 0


def test_clear_orphanage_invalid_reassign_to(client, app, test_admin_id):
    """Test clear orphanage with invalid reassign_to format"""
    with mock_auth(test_admin_id, "admin"):
        response = client.post(
            "/api/orphanage/clear",
            json={"reassign_to": "invalid-uuid"},
            headers=auth_headers(test_admin_id, "admin"),
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data


def test_reassign_orphaned_pages_response_structure(
    client, app, test_user_id, test_admin_id
):
    """Test that reassign response matches API spec structure"""
    with app.app_context():
        new_parent = Page(
            title="New Parent",
            slug="new-parent",
            content="# New Parent",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
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
            parent_id=orphanage.id,
            is_orphaned=True,
            file_path="orphan.md",
        )
        db.session.add(orphan)
        db.session.commit()
        orphan_id = str(orphan.id)
        new_parent_id = str(new_parent.id)

    with mock_auth(test_admin_id, "admin"):
        response = client.post(
            "/api/orphanage/reassign",
            json={"page_ids": [orphan_id], "new_parent_id": new_parent_id},
            headers=auth_headers(test_admin_id, "admin"),
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "reassigned" in data
        assert "remaining_in_orphanage" in data
        assert isinstance(data["reassigned"], int)
        assert isinstance(data["remaining_in_orphanage"], int)
