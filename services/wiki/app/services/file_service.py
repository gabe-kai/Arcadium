"""File system operations for wiki pages"""

import os
import shutil
from typing import Optional

from app import db
from app.models.page import Page
from flask import current_app


class FileService:
    """Service for managing wiki page files"""

    @staticmethod
    def calculate_file_path(page: Page, parent: Optional[Page] = None) -> str:
        """
        Calculate file path for a page based on section and parent hierarchy.

        Path structure:
        - Base: data/pages/
        - Section: {section}/ (if section exists)
        - Parent hierarchy: {parent_slug}/ (if parent exists, recursively)
        - Filename: {slug}.md

        Args:
            page: Page model instance
            parent: Parent page (if not already loaded)

        Returns:
            Relative file path (e.g., "game-mechanics/combat.md")
        """
        relative_path = ""

        # Access page attributes safely (handle SQLite UUID conversion issues)
        try:
            page_section = page.section
            page_slug = page.slug
            page_parent_id = page.parent_id
        except Exception:
            # If accessing attributes fails (SQLite UUID issues), use fallback
            # This shouldn't happen in normal operation, but handle gracefully
            page_section = None
            page_slug = "page"
            page_parent_id = None

        # Add section directory if section exists
        if page_section:
            relative_path = page_section

        # Add parent hierarchy
        if page_parent_id:
            if not parent:
                try:
                    # Use session.get() for better SQLite compatibility
                    parent = db.session.get(Page, page_parent_id)
                except Exception:
                    # If parent lookup fails (e.g., SQLite UUID issues), skip parent path
                    parent = None

            if parent:
                try:
                    # Get parent's directory path (recursive)
                    parent_path = FileService._get_parent_directory_path(parent)
                    if parent_path:
                        if relative_path:
                            relative_path = os.path.join(relative_path, parent_path)
                        else:
                            relative_path = parent_path
                except Exception:
                    # If parent path calculation fails, skip it
                    pass

        # Add filename
        filename = f"{page_slug}.md"

        if relative_path:
            return os.path.join(relative_path, filename)
        return filename

    @staticmethod
    def _get_parent_directory_path(page: Page) -> str:
        """Get directory path for a page (recursive through parents)"""
        parts = []
        current = page
        visited = set()  # Prevent infinite loops

        # Build path from current page up to root
        while current and current.id not in visited:
            visited.add(current.id)
            parts.insert(0, current.slug)
            if current.parent_id:
                try:
                    current = db.session.get(Page, current.parent_id)
                except Exception:
                    # If parent lookup fails (e.g., SQLite UUID issues), stop
                    break
            else:
                break

        return os.path.join(*parts) if parts else ""

    @staticmethod
    def get_full_path(relative_path: str) -> str:
        """Get full filesystem path from relative path"""
        base_path = current_app.config.get("WIKI_PAGES_DIR", "data/pages")
        return os.path.join(base_path, relative_path)

    @staticmethod
    def ensure_directory_exists(file_path: str):
        """Ensure the directory for a file exists"""
        directory = os.path.dirname(file_path)
        if directory:
            os.makedirs(directory, exist_ok=True)

    @staticmethod
    def read_page_file(page: Page) -> str:
        """
        Read page content from file system.

        Args:
            page: Page model instance

        Returns:
            File content as string
        """
        full_path = FileService.get_full_path(page.file_path)

        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Page file not found: {full_path}")

        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def write_page_file(page: Page, content: str, file_path: str = None):
        """
        Write page content to file system.
        Creates directory structure if needed.

        Args:
            page: Page model instance
            content: Markdown content with YAML frontmatter
            file_path: Optional file path (if not provided, uses page.file_path)
        """
        # Get file_path, handling SQLite UUID conversion issues
        if not file_path:
            try:
                file_path = page.file_path
            except (AttributeError, TypeError):
                # SQLite UUID conversion issue - try to get from session
                try:
                    page_obj = db.session.get(Page, page.id)
                    file_path = page_obj.file_path if page_obj else None
                except Exception:
                    file_path = None

        if not file_path:
            raise ValueError(f"Page file_path not set: {page.id}")

        full_path = FileService.get_full_path(file_path)
        FileService.ensure_directory_exists(full_path)

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)

    @staticmethod
    def delete_page_file(page: Page):
        """
        Delete page file from file system.

        Args:
            page: Page model instance
        """
        full_path = FileService.get_full_path(page.file_path)

        if os.path.exists(full_path):
            os.remove(full_path)

            # Clean up empty directories
            FileService._cleanup_empty_directories(os.path.dirname(full_path))

    @staticmethod
    def move_page_file(page: Page, old_path: str, new_path: str):
        """
        Move page file when structure changes.

        Args:
            page: Page model instance
            old_path: Old relative file path
            new_path: New relative file path
        """
        old_full = FileService.get_full_path(old_path)
        new_full = FileService.get_full_path(new_path)

        if os.path.exists(old_full):
            FileService.ensure_directory_exists(new_full)
            shutil.move(old_full, new_full)

            # Clean up old empty directories
            FileService._cleanup_empty_directories(os.path.dirname(old_full))

    @staticmethod
    def _cleanup_empty_directories(directory: str):
        """Recursively remove empty directories"""
        base_path = current_app.config.get("WIKI_PAGES_DIR", "data/pages")

        try:
            # Only clean up directories within the pages directory
            abs_dir = os.path.abspath(directory)
            abs_base = os.path.abspath(base_path)

            if not abs_dir.startswith(abs_base):
                return  # Don't clean up outside our directory

            # Remove directory if empty
            if os.path.exists(directory) and not os.listdir(directory):
                os.rmdir(directory)

                # Recursively check parent
                parent = os.path.dirname(directory)
                if parent and parent != base_path:
                    FileService._cleanup_empty_directories(parent)
        except OSError:
            # Directory not empty or other error, ignore
            pass
