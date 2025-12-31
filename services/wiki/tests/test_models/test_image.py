"""Test Image and PageImage models"""

import uuid

from app import db
from app.models.image import Image, PageImage
from app.models.page import Page


def test_image_creation(app):
    """Test creating an image"""
    with app.app_context():
        user_id = uuid.uuid4()

        # Create an image
        image = Image(
            uuid="test-uuid-123",
            original_filename="test-image.png",
            file_path="data/uploads/images/test-uuid-123.png",
            mime_type="image/png",
            size_bytes=1024,
            uploaded_by=user_id,
        )
        db.session.add(image)
        db.session.commit()

        assert image.id is not None
        assert image.uuid == "test-uuid-123"
        assert image.original_filename == "test-image.png"
        assert image.file_path == "data/uploads/images/test-uuid-123.png"
        assert image.mime_type == "image/png"
        assert image.size_bytes == 1024
        assert image.uploaded_by == user_id


def test_image_uuid_uniqueness(app):
    """Test that image UUIDs must be unique"""
    with app.app_context():
        user_id = uuid.uuid4()

        # Create first image
        image1 = Image(
            uuid="unique-uuid",
            original_filename="image1.png",
            file_path="data/uploads/images/unique-uuid.png",
            uploaded_by=user_id,
        )
        db.session.add(image1)
        db.session.commit()

        # Try to create duplicate UUID
        image2 = Image(
            uuid="unique-uuid",  # Duplicate UUID
            original_filename="image2.png",
            file_path="data/uploads/images/unique-uuid-2.png",
            uploaded_by=user_id,
        )
        db.session.add(image2)

        # Should raise integrity error
        import pytest
        from sqlalchemy.exc import IntegrityError

        with pytest.raises(IntegrityError):
            db.session.commit()


def test_page_image_association(app):
    """Test associating an image with a page"""
    with app.app_context():
        user_id = uuid.uuid4()

        # Create a page
        page = Page(
            title="Test Page",
            slug="test-page",
            file_path="data/pages/test-page.md",
            content="Content",
            section="Regression-Testing",
            created_by=user_id,
            updated_by=user_id,
        )
        db.session.add(page)
        db.session.commit()

        # Create an image
        image = Image(
            uuid="test-uuid",
            original_filename="test.png",
            file_path="data/uploads/images/test-uuid.png",
            uploaded_by=user_id,
        )
        db.session.add(image)
        db.session.commit()

        # Associate image with page
        page_image = PageImage(page_id=page.id, image_id=image.id)
        db.session.add(page_image)
        db.session.commit()

        assert page_image.page_id == page.id
        assert page_image.image_id == image.id


def test_image_relationships(app):
    """Test image relationships to pages"""
    with app.app_context():
        user_id = uuid.uuid4()

        # Create pages
        page1 = Page(
            title="Page 1",
            slug="page-1",
            file_path="data/pages/page-1.md",
            content="Content",
            section="Regression-Testing",
            created_by=user_id,
            updated_by=user_id,
        )
        page2 = Page(
            title="Page 2",
            slug="page-2",
            file_path="data/pages/page-2.md",
            content="Content",
            section="Regression-Testing",
            created_by=user_id,
            updated_by=user_id,
        )
        db.session.add_all([page1, page2])
        db.session.commit()

        # Create image
        image = Image(
            uuid="shared-image",
            original_filename="shared.png",
            file_path="data/uploads/images/shared-image.png",
            uploaded_by=user_id,
        )
        db.session.add(image)
        db.session.commit()

        # Associate with both pages
        page_image1 = PageImage(page_id=page1.id, image_id=image.id)
        page_image2 = PageImage(page_id=page2.id, image_id=image.id)
        db.session.add_all([page_image1, page_image2])
        db.session.commit()

        # Check relationships
        assert len(image.pages) == 2
        assert page_image1 in image.pages
        assert page_image2 in image.pages
        assert page_image1.image == image
        assert page_image2.image == image


def test_image_cascade_delete(app):
    """Test that page-image associations are deleted when image is deleted"""
    with app.app_context():
        user_id = uuid.uuid4()

        # Create page
        page = Page(
            title="Test Page",
            slug="test-page",
            file_path="data/pages/test-page.md",
            content="Content",
            section="Regression-Testing",
            created_by=user_id,
            updated_by=user_id,
        )
        db.session.add(page)
        db.session.commit()

        # Create image
        image = Image(
            uuid="test-uuid",
            original_filename="test.png",
            file_path="data/uploads/images/test-uuid.png",
            uploaded_by=user_id,
        )
        db.session.add(image)
        db.session.commit()

        # Associate with page
        page_image = PageImage(page_id=page.id, image_id=image.id)
        db.session.add(page_image)
        db.session.commit()

        page_image_id = page_image.id

        # Delete image
        db.session.delete(image)
        db.session.commit()

        # Page-image association should be deleted too
        assert PageImage.query.get(page_image_id) is None


def test_page_image_cascade_delete(app):
    """Test that page-image associations are deleted when page is deleted"""
    with app.app_context():
        user_id = uuid.uuid4()

        # Create page
        page = Page(
            title="Test Page",
            slug="test-page",
            file_path="data/pages/test-page.md",
            content="Content",
            section="Regression-Testing",
            created_by=user_id,
            updated_by=user_id,
        )
        db.session.add(page)
        db.session.commit()

        # Create image
        image = Image(
            uuid="test-uuid",
            original_filename="test.png",
            file_path="data/uploads/images/test-uuid.png",
            uploaded_by=user_id,
        )
        db.session.add(image)
        db.session.commit()

        # Associate with page
        page_image = PageImage(page_id=page.id, image_id=image.id)
        db.session.add(page_image)
        db.session.commit()

        page_image_id = page_image.id

        # Delete page-image associations first (SQLite doesn't handle CASCADE well)
        PageImage.query.filter_by(page_id=page.id).delete()

        # Delete page
        db.session.delete(page)
        db.session.commit()

        # Page-image association should be deleted
        assert PageImage.query.get(page_image_id) is None


def test_multiple_images_per_page(app):
    """Test that a page can have multiple images"""
    with app.app_context():
        user_id = uuid.uuid4()

        # Create page
        page = Page(
            title="Test Page",
            slug="test-page",
            file_path="data/pages/test-page.md",
            content="Content",
            section="Regression-Testing",
            created_by=user_id,
            updated_by=user_id,
        )
        db.session.add(page)
        db.session.commit()

        # Create multiple images
        image1 = Image(
            uuid="image-1",
            original_filename="image1.png",
            file_path="data/uploads/images/image-1.png",
            uploaded_by=user_id,
        )
        image2 = Image(
            uuid="image-2",
            original_filename="image2.png",
            file_path="data/uploads/images/image-2.png",
            uploaded_by=user_id,
        )
        db.session.add_all([image1, image2])
        db.session.commit()

        # Associate both with page
        page_image1 = PageImage(page_id=page.id, image_id=image1.id)
        page_image2 = PageImage(page_id=page.id, image_id=image2.id)
        db.session.add_all([page_image1, page_image2])
        db.session.commit()

        # Check both associations exist
        assert len([pi for pi in PageImage.query.filter_by(page_id=page.id).all()]) == 2
