"""Tests for section extraction API endpoints"""

import uuid

from app import db
from app.models.page import Page
from tests.test_api.conftest import auth_headers, mock_auth


def test_extract_selection_requires_auth(client):
    """Test that extract selection requires authentication"""
    response = client.post(
        f"/api/pages/{uuid.uuid4()}/extract",
        json={
            "selection_start": 0,
            "selection_end": 10,
            "new_title": "Test",
            "new_slug": "test",
        },
    )
    assert response.status_code == 401


def test_extract_selection_requires_writer(client, app, test_user_id):
    """Test that extract selection requires writer role"""
    with app.app_context():
        page = Page(
            title="Source Page",
            slug="source-page",
            content="# Source\n\nSome content here.",
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            file_path="source-page.md",
        )
        db.session.add(page)
        db.session.commit()
        page_id = str(page.id)

    with mock_auth(test_user_id, "viewer"):
        response = client.post(
            f"/api/pages/{page_id}/extract",
            json={
                "selection_start": 0,
                "selection_end": 10,
                "new_title": "Test",
                "new_slug": "test",
            },
            headers=auth_headers(test_user_id, "viewer"),
        )
        assert response.status_code == 403


def test_extract_selection_success(client, app, test_writer_id):
    """Test successfully extracting a selection"""
    with app.app_context():
        page = Page(
            title="Source Page",
            slug="source-page",
            content="# Source\n\nSome content here that will be extracted.",
            created_by=test_writer_id,
            updated_by=test_writer_id,
            status="published",
            section="Regression-Testing",
            file_path="source-page.md",
        )
        db.session.add(page)
        db.session.commit()
        page_id = str(page.id)

    with mock_auth(test_writer_id, "writer"):
        response = client.post(
            f"/api/pages/{page_id}/extract",
            json={
                "selection_start": 10,
                "selection_end": 30,
                "new_title": "Extracted Section",
                "new_slug": "extracted-section",
                "replace_with_link": True,
            },
            headers=auth_headers(test_writer_id, "writer"),
        )
        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.get_json()}")
        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.get_json()}"
        data = response.get_json()
        assert "new_page" in data
        assert "original_page" in data
        assert data["new_page"]["title"] == "Extracted Section"
        assert data["new_page"]["slug"] == "extracted-section"


def test_extract_selection_missing_fields(client, app, test_writer_id):
    """Test extract selection with missing required fields"""
    with app.app_context():
        page = Page(
            title="Source Page",
            slug="source-page",
            content="# Source\n\nContent",
            created_by=test_writer_id,
            updated_by=test_writer_id,
            status="published",
            section="Regression-Testing",
            file_path="source-page.md",
        )
        db.session.add(page)
        db.session.commit()
        page_id = str(page.id)

    with mock_auth(test_writer_id, "writer"):
        # Missing selection_start
        response = client.post(
            f"/api/pages/{page_id}/extract",
            json={"selection_end": 10, "new_title": "Test", "new_slug": "test"},
            headers=auth_headers(test_writer_id, "writer"),
        )
        assert response.status_code == 400

        # Missing new_title
        response = client.post(
            f"/api/pages/{page_id}/extract",
            json={"selection_start": 0, "selection_end": 10, "new_slug": "test"},
            headers=auth_headers(test_writer_id, "writer"),
        )
        assert response.status_code == 400


def test_extract_selection_invalid_bounds(client, app, test_writer_id):
    """Test extract selection with invalid selection bounds"""
    with app.app_context():
        page = Page(
            title="Source Page",
            slug="source-page",
            content="# Source\n\nContent",
            created_by=test_writer_id,
            updated_by=test_writer_id,
            status="published",
            section="Regression-Testing",
            file_path="source-page.md",
        )
        db.session.add(page)
        db.session.commit()
        page_id = str(page.id)

    with mock_auth(test_writer_id, "writer"):
        # selection_start > selection_end
        response = client.post(
            f"/api/pages/{page_id}/extract",
            json={
                "selection_start": 20,
                "selection_end": 10,
                "new_title": "Test",
                "new_slug": "test",
            },
            headers=auth_headers(test_writer_id, "writer"),
        )
        assert response.status_code == 400

        # Invalid integer format
        response = client.post(
            f"/api/pages/{page_id}/extract",
            json={
                "selection_start": "invalid",
                "selection_end": 10,
                "new_title": "Test",
                "new_slug": "test",
            },
            headers=auth_headers(test_writer_id, "writer"),
        )
        assert response.status_code == 400


def test_extract_heading_section_requires_auth(client):
    """Test that extract heading requires authentication"""
    response = client.post(
        f"/api/pages/{uuid.uuid4()}/extract-heading",
        json={
            "heading_text": "Section",
            "heading_level": 2,
            "new_title": "Test",
            "new_slug": "test",
        },
    )
    assert response.status_code == 401


def test_extract_heading_section_success(client, app, test_writer_id):
    """Test successfully extracting a heading section"""
    with app.app_context():
        page = Page(
            title="Source Page",
            slug="source-page",
            content="# Source\n\n## Section Title\n\nContent under section.\n\n## Next Section\n\nMore content.",
            created_by=test_writer_id,
            updated_by=test_writer_id,
            status="published",
            section="Regression-Testing",
            file_path="source-page.md",
        )
        db.session.add(page)
        db.session.commit()
        page_id = str(page.id)

    with mock_auth(test_writer_id, "writer"):
        response = client.post(
            f"/api/pages/{page_id}/extract-heading",
            json={
                "heading_text": "Section Title",
                "heading_level": 2,
                "new_title": "Extracted Section",
                "new_slug": "extracted-section",
                "promote_as": "child",
            },
            headers=auth_headers(test_writer_id, "writer"),
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "new_page" in data
        assert "original_page" in data
        assert data["new_page"]["title"] == "Extracted Section"


def test_extract_heading_section_not_found(client, app, test_writer_id):
    """Test extracting a heading that doesn't exist"""
    with app.app_context():
        page = Page(
            title="Source Page",
            slug="source-page",
            content="# Source\n\nContent",
            created_by=test_writer_id,
            updated_by=test_writer_id,
            status="published",
            section="Regression-Testing",
            file_path="source-page.md",
        )
        db.session.add(page)
        db.session.commit()
        page_id = str(page.id)

    with mock_auth(test_writer_id, "writer"):
        response = client.post(
            f"/api/pages/{page_id}/extract-heading",
            json={
                "heading_text": "Non-existent Section",
                "heading_level": 2,
                "new_title": "Test",
                "new_slug": "test",
            },
            headers=auth_headers(test_writer_id, "writer"),
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data


def test_extract_heading_section_invalid_level(client, app, test_writer_id):
    """Test extracting with invalid heading level"""
    with app.app_context():
        page = Page(
            title="Source Page",
            slug="source-page",
            content="# Source\n\nContent",
            created_by=test_writer_id,
            updated_by=test_writer_id,
            status="published",
            section="Regression-Testing",
            file_path="source-page.md",
        )
        db.session.add(page)
        db.session.commit()
        page_id = str(page.id)

    with mock_auth(test_writer_id, "writer"):
        # Level too low
        response = client.post(
            f"/api/pages/{page_id}/extract-heading",
            json={
                "heading_text": "Section",
                "heading_level": 1,  # H1 not allowed
                "new_title": "Test",
                "new_slug": "test",
            },
            headers=auth_headers(test_writer_id, "writer"),
        )
        assert response.status_code == 400

        # Level too high
        response = client.post(
            f"/api/pages/{page_id}/extract-heading",
            json={
                "heading_text": "Section",
                "heading_level": 7,  # H7 not allowed
                "new_title": "Test",
                "new_slug": "test",
            },
            headers=auth_headers(test_writer_id, "writer"),
        )
        assert response.status_code == 400


def test_promote_section_from_toc_requires_auth(client):
    """Test that promote section requires authentication"""
    response = client.post(
        f"/api/pages/{uuid.uuid4()}/promote-section",
        json={
            "heading_anchor": "section-title",
            "new_title": "Test",
            "new_slug": "test",
        },
    )
    assert response.status_code == 401


def test_promote_section_from_toc_success(client, app, test_writer_id):
    """Test successfully promoting a section from TOC"""
    with app.app_context():
        page = Page(
            title="Source Page",
            slug="source-page",
            content="# Source\n\n## Section Title\n\nContent under section.",
            created_by=test_writer_id,
            updated_by=test_writer_id,
            status="published",
            section="Regression-Testing",
            file_path="source-page.md",
        )
        db.session.add(page)
        db.session.commit()
        page_id = str(page.id)

    with mock_auth(test_writer_id, "writer"):
        response = client.post(
            f"/api/pages/{page_id}/promote-section",
            json={
                "heading_anchor": "section-title",
                "new_title": "Promoted Section",
                "new_slug": "promoted-section",
                "promote_as": "child",
            },
            headers=auth_headers(test_writer_id, "writer"),
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "new_page" in data
        assert "original_page" in data
        assert data["new_page"]["title"] == "Promoted Section"


def test_promote_section_from_toc_anchor_not_found(client, app, test_writer_id):
    """Test promoting a section with non-existent anchor"""
    with app.app_context():
        page = Page(
            title="Source Page",
            slug="source-page",
            content="# Source\n\nContent",
            created_by=test_writer_id,
            updated_by=test_writer_id,
            status="published",
            section="Regression-Testing",
            file_path="source-page.md",
        )
        db.session.add(page)
        db.session.commit()
        page_id = str(page.id)

    with mock_auth(test_writer_id, "writer"):
        response = client.post(
            f"/api/pages/{page_id}/promote-section",
            json={
                "heading_anchor": "non-existent-anchor",
                "new_title": "Test",
                "new_slug": "test",
            },
            headers=auth_headers(test_writer_id, "writer"),
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data


def test_extract_selection_with_parent(client, app, test_writer_id):
    """Test extracting selection with specific parent"""
    with app.app_context():
        parent = Page(
            title="Parent Page",
            slug="parent-page",
            content="# Parent",
            created_by=test_writer_id,
            updated_by=test_writer_id,
            status="published",
            section="Regression-Testing",
            file_path="parent-page.md",
        )
        db.session.add(parent)
        db.session.flush()

        source = Page(
            title="Source Page",
            slug="source-page",
            content="# Source\n\nContent to extract.",
            created_by=test_writer_id,
            updated_by=test_writer_id,
            status="published",
            section="Regression-Testing",
            file_path="source-page.md",
        )
        db.session.add(source)
        db.session.commit()
        source_id = str(source.id)
        parent_id = str(parent.id)

    with mock_auth(test_writer_id, "writer"):
        response = client.post(
            f"/api/pages/{source_id}/extract",
            json={
                "selection_start": 10,
                "selection_end": 25,
                "new_title": "Extracted",
                "new_slug": "extracted",
                "parent_id": parent_id,
            },
            headers=auth_headers(test_writer_id, "writer"),
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["new_page"]["title"] == "Extracted"


def test_extract_selection_replace_with_link_false(client, app, test_writer_id):
    """Test extracting selection without replacing with link"""
    with app.app_context():
        page = Page(
            title="Source Page",
            slug="source-page",
            content="# Source\n\nContent to extract.",
            created_by=test_writer_id,
            updated_by=test_writer_id,
            status="published",
            section="Regression-Testing",
            file_path="source-page.md",
        )
        db.session.add(page)
        db.session.commit()
        page_id = str(page.id)
        original_content = page.content

    with mock_auth(test_writer_id, "writer"):
        response = client.post(
            f"/api/pages/{page_id}/extract",
            json={
                "selection_start": 10,
                "selection_end": 25,
                "new_title": "Extracted",
                "new_slug": "extracted",
                "replace_with_link": False,
            },
            headers=auth_headers(test_writer_id, "writer"),
        )
        assert response.status_code == 200

        # Verify original content unchanged
        with app.app_context():
            updated_page = db.session.get(Page, uuid.UUID(page_id))
            assert updated_page.content == original_content


def test_extract_heading_promote_as_sibling(client, app, test_writer_id):
    """Test extracting heading as sibling"""
    with app.app_context():
        parent = Page(
            title="Parent Page",
            slug="parent-page",
            content="# Parent",
            created_by=test_writer_id,
            updated_by=test_writer_id,
            status="published",
            section="Regression-Testing",
            file_path="parent-page.md",
        )
        db.session.add(parent)
        db.session.flush()

        source = Page(
            title="Source Page",
            slug="source-page",
            content="# Source\n\n## Section\n\nContent.",
            created_by=test_writer_id,
            updated_by=test_writer_id,
            status="published",
            parent_id=parent.id,
            file_path="source-page.md",
        )
        db.session.add(source)
        db.session.commit()
        source_id = str(source.id)
        parent_id = str(parent.id)  # Store parent ID before context closes

    with mock_auth(test_writer_id, "writer"):
        response = client.post(
            f"/api/pages/{source_id}/extract-heading",
            json={
                "heading_text": "Section",
                "heading_level": 2,
                "new_title": "Sibling Page",
                "new_slug": "sibling-page",
                "promote_as": "sibling",
            },
            headers=auth_headers(test_writer_id, "writer"),
        )
        assert response.status_code == 200

        # Verify new page is sibling (same parent as source)
        with app.app_context():
            new_page = db.session.query(Page).filter_by(slug="sibling-page").first()
            assert new_page is not None
            assert str(new_page.parent_id) == parent_id


def test_extract_selection_response_structure(client, app, test_writer_id):
    """Test that extract selection response matches API spec"""
    with app.app_context():
        page = Page(
            title="Source Page",
            slug="source-page",
            content="# Source\n\nContent.",
            created_by=test_writer_id,
            updated_by=test_writer_id,
            status="published",
            section="Regression-Testing",
            file_path="source-page.md",
        )
        db.session.add(page)
        db.session.commit()
        page_id = str(page.id)

    with mock_auth(test_writer_id, "writer"):
        response = client.post(
            f"/api/pages/{page_id}/extract",
            json={
                "selection_start": 10,
                "selection_end": 18,
                "new_title": "Extracted",
                "new_slug": "extracted",
            },
            headers=auth_headers(test_writer_id, "writer"),
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "new_page" in data
        assert "original_page" in data
        assert "id" in data["new_page"]
        assert "title" in data["new_page"]
        assert "slug" in data["new_page"]
        assert "id" in data["original_page"]
        assert "version" in data["original_page"]
