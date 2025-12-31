"""Tests for navigation API endpoints"""

import uuid

from app import db
from app.models.page import Page
from tests.test_api.conftest import auth_headers, mock_auth


def test_get_navigation_empty(client):
    """Test getting navigation tree when no pages exist"""
    response = client.get("/api/navigation")
    assert response.status_code == 200
    data = response.get_json()
    assert "tree" in data
    assert len(data["tree"]) == 0


def test_get_navigation_tree(client, app, test_user_id):
    """Test getting navigation tree with pages"""
    with app.app_context():
        # Create root page
        root = Page(
            title="Root Page",
            slug="root-page",
            content="# Root",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            file_path="root-page.md",
        )
        db.session.add(root)
        db.session.flush()

        # Create child page
        child = Page(
            title="Child Page",
            slug="child-page",
            content="# Child",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            parent_id=root.id,
            file_path="child-page.md",
        )
        db.session.add(child)
        db.session.commit()

    response = client.get("/api/navigation")
    assert response.status_code == 200
    data = response.get_json()
    assert "tree" in data
    assert len(data["tree"]) >= 1

    # Find root page in tree
    root_node = next((n for n in data["tree"] if n["slug"] == "root-page"), None)
    assert root_node is not None
    assert len(root_node["children"]) >= 1
    assert root_node["children"][0]["slug"] == "child-page"


def test_get_navigation_excludes_drafts(client, app, test_user_id):
    """Test that navigation tree excludes drafts for viewers"""
    with app.app_context():
        # Create draft page
        draft = Page(
            title="Draft Page",
            slug="draft-page",
            content="# Draft",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="draft",
            section="Regression-Testing",
            file_path="draft-page.md",
        )
        db.session.add(draft)
        db.session.commit()

    response = client.get("/api/navigation")
    assert response.status_code == 200
    data = response.get_json()

    # Draft should not appear in navigation tree
    def find_in_tree(nodes, slug):
        for node in nodes:
            if node["slug"] == slug:
                return True
            if find_in_tree(node.get("children", []), slug):
                return True
        return False

    assert not find_in_tree(data["tree"], "draft-page")


def test_get_navigation_includes_own_drafts(client, app, test_user_id):
    """Test that creators can see their own drafts in navigation"""
    with app.app_context():
        # Create draft page
        draft = Page(
            title="My Draft",
            slug="my-draft",
            content="# Draft",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="draft",
            section="Regression-Testing",
            file_path="my-draft.md",
        )
        db.session.add(draft)
        db.session.commit()

    with mock_auth(test_user_id, "writer"):
        response = client.get(
            "/api/navigation", headers=auth_headers(test_user_id, "writer")
        )
        assert response.status_code == 200
        data = response.get_json()

        # Should see own draft
        def find_in_tree(nodes, slug):
            for node in nodes:
                if node["slug"] == slug:
                    return True
                if find_in_tree(node.get("children", []), slug):
                    return True
            return False

        assert find_in_tree(data["tree"], "my-draft")


def test_get_navigation_admin_sees_all_drafts(client, app, test_user_id, test_admin_id):
    """Test that admins can see all drafts in navigation tree"""
    with app.app_context():
        # Create draft page by another user
        draft = Page(
            title="Other User Draft",
            slug="other-draft",
            content="# Draft",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="draft",
            section="Regression-Testing",
            file_path="other-draft.md",
        )
        db.session.add(draft)
        db.session.commit()

    with mock_auth(test_admin_id, "admin"):
        response = client.get(
            "/api/navigation", headers=auth_headers(test_admin_id, "admin")
        )
        assert response.status_code == 200
        data = response.get_json()

        # Admin should see all drafts
        def find_in_tree(nodes, slug):
            for node in nodes:
                if node["slug"] == slug:
                    return True
                if find_in_tree(node.get("children", []), slug):
                    return True
            return False

        assert find_in_tree(data["tree"], "other-draft")


def test_get_navigation_response_structure(client, app, test_user_id):
    """Test that navigation response matches API spec structure"""
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

    response = client.get("/api/navigation")
    assert response.status_code == 200
    data = response.get_json()
    assert "tree" in data
    assert isinstance(data["tree"], list)

    if len(data["tree"]) > 0:
        node = data["tree"][0]
        assert "id" in node
        assert "title" in node
        assert "slug" in node
        assert "status" in node
        assert "children" in node
        assert isinstance(node["children"], list)


def test_get_breadcrumb_root_page(client, app, test_user_id):
    """Test getting breadcrumb for root page"""
    with app.app_context():
        root = Page(
            title="Root Page",
            slug="root-page",
            content="# Root",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            file_path="root-page.md",
        )
        db.session.add(root)
        db.session.commit()
        root_id = str(root.id)

    response = client.get(f"/api/pages/{root_id}/breadcrumb")
    assert response.status_code == 200
    data = response.get_json()
    assert "breadcrumb" in data
    assert len(data["breadcrumb"]) == 1
    assert data["breadcrumb"][0]["slug"] == "root-page"


def test_get_breadcrumb_nested_page(client, app, test_user_id):
    """Test getting breadcrumb for nested page"""
    with app.app_context():
        # Create hierarchy: root -> parent -> child
        root = Page(
            title="Root",
            slug="root",
            content="# Root",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            file_path="root.md",
        )
        db.session.add(root)
        db.session.flush()

        parent = Page(
            title="Parent",
            slug="parent",
            content="# Parent",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            parent_id=root.id,
            file_path="parent.md",
        )
        db.session.add(parent)
        db.session.flush()

        child = Page(
            title="Child",
            slug="child",
            content="# Child",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            parent_id=parent.id,
            file_path="child.md",
        )
        db.session.add(child)
        db.session.commit()
        child_id = str(child.id)

    response = client.get(f"/api/pages/{child_id}/breadcrumb")
    assert response.status_code == 200
    data = response.get_json()
    assert "breadcrumb" in data
    assert len(data["breadcrumb"]) == 3
    assert data["breadcrumb"][0]["slug"] == "root"
    assert data["breadcrumb"][1]["slug"] == "parent"
    assert data["breadcrumb"][2]["slug"] == "child"


def test_get_breadcrumb_page_not_found(client):
    """Test getting breadcrumb for non-existent page"""
    fake_id = str(uuid.uuid4())
    response = client.get(f"/api/pages/{fake_id}/breadcrumb")
    assert response.status_code == 404
    data = response.get_json()
    assert "error" in data


def test_get_breadcrumb_response_structure(client, app, test_user_id):
    """Test that breadcrumb response matches API spec structure"""
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
        db.session.commit()
        page_id = str(page.id)

    response = client.get(f"/api/pages/{page_id}/breadcrumb")
    assert response.status_code == 200
    data = response.get_json()
    assert "breadcrumb" in data
    assert isinstance(data["breadcrumb"], list)

    if len(data["breadcrumb"]) > 0:
        item = data["breadcrumb"][0]
        assert "id" in item
        assert "title" in item
        assert "slug" in item


def test_get_previous_next_no_siblings(client, app, test_user_id):
    """Test getting previous/next for page with no siblings"""
    with app.app_context():
        page = Page(
            title="Only Page",
            slug="only-page",
            content="# Only",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            file_path="only-page.md",
        )
        db.session.add(page)
        db.session.commit()
        page_id = str(page.id)

    response = client.get(f"/api/pages/{page_id}/navigation")
    assert response.status_code == 200
    data = response.get_json()
    assert "previous" in data
    assert "next" in data
    assert data["previous"] is None
    assert data["next"] is None


def test_get_previous_next_with_siblings(client, app, test_user_id):
    """Test getting previous/next for page with siblings"""
    with app.app_context():
        # Create parent
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

        # Create siblings
        page1 = Page(
            title="Page 1",
            slug="page-1",
            content="# Page 1",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            parent_id=parent.id,
            order_index=1,
            file_path="page-1.md",
        )
        page2 = Page(
            title="Page 2",
            slug="page-2",
            content="# Page 2",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            parent_id=parent.id,
            order_index=2,
            file_path="page-2.md",
        )
        page3 = Page(
            title="Page 3",
            slug="page-3",
            content="# Page 3",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            parent_id=parent.id,
            order_index=3,
            file_path="page-3.md",
        )
        db.session.add(page1)
        db.session.add(page2)
        db.session.add(page3)
        db.session.commit()
        page2_id = str(page2.id)

    response = client.get(f"/api/pages/{page2_id}/navigation")
    assert response.status_code == 200
    data = response.get_json()
    assert "previous" in data
    assert "next" in data
    assert data["previous"] is not None
    assert data["next"] is not None
    assert data["previous"]["slug"] == "page-1"
    assert data["next"]["slug"] == "page-3"


def test_get_previous_next_first_sibling(client, app, test_user_id):
    """Test getting previous/next for first sibling (no previous)"""
    with app.app_context():
        parent = Page(
            title="Parent",
            slug="parent",
            content="# Parent",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            file_path="parent.md",
        )
        db.session.add(parent)
        db.session.flush()

        page1 = Page(
            title="First",
            slug="first",
            content="# First",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            parent_id=parent.id,
            order_index=1,
            file_path="first.md",
        )
        page2 = Page(
            title="Second",
            slug="second",
            content="# Second",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            parent_id=parent.id,
            order_index=2,
            file_path="second.md",
        )
        db.session.add(page1)
        db.session.add(page2)
        db.session.commit()
        page1_id = str(page1.id)

    response = client.get(f"/api/pages/{page1_id}/navigation")
    assert response.status_code == 200
    data = response.get_json()
    assert data["previous"] is None
    assert data["next"] is not None
    assert data["next"]["slug"] == "second"


def test_get_previous_next_last_sibling(client, app, test_user_id):
    """Test getting previous/next for last sibling (no next)"""
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
        page2 = Page(
            title="Last",
            slug="last",
            content="# Last",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            parent_id=parent.id,
            order_index=2,
            file_path="last.md",
        )
        db.session.add(page1)
        db.session.add(page2)
        db.session.commit()
        page2_id = str(page2.id)

    response = client.get(f"/api/pages/{page2_id}/navigation")
    assert response.status_code == 200
    data = response.get_json()
    assert data["previous"] is not None
    assert data["previous"]["slug"] == "first"
    assert data["next"] is None


def test_get_previous_next_excludes_drafts(client, app, test_user_id):
    """Test that previous/next excludes draft siblings for viewers"""
    with app.app_context():
        parent = Page(
            title="Parent",
            slug="parent",
            content="# Parent",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
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
            section="Regression-Testing",
            parent_id=parent.id,
            order_index=1,
            file_path="published.md",
        )
        draft = Page(
            title="Draft",
            slug="draft",
            content="# Draft",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="draft",
            section="Regression-Testing",
            parent_id=parent.id,
            order_index=2,
            file_path="draft.md",
        )
        page2 = Page(
            title="Published 2",
            slug="published-2",
            content="# Published 2",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            parent_id=parent.id,
            order_index=3,
            file_path="published-2.md",
        )
        db.session.add(page1)
        db.session.add(draft)
        db.session.add(page2)
        db.session.commit()
        page1_id = str(page1.id)

    response = client.get(f"/api/pages/{page1_id}/navigation")
    assert response.status_code == 200
    data = response.get_json()
    # Next should be published-2, skipping the draft
    assert data["next"] is not None
    assert data["next"]["slug"] == "published-2"


def test_get_previous_next_page_not_found(client):
    """Test getting previous/next for non-existent page"""
    fake_id = str(uuid.uuid4())
    response = client.get(f"/api/pages/{fake_id}/navigation")
    assert response.status_code == 404
    data = response.get_json()
    assert "error" in data


def test_get_previous_next_response_structure(client, app, test_user_id):
    """Test that previous/next response matches API spec structure"""
    with app.app_context():
        parent = Page(
            title="Parent",
            slug="parent",
            content="# Parent",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            file_path="parent.md",
        )
        db.session.add(parent)
        db.session.flush()

        page1 = Page(
            title="Page 1",
            slug="page-1",
            content="# Page 1",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            parent_id=parent.id,
            order_index=1,
            file_path="page-1.md",
        )
        page2 = Page(
            title="Page 2",
            slug="page-2",
            content="# Page 2",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            parent_id=parent.id,
            order_index=2,
            file_path="page-2.md",
        )
        db.session.add(page1)
        db.session.add(page2)
        db.session.commit()
        page1_id = str(page1.id)

    response = client.get(f"/api/pages/{page1_id}/navigation")
    assert response.status_code == 200
    data = response.get_json()
    assert "previous" in data
    assert "next" in data

    if data["previous"]:
        assert "id" in data["previous"]
        assert "title" in data["previous"]
        assert "slug" in data["previous"]

    if data["next"]:
        assert "id" in data["next"]
        assert "title" in data["next"]
        assert "slug" in data["next"]
