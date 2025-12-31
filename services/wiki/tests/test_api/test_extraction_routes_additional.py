"""Additional tests for section extraction API endpoints - edge cases"""

import uuid

from app import db
from app.models.page import Page
from tests.test_api.conftest import auth_headers, mock_auth


def test_extract_selection_empty_selection(client, app, test_writer_id):
    """Test extracting empty selection (should fail)"""
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
        # Selection with same start and end (empty)
        response = client.post(
            f"/api/pages/{page_id}/extract",
            json={
                "selection_start": 10,
                "selection_end": 10,
                "new_title": "Test",
                "new_slug": "test",
            },
            headers=auth_headers(test_writer_id, "writer"),
        )
        assert response.status_code == 400


def test_extract_selection_out_of_bounds(client, app, test_writer_id):
    """Test extracting selection that's out of bounds"""
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
        # Selection end beyond content length
        response = client.post(
            f"/api/pages/{page_id}/extract",
            json={
                "selection_start": 0,
                "selection_end": 10000,  # Way beyond content length
                "new_title": "Test",
                "new_slug": "test",
            },
            headers=auth_headers(test_writer_id, "writer"),
        )
        assert response.status_code == 400


def test_extract_selection_negative_bounds(client, app, test_writer_id):
    """Test extracting with negative selection bounds"""
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
            f"/api/pages/{page_id}/extract",
            json={
                "selection_start": -10,
                "selection_end": 10,
                "new_title": "Test",
                "new_slug": "test",
            },
            headers=auth_headers(test_writer_id, "writer"),
        )
        assert response.status_code == 400


def test_extract_heading_section_multiple_same_level(client, app, test_writer_id):
    """Test extracting heading when multiple headings of same level exist"""
    with app.app_context():
        page = Page(
            title="Source Page",
            slug="source-page",
            content="# Source\n\n## First Section\n\nContent 1.\n\n## Second Section\n\nContent 2.",
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
        # Extract first section
        response = client.post(
            f"/api/pages/{page_id}/extract-heading",
            json={
                "heading_text": "First Section",
                "heading_level": 2,
                "new_title": "Extracted First",
                "new_slug": "extracted-first",
            },
            headers=auth_headers(test_writer_id, "writer"),
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["new_page"]["title"] == "Extracted First"


def test_extract_heading_section_nested_headings(client, app, test_writer_id):
    """Test extracting heading section with nested headings"""
    with app.app_context():
        page = Page(
            title="Source Page",
            slug="source-page",
            content="# Source\n\n## Main Section\n\nContent.\n\n### Subsection\n\nSub content.\n\n## Next Section\n\nMore.",
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
        # Extract main section (should include subsection)
        response = client.post(
            f"/api/pages/{page_id}/extract-heading",
            json={
                "heading_text": "Main Section",
                "heading_level": 2,
                "new_title": "Extracted Main",
                "new_slug": "extracted-main",
            },
            headers=auth_headers(test_writer_id, "writer"),
        )
        assert response.status_code == 200

        # Verify extracted content includes subsection
        with app.app_context():
            new_page = db.session.query(Page).filter_by(slug="extracted-main").first()
            assert new_page is not None
            assert "Subsection" in new_page.content
            assert "Sub content" in new_page.content


def test_extract_heading_section_last_section(client, app, test_writer_id):
    """Test extracting the last section (no next heading)"""
    with app.app_context():
        page = Page(
            title="Source Page",
            slug="source-page",
            content="# Source\n\n## First Section\n\nContent 1.\n\n## Last Section\n\nContent 2.",
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
        # Extract last section
        response = client.post(
            f"/api/pages/{page_id}/extract-heading",
            json={
                "heading_text": "Last Section",
                "heading_level": 2,
                "new_title": "Extracted Last",
                "new_slug": "extracted-last",
            },
            headers=auth_headers(test_writer_id, "writer"),
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["new_page"]["title"] == "Extracted Last"


def test_promote_section_invalid_promote_as(client, app, test_writer_id):
    """Test promoting section with invalid promote_as value"""
    with app.app_context():
        page = Page(
            title="Source Page",
            slug="source-page",
            content="# Source\n\n## Section\n\nContent.",
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
                "heading_anchor": "section",
                "new_title": "Test",
                "new_slug": "test",
                "promote_as": "invalid",
            },
            headers=auth_headers(test_writer_id, "writer"),
        )
        assert response.status_code == 400


def test_extract_selection_creates_link(client, app, test_writer_id):
    """Test that extracting selection creates bidirectional link"""
    with app.app_context():
        page = Page(
            title="Source Page",
            slug="source-page",
            content="# Source\n\nContent to extract.",
            created_by=test_writer_id,
            updated_by=test_writer_id,
            status="published",
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
                "selection_end": 25,
                "new_title": "Extracted",
                "new_slug": "extracted",
            },
            headers=auth_headers(test_writer_id, "writer"),
        )
        assert response.status_code == 200

        # Verify link was created
        with app.app_context():
            from app.models.page_link import PageLink

            source_page = db.session.get(Page, uuid.UUID(page_id))
            new_page = db.session.query(Page).filter_by(slug="extracted").first()

            # Check forward link (source -> new)
            forward_link = (
                db.session.query(PageLink)
                .filter_by(from_page_id=source_page.id, to_page_id=new_page.id)
                .first()
            )
            assert forward_link is not None

            # Check reverse link (new -> source)
            reverse_link = (
                db.session.query(PageLink)
                .filter_by(from_page_id=new_page.id, to_page_id=source_page.id)
                .first()
            )
            assert reverse_link is not None


def test_extract_selection_creates_version(client, app, test_writer_id):
    """Test that extracting selection creates version history"""
    with app.app_context():
        page = Page(
            title="Source Page",
            slug="source-page",
            content="# Source\n\nContent to extract.",
            created_by=test_writer_id,
            updated_by=test_writer_id,
            status="published",
            file_path="source-page.md",
        )
        db.session.add(page)
        db.session.commit()
        page_id = str(page.id)
        original_version = page.version

    with mock_auth(test_writer_id, "writer"):
        response = client.post(
            f"/api/pages/{page_id}/extract",
            json={
                "selection_start": 10,
                "selection_end": 25,
                "new_title": "Extracted",
                "new_slug": "extracted",
                "replace_with_link": True,  # Ensure content is updated
            },
            headers=auth_headers(test_writer_id, "writer"),
        )
        assert response.status_code == 200

        # Verify version was created
        with app.app_context():
            from app.models.page_version import PageVersion

            updated_page = db.session.get(Page, uuid.UUID(page_id))
            assert updated_page.version > original_version

            # Check version entry exists (may be at updated version or previous)
            # PageService.update_page increments version, then we create another version
            versions = (
                db.session.query(PageVersion)
                .filter_by(page_id=updated_page.id)
                .order_by(PageVersion.version.desc())
                .all()
            )

            # Should have at least one version with extraction summary
            found_extraction_version = False
            for version in versions:
                if (
                    version.change_summary
                    and "extracted" in version.change_summary.lower()
                ):
                    found_extraction_version = True
                    break
            assert found_extraction_version, "No version found with extraction summary"


def test_extract_heading_with_section(client, app, test_writer_id):
    """Test extracting heading with section specified"""
    with app.app_context():
        page = Page(
            title="Source Page",
            slug="source-page",
            content="# Source\n\n## Section\n\nContent.",
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
                "heading_text": "Section",
                "heading_level": 2,
                "new_title": "Extracted",
                "new_slug": "extracted",
                "section": "Regression-Testing/test-section",
            },
            headers=auth_headers(test_writer_id, "writer"),
        )
        assert response.status_code == 200

        # Verify new page has section
        with app.app_context():
            new_page = db.session.query(Page).filter_by(slug="extracted").first()
            assert new_page is not None
            assert new_page.section == "Regression-Testing/test-section"


def test_extract_selection_page_not_found(client, app, test_writer_id):
    """Test extracting from non-existent page"""
    fake_id = str(uuid.uuid4())

    with mock_auth(test_writer_id, "writer"):
        response = client.post(
            f"/api/pages/{fake_id}/extract",
            json={
                "selection_start": 0,
                "selection_end": 10,
                "new_title": "Test",
                "new_slug": "test",
            },
            headers=auth_headers(test_writer_id, "writer"),
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data


def test_extract_selection_invalid_parent_id(client, app, test_writer_id):
    """Test extracting with invalid parent_id format"""
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
            f"/api/pages/{page_id}/extract",
            json={
                "selection_start": 0,
                "selection_end": 10,
                "new_title": "Test",
                "new_slug": "test",
                "parent_id": "invalid-uuid",
            },
            headers=auth_headers(test_writer_id, "writer"),
        )
        assert response.status_code == 400


def test_extract_heading_case_insensitive(client, app, test_writer_id):
    """Test that heading extraction is case-insensitive"""
    with app.app_context():
        page = Page(
            title="Source Page",
            slug="source-page",
            content="# Source\n\n## Section Title\n\nContent.",
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
        # Try with different case
        response = client.post(
            f"/api/pages/{page_id}/extract-heading",
            json={
                "heading_text": "section title",  # Lowercase
                "heading_level": 2,
                "new_title": "Extracted",
                "new_slug": "extracted",
            },
            headers=auth_headers(test_writer_id, "writer"),
        )
        assert response.status_code == 200
