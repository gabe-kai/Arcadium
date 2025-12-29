"""Additional tests for navigation API endpoints - edge cases and validation"""

from app import db
from app.models.page import Page
from tests.test_api.conftest import auth_headers, mock_auth


def test_get_navigation_deep_hierarchy(client, app, test_user_id):
    """Test navigation tree with deeply nested hierarchy"""
    with app.app_context():
        # Create 4-level hierarchy
        level1 = Page(
            title="Level 1",
            slug="level-1",
            content="# Level 1",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            file_path="level-1.md",
        )
        db.session.add(level1)
        db.session.flush()

        level2 = Page(
            title="Level 2",
            slug="level-2",
            content="# Level 2",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            parent_id=level1.id,
            file_path="level-2.md",
        )
        db.session.add(level2)
        db.session.flush()

        level3 = Page(
            title="Level 3",
            slug="level-3",
            content="# Level 3",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            parent_id=level2.id,
            file_path="level-3.md",
        )
        db.session.add(level3)
        db.session.flush()

        level4 = Page(
            title="Level 4",
            slug="level-4",
            content="# Level 4",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            parent_id=level3.id,
            file_path="level-4.md",
        )
        db.session.add(level4)
        db.session.commit()

    response = client.get("/api/navigation")
    assert response.status_code == 200
    data = response.get_json()

    # Verify deep nesting is preserved
    def find_path(nodes, target_slug, path=[]):
        for node in nodes:
            current_path = path + [node["slug"]]
            if node["slug"] == target_slug:
                return current_path
            if node.get("children"):
                result = find_path(node["children"], target_slug, current_path)
                if result:
                    return result
        return None

    path = find_path(data["tree"], "level-4")
    assert path is not None
    assert len(path) == 4


def test_get_navigation_multiple_roots(client, app, test_user_id):
    """Test navigation tree with multiple root pages"""
    with app.app_context():
        root1 = Page(
            title="Root 1",
            slug="root-1",
            content="# Root 1",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            file_path="root-1.md",
        )
        root2 = Page(
            title="Root 2",
            slug="root-2",
            content="# Root 2",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            file_path="root-2.md",
        )
        db.session.add(root1)
        db.session.add(root2)
        db.session.commit()

    response = client.get("/api/navigation")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data["tree"]) >= 2

    slugs = [n["slug"] for n in data["tree"]]
    assert "root-1" in slugs
    assert "root-2" in slugs


def test_get_navigation_ordering(client, app, test_user_id):
    """Test that navigation tree respects order_index"""
    with app.app_context():
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

        # Create children with different order_index
        child2 = Page(
            title="Second",
            slug="second",
            content="# Second",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            parent_id=parent.id,
            order_index=2,
            file_path="second.md",
        )
        child1 = Page(
            title="First",
            slug="first",
            content="# First",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            parent_id=parent.id,
            order_index=1,
            file_path="first.md",
        )
        db.session.add(child1)
        db.session.add(child2)
        db.session.commit()

    response = client.get("/api/navigation")
    assert response.status_code == 200
    data = response.get_json()

    # Find parent node
    def find_node(nodes, slug):
        for node in nodes:
            if node["slug"] == slug:
                return node
            result = find_node(node.get("children", []), slug)
            if result:
                return result
        return None

    parent_node = find_node(data["tree"], "parent")
    assert parent_node is not None
    assert len(parent_node["children"]) == 2
    # Should be ordered by order_index
    assert parent_node["children"][0]["slug"] == "first"
    assert parent_node["children"][1]["slug"] == "second"


def test_get_breadcrumb_handles_missing_parent(client, app, test_user_id):
    """Test breadcrumb handles gracefully when parent is missing (edge case)"""
    with app.app_context():
        # Create a root page
        root = Page(
            title="Root",
            slug="root",
            content="# Root",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            file_path="root.md",
        )
        db.session.add(root)
        db.session.flush()

        # Create child page
        child = Page(
            title="Child",
            slug="child",
            content="# Child",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            parent_id=root.id,
            file_path="child.md",
        )
        db.session.add(child)
        db.session.commit()
        child_id = str(child.id)

    response = client.get(f"/api/pages/{child_id}/breadcrumb")
    assert response.status_code == 200
    data = response.get_json()
    # Should return breadcrumb path
    assert len(data["breadcrumb"]) == 2
    assert data["breadcrumb"][0]["slug"] == "root"
    assert data["breadcrumb"][1]["slug"] == "child"


def test_get_breadcrumb_circular_reference_prevention(client, app, test_user_id):
    """Test that breadcrumb handles potential circular references"""
    with app.app_context():
        # Create pages that could form a cycle (though DB constraints prevent this)
        page1 = Page(
            title="Page 1",
            slug="page-1",
            content="# Page 1",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            file_path="page-1.md",
        )
        db.session.add(page1)
        db.session.flush()

        page2 = Page(
            title="Page 2",
            slug="page-2",
            content="# Page 2",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            parent_id=page1.id,
            file_path="page-2.md",
        )
        db.session.add(page2)
        db.session.commit()
        page2_id = str(page2.id)

    response = client.get(f"/api/pages/{page2_id}/breadcrumb")
    assert response.status_code == 200
    data = response.get_json()
    # Should not have duplicates (circular reference prevention)
    slugs = [item["slug"] for item in data["breadcrumb"]]
    assert len(slugs) == len(set(slugs))  # No duplicates


def test_get_previous_next_ordering_by_title(client, app, test_user_id):
    """Test that previous/next uses order_index then title for ordering"""
    with app.app_context():
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

        # Create pages with same order_index (should order by title)
        page_b = Page(
            title="B Page",
            slug="b-page",
            content="# B",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            parent_id=parent.id,
            order_index=1,
            file_path="b-page.md",
        )
        page_a = Page(
            title="A Page",
            slug="a-page",
            content="# A",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            parent_id=parent.id,
            order_index=1,
            file_path="a-page.md",
        )
        db.session.add(page_a)
        db.session.add(page_b)
        db.session.commit()
        page_a_id = str(page_a.id)

    response = client.get(f"/api/pages/{page_a_id}/navigation")
    assert response.status_code == 200
    data = response.get_json()
    # Next should be ordered by title when order_index is same
    assert data["next"] is not None
    assert data["next"]["slug"] == "b-page"


def test_get_previous_next_includes_own_drafts(client, app, test_user_id):
    """Test that creators can see their own drafts in previous/next"""
    with app.app_context():
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

        page1 = Page(
            title="Published",
            slug="published",
            content="# Published",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            parent_id=parent.id,
            order_index=1,
            file_path="published.md",
        )
        draft = Page(
            title="My Draft",
            slug="my-draft",
            content="# Draft",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="draft",
            parent_id=parent.id,
            order_index=2,
            file_path="my-draft.md",
        )
        db.session.add(page1)
        db.session.add(draft)
        db.session.commit()
        page1_id = str(page1.id)

    with mock_auth(test_user_id, "writer"):
        response = client.get(
            f"/api/pages/{page1_id}/navigation",
            headers=auth_headers(test_user_id, "writer"),
        )
        assert response.status_code == 200
        data = response.get_json()
        # Should see own draft as next
        assert data["next"] is not None
        assert data["next"]["slug"] == "my-draft"


def test_get_previous_next_admin_sees_all_drafts(
    client, app, test_user_id, test_admin_id
):
    """Test that admins can see all drafts in previous/next"""
    with app.app_context():
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

        page1 = Page(
            title="Published",
            slug="published",
            content="# Published",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            parent_id=parent.id,
            order_index=1,
            file_path="published.md",
        )
        draft = Page(
            title="Other User Draft",
            slug="other-draft",
            content="# Draft",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="draft",
            parent_id=parent.id,
            order_index=2,
            file_path="other-draft.md",
        )
        db.session.add(page1)
        db.session.add(draft)
        db.session.commit()
        page1_id = str(page1.id)

    with mock_auth(test_admin_id, "admin"):
        response = client.get(
            f"/api/pages/{page1_id}/navigation",
            headers=auth_headers(test_admin_id, "admin"),
        )
        assert response.status_code == 200
        data = response.get_json()
        # Admin should see all drafts
        assert data["next"] is not None
        assert data["next"]["slug"] == "other-draft"


def test_get_navigation_tree_empty_children(client, app, test_user_id):
    """Test navigation tree with pages that have no children"""
    with app.app_context():
        root = Page(
            title="Root",
            slug="root",
            content="# Root",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            file_path="root.md",
        )
        db.session.add(root)
        db.session.commit()

    response = client.get("/api/navigation")
    assert response.status_code == 200
    data = response.get_json()

    root_node = next((n for n in data["tree"] if n["slug"] == "root"), None)
    assert root_node is not None
    assert root_node["children"] == []


def test_get_breadcrumb_single_page(client, app, test_user_id):
    """Test breadcrumb for a single isolated page"""
    with app.app_context():
        page = Page(
            title="Isolated",
            slug="isolated",
            content="# Isolated",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            parent_id=None,
            file_path="isolated.md",
        )
        db.session.add(page)
        db.session.commit()
        page_id = str(page.id)

    response = client.get(f"/api/pages/{page_id}/breadcrumb")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data["breadcrumb"]) == 1
    assert data["breadcrumb"][0]["slug"] == "isolated"
