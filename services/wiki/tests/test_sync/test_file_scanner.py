"""Tests for file scanner"""

import os
import tempfile

import pytest
from app.sync.file_scanner import FileScanner


@pytest.fixture
def temp_pages_dir(app):
    """Create temporary pages directory"""
    temp_dir = tempfile.mkdtemp()
    original_pages_dir = app.config.get("WIKI_PAGES_DIR")
    app.config["WIKI_PAGES_DIR"] = temp_dir

    yield temp_dir

    app.config["WIKI_PAGES_DIR"] = original_pages_dir
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)


def test_scan_directory_empty(temp_pages_dir, app):
    """Test scanning empty directory"""
    with app.app_context():
        files = FileScanner.scan_directory()
        assert files == []


def test_scan_directory_finds_markdown_files(temp_pages_dir, app):
    """Test scanning finds markdown files"""
    with app.app_context():
        # Create test files
        os.makedirs(os.path.join(temp_pages_dir, "section1"), exist_ok=True)
        os.makedirs(os.path.join(temp_pages_dir, "section2"), exist_ok=True)

        with open(os.path.join(temp_pages_dir, "page1.md"), "w") as f:
            f.write("# Page 1")

        with open(os.path.join(temp_pages_dir, "section1", "page2.md"), "w") as f:
            f.write("# Page 2")

        with open(os.path.join(temp_pages_dir, "section2", "page3.md"), "w") as f:
            f.write("# Page 3")

        # Create non-markdown file (should be ignored)
        with open(os.path.join(temp_pages_dir, "readme.txt"), "w") as f:
            f.write("Readme")

        files = FileScanner.scan_directory()

        assert len(files) == 3
        assert "page1.md" in files
        assert "section1/page2.md" in files
        assert "section2/page3.md" in files
        assert "readme.txt" not in files


def test_scan_directory_nested_structure(temp_pages_dir, app):
    """Test scanning nested directory structure"""
    with app.app_context():
        # Create nested structure
        os.makedirs(
            os.path.join(temp_pages_dir, "section", "subsection"), exist_ok=True
        )

        with open(
            os.path.join(temp_pages_dir, "section", "subsection", "nested.md"), "w"
        ) as f:
            f.write("# Nested")

        files = FileScanner.scan_directory()

        assert "section/subsection/nested.md" in files


def test_scan_file_exists(temp_pages_dir, app):
    """Test scanning specific file that exists"""
    with app.app_context():
        with open(os.path.join(temp_pages_dir, "test.md"), "w") as f:
            f.write("# Test")

        result = FileScanner.scan_file("test.md")
        assert result == "test.md"


def test_scan_file_not_exists(temp_pages_dir, app):
    """Test scanning specific file that doesn't exist"""
    with app.app_context():
        result = FileScanner.scan_file("nonexistent.md")
        assert result is None


def test_scan_file_absolute_path(temp_pages_dir, app):
    """Test scanning with absolute path"""
    with app.app_context():
        file_path = os.path.join(temp_pages_dir, "test.md")
        with open(file_path, "w") as f:
            f.write("# Test")

        result = FileScanner.scan_file(file_path)
        assert result == "test.md"


def test_scan_file_absolute_path_outside_directory(temp_pages_dir, app):
    """Test scanning absolute path outside pages directory"""
    with app.app_context():
        # Create file outside pages directory
        outside_dir = tempfile.mkdtemp()
        file_path = os.path.join(outside_dir, "test.md")
        with open(file_path, "w") as f:
            f.write("# Test")

        result = FileScanner.scan_file(file_path)
        assert result is None

        import shutil

        shutil.rmtree(outside_dir, ignore_errors=True)


def test_get_file_modification_time(temp_pages_dir, app):
    """Test getting file modification time"""
    with app.app_context():
        file_path = os.path.join(temp_pages_dir, "test.md")
        with open(file_path, "w") as f:
            f.write("# Test")

        mtime = FileScanner.get_file_modification_time("test.md")
        assert mtime is not None
        assert isinstance(mtime, float)
        assert mtime > 0


def test_get_file_modification_time_not_exists(temp_pages_dir, app):
    """Test getting modification time for non-existent file"""
    with app.app_context():
        mtime = FileScanner.get_file_modification_time("nonexistent.md")
        assert mtime is None
