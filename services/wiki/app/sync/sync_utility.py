"""
Main sync utility for syncing markdown files to database.

For AI agents writing wiki pages:
- Write markdown files with YAML frontmatter to services/wiki/data/pages/
- See docs/wiki-ai-content-management.md for complete instructions
- After writing files, user runs: python -m app.sync sync-all
"""
import os
import uuid
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from flask import current_app
from app import db
from app.models.page import Page
from app.sync.file_scanner import FileScanner
from app.utils.markdown_service import parse_frontmatter
from app.services.page_service import PageService
from app.services.link_service import LinkService
from app.services.search_index_service import SearchIndexService
from app.services.version_service import VersionService
from app.utils.slug_generator import generate_slug


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
        self.pages_dir = current_app.config.get('WIKI_PAGES_DIR', 'data/pages')
    
    def _get_admin_user_id(self) -> uuid.UUID:
        """
        Get admin user ID from config or use default.
        
        Returns:
            Admin user UUID
        """
        # Try to get from config
        admin_id_str = current_app.config.get('SYNC_ADMIN_USER_ID')
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
        
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        frontmatter, markdown_content = parse_frontmatter(content)
        return frontmatter, markdown_content
    
    def should_sync_file(self, file_path: str, page: Optional[Page]) -> bool:
        """
        Determine if file should be synced (newer than database record).
        
        Args:
            file_path: Relative file path
            page: Existing page record (None if new)
            
        Returns:
            True if file should be synced
        """
        file_mtime = FileScanner.get_file_modification_time(file_path, self.pages_dir)
        
        if not file_mtime:
            return False
        
        if not page:
            # New file, should sync
            return True
        
        # Compare file modification time with database updated_at
        if page.updated_at:
            db_time = page.updated_at.timestamp()
            return file_mtime > db_time
        
        # If no updated_at, sync it
        return True
    
    def sync_file(self, file_path: str, force: bool = False) -> Tuple[Page, Optional[bool]]:
        """
        Sync a single file to database.
        
        Args:
            file_path: Relative file path
            force: Force sync even if file is not newer
            
        Returns:
            Tuple of (Page instance, status: bool|None)
            - True: page was created
            - False: page was updated
            - None: page was skipped (not newer than DB)
        """
        # Read file
        frontmatter, markdown_content = self.read_file(file_path)
        
        # Extract metadata
        slug = frontmatter.get('slug')
        title = frontmatter.get('title', 'Untitled')
        
        # Truncate title if too long (database limit is 255 characters)
        if len(title) > 255:
            current_app.logger.warning(f"Title too long ({len(title)} chars) for {file_path}, truncating to 255 characters")
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
        parent_slug = frontmatter.get('parent_slug')
        parent_id = self.resolve_parent_slug(parent_slug)
        
        # Extract other metadata
        section = frontmatter.get('section')
        order = frontmatter.get('order')
        status = frontmatter.get('status', 'published')
        
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
            from app.utils.size_calculator import calculate_word_count, calculate_content_size_kb
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
                status=status
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
                change_summary="Synced from file"
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
    
    def sync_all(self, force: bool = False) -> Dict[str, int]:
        """
        Sync all markdown files in pages directory.
        
        Args:
            force: Force sync even if files are not newer
            
        Returns:
            Dictionary with sync statistics
        """
        files = FileScanner.scan_directory(self.pages_dir)
        
        stats = {
            'total_files': len(files),
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0
        }
        
        for file_path in files:
            try:
                page, status = self.sync_file(file_path, force=force)
                if status is True:
                    stats['created'] += 1
                elif status is False:
                    stats['updated'] += 1
                else:  # status is None (skipped)
                    stats['skipped'] += 1
            except Exception as e:
                # Rollback session on error to prevent cascading failures
                try:
                    db.session.rollback()
                except Exception:
                    pass  # Ignore rollback errors
                current_app.logger.error(f"Error syncing {file_path}: {e}")
                stats['errors'] += 1
        
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
        directory_normalized = directory.replace('\\', '/')
        filtered_files = [
            f for f in all_files 
            if f.startswith(directory_normalized + '/') or f == directory_normalized.split('/')[-1] + '.md'
        ]
        
        stats = {
            'total_files': len(filtered_files),
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0
        }
        
        for file_path in filtered_files:
            try:
                page, status = self.sync_file(file_path, force=force)
                if status is True:
                    stats['created'] += 1
                elif status is False:
                    stats['updated'] += 1
                else:  # status is None (skipped)
                    stats['skipped'] += 1
            except Exception as e:
                # Rollback session on error to prevent cascading failures
                try:
                    db.session.rollback()
                except Exception:
                    pass  # Ignore rollback errors
                current_app.logger.error(f"Error syncing {file_path}: {e}")
                stats['errors'] += 1
        
        return stats

