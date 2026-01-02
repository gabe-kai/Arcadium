"""
Main sync utility for syncing markdown files to database.

For AI agents writing wiki pages:
- Write markdown files with YAML frontmatter to services/wiki/data/pages/
- See docs/wiki-ai-content-management.md for complete instructions
- After writing files, user runs: python -m app.sync sync-all
"""

import hashlib
import os
import time
import uuid
from typing import Dict, Optional, Tuple

from app import db
from app.models.page import Page
from app.services.link_service import LinkService
from app.services.page_service import PageService
from app.services.search_index_service import SearchIndexService
from app.services.version_service import VersionService
from app.sync.file_scanner import FileScanner
from app.utils.markdown_service import parse_frontmatter
from app.utils.slug_generator import generate_slug
from flask import current_app


class SyncUtility:
    """Utility for syncing markdown files to database"""

    def __init__(self, admin_user_id: Optional[uuid.UUID] = None):
        """
        Initialize sync utility.

        Args:
            admin_user_id: UUID of admin user to assign pages to.
                          If None, will try to get from config or use a default.
        """
        self.admin_user_id = admin_user_id or self._get_admin_user_id()
        self.pages_dir = current_app.config.get("WIKI_PAGES_DIR", "data/pages")

    def _get_admin_user_id(self) -> uuid.UUID:
        """
        Get admin user ID from config or use default.

        Returns:
            Admin user UUID
        """
        # Try to get from config
        admin_id_str = current_app.config.get("SYNC_ADMIN_USER_ID")
        if admin_id_str:
            try:
                return uuid.UUID(admin_id_str)
            except ValueError:
                pass

        # Default admin user ID (can be overridden via config)
        # In production, this should be set via environment variable
        default_admin_id = "00000000-0000-0000-0000-000000000001"
        return uuid.UUID(default_admin_id)

    def resolve_parent_slug(self, parent_slug: Optional[str]) -> Optional[uuid.UUID]:
        """
        Resolve parent_slug to parent_id.

        Args:
            parent_slug: Slug of parent page

        Returns:
            Parent page UUID, or None if not found
        """
        if not parent_slug:
            return None

        parent = db.session.query(Page).filter_by(slug=parent_slug).first()
        if parent:
            return parent.id

        return None

    def read_file(self, file_path: str) -> Tuple[Dict, str]:
        """
        Read and parse markdown file.

        Args:
            file_path: Relative file path

        Returns:
            Tuple of (frontmatter_dict, markdown_content)
        """
        full_path = os.path.join(self.pages_dir, file_path)

        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {full_path}")

        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()

        frontmatter, markdown_content = parse_frontmatter(content)
        return frontmatter, markdown_content

    def _compute_content_hash(self, content: str) -> str:
        """
        Compute SHA256 hash of content.

        Args:
            content: Content string to hash

        Returns:
            Hexadecimal hash string
        """
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _get_file_content_hash(self, file_path: str) -> Optional[str]:
        """
        Get content hash of file (reconstructing full content with frontmatter).

        Args:
            file_path: Relative file path

        Returns:
            Content hash string, or None if file cannot be read
        """
        try:
            full_path = os.path.join(self.pages_dir, file_path)
            if not os.path.exists(full_path):
                return None

            with open(full_path, "r", encoding="utf-8") as f:
                file_content = f.read()

            # Reconstruct full content with frontmatter for comparison
            frontmatter, markdown_content = parse_frontmatter(file_content)
            full_content = self._reconstruct_content(frontmatter, markdown_content)

            return self._compute_content_hash(full_content)
        except Exception as e:
            current_app.logger.warning(
                f"Error computing file content hash for {file_path}: {e}"
            )
            return None

    def should_sync_file(self, file_path: str, page: Optional[Page]) -> bool:
        """
        Determine if file should be synced.

        Uses content comparison (hash-based) to skip syncs when content is identical,
        even if timestamps differ. Also includes conflict detection: if database was
        recently updated (within grace period), sync is skipped to protect browser edits.

        Args:
            file_path: Relative file path
            page: Existing page record (None if new)

        Returns:
            True if file should be synced, False if sync should be skipped
        """
        file_mtime = FileScanner.get_file_modification_time(file_path, self.pages_dir)

        if not file_mtime:
            return False

        if not page:
            # New file, should sync
            return True

        # Check if content comparison is enabled (default: True)
        enable_content_comparison = current_app.config.get(
            "SYNC_ENABLE_CONTENT_COMPARISON", True
        )

        # Content comparison: Skip sync if content is identical
        if enable_content_comparison:
            file_hash = self._get_file_content_hash(file_path)
            if file_hash:
                db_hash = self._compute_content_hash(page.content)
                if file_hash == db_hash:
                    # Content is identical, skip sync regardless of timestamps
                    current_app.logger.debug(
                        f"Sync skipped for {file_path} (slug: {page.slug}): "
                        "Content is identical (content hash match)."
                    )
                    return False

        # Content differs - check timestamps and grace period
        if page.updated_at:
            db_time = page.updated_at.timestamp()

            # Check if file is newer than database
            if file_mtime <= db_time:
                # File is not newer, skip sync
                return False

            # File is newer - check for conflict with recent browser edits
            grace_period = current_app.config.get(
                "SYNC_CONFLICT_GRACE_PERIOD_SECONDS", 600
            )  # Default: 10 minutes
            current_time = time.time()
            time_since_db_update = current_time - db_time

            if time_since_db_update < grace_period:
                # Database was updated recently (within grace period)
                # Skip sync to protect browser edits
                current_app.logger.info(
                    f"Sync skipped for {file_path} (slug: {page.slug}): "
                    f"Database was updated {time_since_db_update:.1f}s ago "
                    f"(within {grace_period}s grace period). Browser edits protected."
                )
                return False

            # File is newer and database update was outside grace period, safe to sync
            return True

        # If no updated_at, sync it
        return True

    def sync_file(
        self, file_path: str, force: bool = False
    ) -> Tuple[Page, Optional[bool]]:
        """
        Sync a single file to database.

        Args:
            file_path: Relative file path
            force: Force sync even if file is not newer (bypasses conflict detection)

        Returns:
            Tuple of (Page instance, status: bool|None)
            - True: page was created
            - False: page was updated
            - None: page was skipped (file not newer than DB, or conflict detected)
        """
        # Read file
        frontmatter, markdown_content = self.read_file(file_path)

        # Extract metadata
        slug = frontmatter.get("slug")
        title = frontmatter.get("title", "Untitled")

        # Truncate title if too long (database limit is 255 characters)
        if len(title) > 255:
            current_app.logger.warning(
                f"Title too long ({len(title)} chars) for {file_path}, truncating to 255 characters"
            )
            title = title[:252] + "..."

        if not slug:
            # Generate slug from title
            existing_slugs = [p.slug for p in db.session.query(Page.slug).all()]
            slug = generate_slug(title, existing_slugs)

        # Check if page exists
        page = db.session.query(Page).filter_by(slug=slug).first()

        # Check if should sync
        # - If page doesn't exist, always create it
        # - If page exists and force=False, check if file is newer
        # - If page exists and force=True, always update
        if page and not force:
            if not self.should_sync_file(file_path, page):
                # Page exists but file is not newer, skip sync
                return page, None  # None indicates skipped

        # Resolve parent
        parent_slug = frontmatter.get("parent_slug")
        parent_id = self.resolve_parent_slug(parent_slug)

        # Extract other metadata
        section = frontmatter.get("section")
        order = frontmatter.get("order")
        status = frontmatter.get("status", "published")

        # Store content WITH frontmatter in database (needed for AI content management)
        # Frontend will parse and strip frontmatter for editor display
        full_content = self._reconstruct_content(frontmatter, markdown_content)

        if page:
            # Update existing page
            page.title = title
            page.content = full_content  # Store content with frontmatter for AI system
            page.parent_id = parent_id
            page.section = section
            page.status = status
            page.updated_by = self.admin_user_id

            if order is not None:
                page.order_index = order

            # Recalculate metrics
            from app.utils.size_calculator import (
                calculate_content_size_kb,
                calculate_word_count,
            )

            page.word_count = calculate_word_count(markdown_content)
            page.content_size_kb = calculate_content_size_kb(markdown_content)

            # Update file path
            page.file_path = file_path

            db.session.commit()
            was_created = False
        else:
            # Create new page
            # Pass full_content with frontmatter (needed for AI content management)
            page = PageService.create_page(
                title=title,
                content=full_content,  # Pass content with frontmatter for AI system
                user_id=self.admin_user_id,
                slug=slug,
                parent_id=parent_id,
                section=section,
                status=status,
            )

            if order is not None:
                page.order_index = order

            # Override file_path with actual file location
            page.file_path = file_path
            db.session.commit()
            was_created = True

        # Update links - use page.content (which includes frontmatter, but link extraction handles it)
        LinkService.update_page_links(page.id, page.content)

        # Update search index
        SearchIndexService.index_page(page.id, markdown_content, title=title)

        # Create version if this is an update
        if not was_created:
            VersionService.create_version(
                page_id=page.id,
                user_id=self.admin_user_id,
                change_summary="Synced from file",
            )

        return page, was_created

    def _reconstruct_content(self, frontmatter: Dict, markdown_content: str) -> str:
        """
        Reconstruct full content with frontmatter.

        Args:
            frontmatter: Frontmatter dictionary
            markdown_content: Markdown content without frontmatter

        Returns:
            Full content with frontmatter
        """
        import yaml

        if not frontmatter:
            return markdown_content

        # Convert frontmatter to YAML string
        yaml_str = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)

        # Reconstruct with frontmatter
        return f"---\n{yaml_str}---\n\n{markdown_content}"

    def _cleanup_orphaned_pages(self) -> int:
        """
        Remove pages from database whose files no longer exist.

        Returns:
            Number of pages deleted
        """
        import os

        from app.services.file_service import FileService

        # Find all pages with file_path set
        pages_with_files = (
            db.session.query(Page).filter(Page.file_path.isnot(None)).all()
        )

        deleted_count = 0
        files_on_disk = set(FileScanner.scan_directory(self.pages_dir))

        for page in pages_with_files:
            # Check if file exists on disk
            # First check if the file_path is in the files_on_disk set (exact match)
            file_exists = page.file_path in files_on_disk

            # If not found, also check if the file physically exists on disk
            # (handles cases where file_path format might differ)
            if not file_exists:
                full_path = FileService.get_full_path(page.file_path)
                file_exists = os.path.exists(full_path)

            if not file_exists:
                # File is missing, delete the page
                try:
                    page_id = page.id
                    page_title = page.title
                    page_slug = page.slug
                    page_file_path = page.file_path

                    # Delete related data
                    from app.models.comment import Comment
                    from app.models.index_entry import IndexEntry
                    from app.models.page_version import PageVersion

                    IndexEntry.query.filter_by(page_id=page_id).delete()
                    Comment.query.filter_by(page_id=page_id).delete()
                    PageVersion.query.filter_by(page_id=page_id).delete()

                    # Clean up links
                    LinkService.handle_page_deletion(page_id)

                    # Delete the page
                    db.session.delete(page)

                    # Commit immediately to ensure deletion persists
                    db.session.commit()

                    deleted_count += 1
                    current_app.logger.info(
                        f"Deleted orphaned page: {page_title} (slug: {page_slug}, file_path: {page_file_path})"
                    )
                except Exception as e:
                    current_app.logger.error(
                        f"Error deleting orphaned page {page.id}: {e}"
                    )
                    import traceback

                    current_app.logger.error(traceback.format_exc())
                    db.session.rollback()
                    continue

        if deleted_count > 0:
            current_app.logger.info(f"Cleaned up {deleted_count} orphaned page(s)")

        return deleted_count

    def sync_all(self, force: bool = False) -> Dict[str, int]:
        """
        Sync all markdown files in pages directory.

        Also removes pages from database whose files no longer exist,
        ensuring the database matches the file system state.

        Args:
            force: Force sync even if files are not newer

        Returns:
            Dictionary with sync statistics including 'deleted' count
        """
        files = FileScanner.scan_directory(self.pages_dir)

        stats = {
            "total_files": len(files),
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0,
            "deleted": 0,
        }

        # First, sync all existing files
        for file_path in files:
            try:
                page, status = self.sync_file(file_path, force=force)
                if status is True:
                    stats["created"] += 1
                elif status is False:
                    stats["updated"] += 1
                else:  # status is None (skipped)
                    stats["skipped"] += 1
            except Exception as e:
                # Rollback session on error to prevent cascading failures
                try:
                    db.session.rollback()
                except Exception:
                    pass  # Ignore rollback errors
                current_app.logger.error(f"Error syncing {file_path}: {e}")
                stats["errors"] += 1

        # Then, clean up orphaned pages (pages whose files are missing)
        try:
            stats["deleted"] = self._cleanup_orphaned_pages()
        except Exception as e:
            current_app.logger.error(f"Error cleaning up orphaned pages: {e}")
            # Don't increment errors count for cleanup failures, just log

        return stats

    def sync_directory(self, directory: str, force: bool = False) -> Dict[str, int]:
        """
        Sync all files in a specific directory.

        Args:
            directory: Directory path (relative to pages directory)
            force: Force sync even if files are not newer

        Returns:
            Dictionary with sync statistics
        """
        full_dir = os.path.join(self.pages_dir, directory)

        if not os.path.exists(full_dir):
            raise ValueError(f"Directory not found: {full_dir}")

        # Scan the full pages directory and filter to the specified directory
        all_files = FileScanner.scan_directory(self.pages_dir)

        # Filter to only files in the specified directory
        # Normalize directory path for comparison
        directory_normalized = directory.replace("\\", "/")
        filtered_files = [
            f
            for f in all_files
            if f.startswith(directory_normalized + "/")
            or f == directory_normalized.split("/")[-1] + ".md"
        ]

        stats = {
            "total_files": len(filtered_files),
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0,
        }

        for file_path in filtered_files:
            try:
                page, status = self.sync_file(file_path, force=force)
                if status is True:
                    stats["created"] += 1
                elif status is False:
                    stats["updated"] += 1
                else:  # status is None (skipped)
                    stats["skipped"] += 1
            except Exception as e:
                # Rollback session on error to prevent cascading failures
                try:
                    db.session.rollback()
                except Exception:
                    pass  # Ignore rollback errors
                current_app.logger.error(f"Error syncing {file_path}: {e}")
                stats["errors"] += 1

        return stats
