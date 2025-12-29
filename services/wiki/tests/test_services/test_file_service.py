"""Test file service"""

import os
import shutil
import tempfile
import uuid

from app import db
from app.models.page import Page
from app.services.file_service import FileService


def test_calculate_file_path_root_page(app):
    """Test file path calculation for root page"""
    with app.app_context():
        page = Page(
            title="Test Page",
            slug="test-page",
            content="Content",
            file_path="test-page.md",  # Set initial file_path
            created_by=uuid.uuid4(),
            updated_by=uuid.uuid4(),
        )
        db.session.add(page)
        db.session.commit()

        path = FileService.calculate_file_path(page)
        assert path == "test-page.md"


def test_calculate_file_path_with_section(app):
    """Test file path calculation with section"""
    with app.app_context():
        page = Page(
            title="Test Page",
            slug="test-page",
            content="Content",
            section="game-mechanics",
            file_path=os.path.join("game-mechanics", "test-page.md"),
            created_by=uuid.uuid4(),
            updated_by=uuid.uuid4(),
        )
        db.session.add(page)
        db.session.commit()

        path = FileService.calculate_file_path(page)
        assert path == os.path.join("game-mechanics", "test-page.md")


def test_calculate_file_path_with_parent(app):
    """Test file path calculation with parent"""
    with app.app_context():
        user_id = uuid.uuid4()
        parent = Page(
            title="Parent Page",
            slug="parent-page",
            content="Parent content",
            file_path="parent-page.md",
            created_by=user_id,
            updated_by=user_id,
        )
        db.session.add(parent)
        db.session.commit()

        child = Page(
            title="Child Page",
            slug="child-page",
            content="Child content",
            parent_id=parent.id,
            file_path=os.path.join("parent-page", "child-page.md"),
            created_by=user_id,
            updated_by=user_id,
        )
        db.session.add(child)
        db.session.commit()

        path = FileService.calculate_file_path(child)
        assert path == os.path.join("parent-page", "child-page.md")


def test_calculate_file_path_nested_hierarchy(app):
    """Test file path calculation with nested parent hierarchy"""
    with app.app_context():
        user_id = uuid.uuid4()
        grandparent = Page(
            title="Grandparent",
            slug="grandparent",
            content="Content",
            file_path="grandparent.md",
            created_by=user_id,
            updated_by=user_id,
        )
        db.session.add(grandparent)
        db.session.commit()

        parent = Page(
            title="Parent",
            slug="parent",
            content="Content",
            parent_id=grandparent.id,
            file_path=os.path.join("grandparent", "parent.md"),
            created_by=user_id,
            updated_by=user_id,
        )
        db.session.add(parent)
        db.session.commit()

        child = Page(
            title="Child",
            slug="child",
            content="Content",
            parent_id=parent.id,
            file_path=os.path.join("grandparent", "parent", "child.md"),
            created_by=user_id,
            updated_by=user_id,
        )
        db.session.add(child)
        db.session.commit()

        path = FileService.calculate_file_path(child)
        expected = os.path.join("grandparent", "parent", "child.md")
        assert path == expected


def test_write_and_read_page_file(app):
    """Test writing and reading page files"""
    with app.app_context():
        # Create temporary directory for test
        temp_dir = tempfile.mkdtemp()
        app.config["WIKI_PAGES_DIR"] = temp_dir

        try:
            page = Page(
                title="Test Page",
                slug="test-page",
                content="Test content",
                file_path="test-page.md",
                created_by=uuid.uuid4(),
                updated_by=uuid.uuid4(),
            )
            db.session.add(page)
            db.session.commit()

            content = "---\ntitle: Test Page\n---\n# Test Page\n\nContent here."
            FileService.write_page_file(page, content)

            # Verify file exists
            full_path = FileService.get_full_path(page.file_path)
            assert os.path.exists(full_path)

            # Read it back
            read_content = FileService.read_page_file(page)
            assert read_content == content
        finally:
            shutil.rmtree(temp_dir)


def test_delete_page_file(app):
    """Test deleting page files"""
    with app.app_context():
        temp_dir = tempfile.mkdtemp()
        app.config["WIKI_PAGES_DIR"] = temp_dir

        try:
            page = Page(
                title="Test Page",
                slug="test-page",
                content="Test content",
                file_path="test-page.md",
                created_by=uuid.uuid4(),
                updated_by=uuid.uuid4(),
            )
            db.session.add(page)
            db.session.commit()

            # Write file
            content = "Test content"
            FileService.write_page_file(page, content)

            # Delete it
            FileService.delete_page_file(page)

            # Verify file is gone
            full_path = FileService.get_full_path(page.file_path)
            assert not os.path.exists(full_path)
        finally:
            # Clean up temp directory if it still exists
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)


def test_move_page_file(app):
    """Test moving page files"""
    with app.app_context():
        temp_dir = tempfile.mkdtemp()
        app.config["WIKI_PAGES_DIR"] = temp_dir

        try:
            page = Page(
                title="Test Page",
                slug="test-page",
                content="Test content",
                file_path="old-path.md",
                created_by=uuid.uuid4(),
                updated_by=uuid.uuid4(),
            )
            db.session.add(page)
            db.session.commit()

            # Write file at old location
            content = "Test content"
            FileService.write_page_file(page, content)

            # Move to new location
            new_path = "new-path.md"
            FileService.move_page_file(page, page.file_path, new_path)

            # Verify old file is gone and new file exists
            old_full = FileService.get_full_path("old-path.md")
            new_full = FileService.get_full_path(new_path)
            assert not os.path.exists(old_full)
            assert os.path.exists(new_full)
        finally:
            shutil.rmtree(temp_dir)
