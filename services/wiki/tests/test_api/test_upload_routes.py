"""Tests for file upload endpoints (images)."""
import io
import uuid

from app import db
from app.models.page import Page
from app.models.image import Image, PageImage
from app.models.wiki_config import WikiConfig
from tests.test_api.conftest import mock_auth, auth_headers, test_writer_id, test_admin_id, test_user_id


def test_upload_image_requires_auth(client):
    """Upload image should require authentication."""
    resp = client.post(
        "/api/upload/image",
        data={"file": (io.BytesIO(b"data"), "test.png")},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 401


def test_upload_image_requires_writer_or_admin(client, app, test_user_id):
    """Non-writer/admin roles should be forbidden."""
    with mock_auth(test_user_id, "viewer"):
        headers = auth_headers(test_user_id, "viewer")
        resp = client.post(
            "/api/upload/image",
            data={"file": (io.BytesIO(b"data"), "test.png")},
            content_type="multipart/form-data",
            headers=headers,
        )
        assert resp.status_code == 403


def test_upload_image_success_basic(client, app, test_writer_id):
    """Writer can upload an image without page association."""
    file_bytes = b"\x89PNG\r\n\x1a\n" + b"0" * 100

    with mock_auth(test_writer_id, "writer"):
        headers = auth_headers(test_writer_id, "writer")
        resp = client.post(
            "/api/upload/image",
            data={"file": (io.BytesIO(file_bytes), "my-image.png")},
            content_type="multipart/form-data",
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "url" in data
        assert data["url"].startswith("/uploads/images/")
        assert "uuid" in data and data["uuid"]
        assert data["original_filename"] == "my-image.png"
        assert data["size"] == len(file_bytes)
        assert data["mime_type"] in ("image/png", None)
        assert data["page_id"] is None

    # Verify Image stored in DB
    with app.app_context():
        img = db.session.query(Image).filter_by(original_filename="my-image.png").first()
        assert img is not None
        assert img.size_bytes == len(file_bytes)


def test_upload_image_with_page_id(client, app, test_writer_id, test_user_id):
    """Upload image associated with a page should create PageImage link."""
    with app.app_context():
        page = Page(
            title="Page",
            slug="page-for-image",
            content="# Page",
            created_by=test_user_id,
            updated_by=test_user_id,
            file_path="page-for-image.md",
        )
        db.session.add(page)
        db.session.commit()
        page_id_str = str(page.id)

    file_bytes = b"JPEGDATA"

    with mock_auth(test_writer_id, "writer"):
        headers = auth_headers(test_writer_id, "writer")
        resp = client.post(
            "/api/upload/image",
            data={
                "file": (io.BytesIO(file_bytes), "photo.jpg"),
                "page_id": page_id_str,
            },
            content_type="multipart/form-data",
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["page_id"] == page_id_str

    with app.app_context():
        # There should be exactly one PageImage record
        page = db.session.get(Page, uuid.UUID(page_id_str))
        assert page is not None
        assert len(page.page_images) == 1
        assert page.page_images[0].image is not None


def test_upload_image_invalid_page_id_format(client, app, test_writer_id):
    """Invalid page_id format should return 400."""
    file_bytes = b"IMG"
    with mock_auth(test_writer_id, "writer"):
        headers = auth_headers(test_writer_id, "writer")
        resp = client.post(
            "/api/upload/image",
            data={
                "file": (io.BytesIO(file_bytes), "img.png"),
                "page_id": "not-a-uuid",
            },
            content_type="multipart/form-data",
            headers=headers,
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert "error" in data


def test_upload_image_page_not_found(client, app, test_writer_id):
    """Non-existent page_id should return 404."""
    file_bytes = b"IMG"
    fake_id = str(uuid.uuid4())

    with mock_auth(test_writer_id, "writer"):
        headers = auth_headers(test_writer_id, "writer")
        resp = client.post(
            "/api/upload/image",
            data={
                "file": (io.BytesIO(file_bytes), "img.png"),
                "page_id": fake_id,
            },
            content_type="multipart/form-data",
            headers=headers,
        )
        assert resp.status_code == 404
        data = resp.get_json()
        assert "error" in data


def test_upload_image_file_size_validation(client, app, test_writer_id, test_user_id):
    """Upload should enforce max size from WikiConfig."""
    with app.app_context():
        cfg = WikiConfig(
            key="upload_max_size_mb",
            value="0.0001",  # Very small (~100 bytes)
            updated_by=test_user_id,
        )
        db.session.add(cfg)
        db.session.commit()

    # Larger than limit
    file_bytes = b"A" * 1000
    with mock_auth(test_writer_id, "writer"):
        headers = auth_headers(test_writer_id, "writer")
        resp = client.post(
            "/api/upload/image",
            data={"file": (io.BytesIO(file_bytes), "big.bin")},
            content_type="multipart/form-data",
            headers=headers,
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data.get("error") == "File too large"
        assert data["size_bytes"] == len(file_bytes)
        assert data["max_size_bytes"] < len(file_bytes)


def test_upload_image_missing_file_field(client, app, test_writer_id):
    """Missing file field should return 400."""
    with mock_auth(test_writer_id, "writer"):
        headers = auth_headers(test_writer_id, "writer")
        resp = client.post(
            "/api/upload/image",
            data={},  # No file field
            content_type="multipart/form-data",
            headers=headers,
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data.get("error") == "file field is required"


def test_upload_image_empty_filename(client, app, test_writer_id):
    """Empty filename should return 400."""
    with mock_auth(test_writer_id, "writer"):
        headers = auth_headers(test_writer_id, "writer")
        resp = client.post(
            "/api/upload/image",
            data={"file": (io.BytesIO(b"data"), "")},  # Empty filename
            content_type="multipart/form-data",
            headers=headers,
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data.get("error") == "No selected file"


def test_upload_image_invalid_config_falls_back_to_default(client, app, test_writer_id, test_user_id):
    """Non-numeric upload_max_size_mb should fall back to default (10MB)."""
    with app.app_context():
        # Set invalid config value
        cfg = WikiConfig(
            key="upload_max_size_mb",
            value="not-a-number",
            updated_by=test_user_id,
        )
        db.session.add(cfg)
        db.session.commit()

    # File under default 10MB limit should succeed
    file_bytes = b"X" * 1000  # 1KB, well under 10MB default
    with mock_auth(test_writer_id, "writer"):
        headers = auth_headers(test_writer_id, "writer")
        resp = client.post(
            "/api/upload/image",
            data={"file": (io.BytesIO(file_bytes), "test.png")},
            content_type="multipart/form-data",
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "url" in data
        assert data["size"] == len(file_bytes)

    # Verify that a file larger than 10MB would be rejected
    large_file_bytes = b"Y" * (11 * 1024 * 1024)  # 11MB, over default 10MB limit
    with mock_auth(test_writer_id, "writer"):
        headers = auth_headers(test_writer_id, "writer")
        resp = client.post(
            "/api/upload/image",
            data={"file": (io.BytesIO(large_file_bytes), "large.png")},
            content_type="multipart/form-data",
            headers=headers,
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data.get("error") == "File too large"
        assert data["max_size_bytes"] == 10 * 1024 * 1024  # Default 10MB


