"""Additional validation tests for orphanage management endpoints - verifying actual state changes"""

import uuid

from app import db
from app.models.page import Page
from app.services.orphanage_service import OrphanageService
from tests.test_api.conftest import auth_headers, mock_auth


def test_get_orphanage_only_returns_orphaned_pages(client, app, test_user_id):
    """Test that GET /api/orphanage only returns pages with is_orphaned=True"""
    with app.app_context():
        orphanage = OrphanageService.get_or_create_orphanage(test_user_id)

        # Create orphaned page
        orphan = Page(
            title="Orphaned Page",
            slug="orphaned-page",
            content="# Orphan",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            parent_id=orphanage.id,
            is_orphaned=True,
            file_path="orphaned-page.md",
        )
        db.session.add(orphan)

        # Create non-orphaned page (should NOT appear in orphanage)
        normal_page = Page(
            title="Normal Page",
            slug="normal-page",
            content="# Normal",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            parent_id=None,
            is_orphaned=False,
            file_path="normal-page.md",
        )
        db.session.add(normal_page)
        db.session.commit()

    response = client.get("/api/orphanage")
    assert response.status_code == 200
    data = response.get_json()

    # Should only contain orphaned page
    assert len(data["pages"]) == 1
    assert data["pages"][0]["slug"] == "orphaned-page"
    assert "normal-page" not in [p["slug"] for p in data["pages"]]


def test_reassign_orphaned_pages_actually_updates_page_state(
    client, app, test_user_id, test_admin_id
):
    """Test that reassigning actually updates is_orphaned, orphaned_from, and parent_id"""
    with app.app_context():
        # Create a parent page that will be deleted (to set orphaned_from)
        deleted_parent = Page(
            title="Deleted Parent",
            slug="deleted-parent",
            content="# Deleted Parent",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            file_path="deleted-parent.md",
        )
        db.session.add(deleted_parent)
        db.session.flush()
        deleted_parent_id = deleted_parent.id

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
            orphaned_from=deleted_parent_id,  # Reference to deleted parent
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

    # Verify page state was actually updated
    with app.app_context():
        updated_page = db.session.get(Page, uuid.UUID(orphan_id))
        assert updated_page is not None
        assert updated_page.is_orphaned is False, "Page should no longer be orphaned"
        assert updated_page.orphaned_from is None, "orphaned_from should be cleared"
        assert (
            str(updated_page.parent_id) == new_parent_id
        ), "parent_id should be updated"


def test_reassign_orphaned_pages_to_root_clears_parent(
    client, app, test_user_id, test_admin_id
):
    """Test that reassigning to root (None) actually sets parent_id to None"""
    with app.app_context():
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

    with mock_auth(test_admin_id, "admin"):
        response = client.post(
            "/api/orphanage/reassign",
            json={"page_ids": [orphan_id], "new_parent_id": None},
            headers=auth_headers(test_admin_id, "admin"),
        )
        assert response.status_code == 200

    # Verify page state
    with app.app_context():
        updated_page = db.session.get(Page, uuid.UUID(orphan_id))
        assert updated_page.parent_id is None
        assert updated_page.is_orphaned is False
        assert updated_page.orphaned_from is None


def test_reassign_non_orphaned_page_fails(client, app, test_user_id, test_admin_id):
    """Test that reassigning a non-orphaned page fails"""
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

        # Create non-orphaned page
        normal_page = Page(
            title="Normal Page",
            slug="normal-page",
            content="# Normal",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            parent_id=None,
            is_orphaned=False,
            file_path="normal-page.md",
        )
        db.session.add(normal_page)
        db.session.commit()
        page_id = str(normal_page.id)
        new_parent_id = str(new_parent.id)

    with mock_auth(test_admin_id, "admin"):
        response = client.post(
            "/api/orphanage/reassign",
            json={"page_ids": [page_id], "new_parent_id": new_parent_id},
            headers=auth_headers(test_admin_id, "admin"),
        )
        # Should fail because page is not orphaned
        assert (
            response.status_code == 200
        )  # Route succeeds, but service skips non-orphaned pages
        data = response.get_json()
        assert data["reassigned"] == 0  # No pages reassigned


def test_reassign_orphaned_pages_circular_reference_prevention(
    client, app, test_user_id, test_admin_id
):
    """Test that reassigning to a descendant prevents circular references"""
    with app.app_context():
        # Create parent page
        parent = Page(
            title="Parent",
            slug="parent",
            content="# Parent",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            file_path="parent.md",
        )
        db.session.add(parent)
        db.session.flush()

        # Create child page
        child = Page(
            title="Child",
            slug="child",
            content="# Child",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            parent_id=parent.id,
            file_path="child.md",
        )
        db.session.add(child)
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
        child_id = str(child.id)

    # Try to reassign orphan to child (orphan would become child's parent, but child is already parent's child)
    # This should work because orphan is not a descendant of child
    # But if we try to reassign orphan to itself, that should fail
    with mock_auth(test_admin_id, "admin"):
        # First, try reassigning orphan to child (should work)
        response = client.post(
            "/api/orphanage/reassign",
            json={"page_ids": [orphan_id], "new_parent_id": child_id},
            headers=auth_headers(test_admin_id, "admin"),
        )
        assert response.status_code == 200

        # Re-orphan the page for next test
        with app.app_context():
            orphanage = OrphanageService.get_or_create_orphanage(test_user_id)
            orphan_page = db.session.get(Page, uuid.UUID(orphan_id))
            orphan_page.parent_id = orphanage.id
            orphan_page.is_orphaned = True
            db.session.commit()

        # Now try to reassign orphan to itself (should fail)
        response = client.post(
            "/api/orphanage/reassign",
            json={
                "page_ids": [orphan_id],
                "new_parent_id": orphan_id,  # Circular reference
            },
            headers=auth_headers(test_admin_id, "admin"),
        )
        # Service should prevent this
        assert response.status_code == 200  # Route succeeds
        data = response.get_json()
        assert (
            data["reassigned"] == 0
        )  # But no pages reassigned due to circular reference


def test_reassign_orphaned_pages_remaining_count_accuracy(
    client, app, test_user_id, test_admin_id
):
    """Test that remaining_in_orphanage count is accurate after reassign"""
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
        new_parent_id = str(new_parent.id)

        orphanage = OrphanageService.get_or_create_orphanage(test_user_id)

        # Create 5 orphaned pages
        orphans = []
        for i in range(5):
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
            orphans.append(orphan)
        db.session.flush()  # Flush to get IDs
        orphan_ids = [str(orphan.id) for orphan in orphans]
        db.session.commit()

    with mock_auth(test_admin_id, "admin"):
        # Reassign 2 pages
        response = client.post(
            "/api/orphanage/reassign",
            json={
                "page_ids": orphan_ids[:2],  # First 2
                "new_parent_id": new_parent_id,
            },
            headers=auth_headers(test_admin_id, "admin"),
        )
        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.get_json()}")
        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.get_json()}"
        data = response.get_json()
        assert data["reassigned"] == 2
        assert data["remaining_in_orphanage"] == 3  # 5 - 2 = 3


def test_clear_orphanage_actually_reassigns_pages(
    client, app, test_user_id, test_admin_id
):
    """Test that clear orphanage actually reassigns pages to root"""
    orphan_ids = []
    with app.app_context():
        orphanage = OrphanageService.get_or_create_orphanage(test_user_id)

        # Create orphaned pages
        orphans = []
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
            orphans.append(orphan)
        db.session.flush()  # Flush to get IDs
        orphan_ids = [str(orphan.id) for orphan in orphans]
        db.session.commit()

    with mock_auth(test_admin_id, "admin"):
        response = client.post(
            "/api/orphanage/clear",
            json={},
            headers=auth_headers(test_admin_id, "admin"),
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["reassigned_count"] == 3

    # Verify pages are no longer orphaned
    with app.app_context():
        for orphan_id_str in orphan_ids:
            orphan_uuid = uuid.UUID(orphan_id_str)
            page = db.session.get(Page, orphan_uuid)
            assert page is not None
            assert page.is_orphaned is False
            assert page.orphaned_from is None


def test_clear_orphanage_with_reassign_to_actually_reassigns(
    client, app, test_user_id, test_admin_id
):
    """Test that clear with reassign_to actually reassigns all pages to that parent"""
    orphan_ids = []
    new_parent_id = None
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
        new_parent_id = str(new_parent.id)

        orphanage = OrphanageService.get_or_create_orphanage(test_user_id)

        # Create orphaned pages
        orphans = []
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
            orphans.append(orphan)
        db.session.flush()  # Flush to get IDs
        orphan_ids = [str(orphan.id) for orphan in orphans]
        db.session.commit()

    with mock_auth(test_admin_id, "admin"):
        response = client.post(
            "/api/orphanage/clear",
            json={"reassign_to": new_parent_id},
            headers=auth_headers(test_admin_id, "admin"),
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["reassigned_count"] == 2

    # Verify pages are reassigned to new_parent
    with app.app_context():
        new_parent_uuid = uuid.UUID(new_parent_id)
        for orphan_id_str in orphan_ids:
            orphan_uuid = uuid.UUID(orphan_id_str)
            page = db.session.get(Page, orphan_uuid)
            assert page is not None
            assert page.is_orphaned is False
            assert page.parent_id == new_parent_uuid


def test_reassign_all_with_empty_orphanage(client, app, test_user_id, test_admin_id):
    """Test reassign_all when orphanage is empty"""
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
        db.session.commit()
        new_parent_id = str(new_parent.id)

    with mock_auth(test_admin_id, "admin"):
        response = client.post(
            "/api/orphanage/reassign",
            json={"page_ids": [], "new_parent_id": new_parent_id, "reassign_all": True},
            headers=auth_headers(test_admin_id, "admin"),
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["reassigned"] == 0
        assert data["remaining_in_orphanage"] == 0
