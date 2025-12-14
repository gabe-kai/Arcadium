"""Page service for CRUD operations and business logic"""
import uuid
from typing import Optional, List, Dict
from flask import current_app
from sqlalchemy.exc import IntegrityError
from app import db
from app.models.page import Page
from app.models.page_version import PageVersion
from app.models.page_link import PageLink
from app.services.file_service import FileService
from app.utils.slug_generator import generate_slug, validate_slug
from app.utils.size_calculator import calculate_word_count, calculate_content_size_kb
from app.utils.toc_service import generate_toc
from app.utils.markdown_service import parse_frontmatter, extract_internal_links
import yaml


class PageService:
    """Service for managing wiki pages"""
    
    @staticmethod
    def create_page(
        title: str,
        content: str,
        user_id: uuid.UUID,
        slug: Optional[str] = None,
        parent_id: Optional[uuid.UUID] = None,
        section: Optional[str] = None,
        status: str = 'published',
        is_public: bool = True
    ) -> Page:
        """
        Create a new page.
        
        Args:
            title: Page title
            content: Markdown content
            user_id: ID of user creating the page
            slug: Optional custom slug (auto-generated if not provided)
            parent_id: Optional parent page ID
            section: Optional section name
            status: 'published' or 'draft'
            is_public: Whether page is publicly visible
            
        Returns:
            Created Page instance
            
        Raises:
            ValueError: If slug is invalid or already exists
        """
        # Generate slug if not provided
        if not slug:
            existing_slugs = [p.slug for p in Page.query.with_entities(Page.slug).all()]
            slug = generate_slug(title, existing_slugs)
        else:
            if not validate_slug(slug):
                raise ValueError(f"Invalid slug format: {slug}")
            
            # Check uniqueness
            if Page.query.filter_by(slug=slug).first():
                raise ValueError(f"Slug already exists: {slug}")
        
        # Parse frontmatter if present
        frontmatter, markdown_content = parse_frontmatter(content)
        
        # Calculate metrics
        word_count = calculate_word_count(markdown_content)
        content_size_kb = calculate_content_size_kb(markdown_content)
        
        # Create page
        page = Page(
            title=title,
            slug=slug,
            content=content,
            parent_id=parent_id,
            section=section,
            status=status,
            is_public=is_public,
            word_count=word_count,
            content_size_kb=content_size_kb,
            created_by=user_id,
            updated_by=user_id
        )
        
        # Calculate and set file path
        page.file_path = FileService.calculate_file_path(page)
        
        db.session.add(page)
        
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ValueError(f"Failed to create page: slug may already exist")
        
        # Write file to disk
        # Use values we already have to avoid SQLAlchemy lazy loading issues
        file_content = PageService._build_file_content_from_values(
            title=title,
            slug=slug,
            parent_id=parent_id,
            section=section,
            status=status,
            frontmatter=frontmatter,
            markdown_content=markdown_content
        )
        FileService.write_page_file(page, file_content)
        
        # Create initial version
        PageService._create_version(page, user_id, "Initial version")
        
        return page
    
    @staticmethod
    def update_page(
        page_id: uuid.UUID,
        user_id: uuid.UUID,
        title: Optional[str] = None,
        content: Optional[str] = None,
        slug: Optional[str] = None,
        parent_id: Optional[uuid.UUID] = None,
        section: Optional[str] = None,
        status: Optional[str] = None,
        is_public: Optional[bool] = None
    ) -> Page:
        """
        Update an existing page.
        
        Args:
            page_id: ID of page to update
            user_id: ID of user making the update
            title: Optional new title
            content: Optional new content
            slug: Optional new slug
            parent_id: Optional new parent ID
            section: Optional new section
            status: Optional new status
            is_public: Optional new public flag
            
        Returns:
            Updated Page instance
            
        Raises:
            ValueError: If page not found or slug invalid/duplicate
        """
        page = Page.query.get(page_id)
        if not page:
            raise ValueError(f"Page not found: {page_id}")
        
        old_file_path = page.file_path
        old_content = page.content
        
        # Update fields
        if title is not None:
            page.title = title
        
        if content is not None:
            page.content = content
        
        if slug is not None:
            if not validate_slug(slug):
                raise ValueError(f"Invalid slug format: {slug}")
            
            # Check uniqueness (excluding current page)
            existing = Page.query.filter_by(slug=slug).first()
            if existing and existing.id != page_id:
                raise ValueError(f"Slug already exists: {slug}")
            
            page.slug = slug
        
        if parent_id is not None:
            # Validate parent exists and isn't creating a cycle
            if parent_id:
                parent = Page.query.get(parent_id)
                if not parent:
                    raise ValueError(f"Parent page not found: {parent_id}")
                
                # Check for cycles
                current = parent
                while current:
                    if current.id == page_id:
                        raise ValueError("Cannot set parent: would create circular reference")
                    current = current.parent
                
                page.parent_id = parent_id
            else:
                page.parent_id = None
        
        if section is not None:
            page.section = section
        
        if status is not None:
            page.status = status
        
        if is_public is not None:
            page.is_public = is_public
        
        # Recalculate metrics if content changed
        if content is not None:
            frontmatter, markdown_content = parse_frontmatter(content)
            page.word_count = calculate_word_count(markdown_content)
            page.content_size_kb = calculate_content_size_kb(markdown_content)
        
        page.updated_by = user_id
        
        # Recalculate file path if structure changed
        new_file_path = FileService.calculate_file_path(page)
        if new_file_path != old_file_path:
            page.file_path = new_file_path
            # Move file if path changed
            FileService.move_page_file(page, old_file_path, new_file_path)
        else:
            # Update file content
            frontmatter, markdown_content = parse_frontmatter(page.content)
            file_content = PageService._build_file_content_from_values(
                title=page.title,
                slug=page.slug,
                parent_id=page.parent_id,
                section=page.section,
                status=page.status,
                frontmatter=frontmatter,
                markdown_content=markdown_content
            )
            FileService.write_page_file(page, file_content)
        
        db.session.commit()
        
        # Create version if content changed
        if content is not None and content != old_content:
            PageService._create_version(page, user_id, "Page updated")
        
        return page
    
    @staticmethod
    def delete_page(page_id: uuid.UUID, user_id: uuid.UUID) -> Dict:
        """
        Delete a page and handle orphaned children.
        
        Args:
            page_id: ID of page to delete
            user_id: ID of user deleting the page
            
        Returns:
            Dict with 'deleted_page' and 'orphaned_pages' list
            
        Raises:
            ValueError: If page not found or is system page
        """
        page = Page.query.get(page_id)
        if not page:
            raise ValueError(f"Page not found: {page_id}")
        
        if page.is_system_page:
            raise ValueError("Cannot delete system pages")
        
        # Get children and page info before deletion
        children = Page.query.filter_by(parent_id=page_id).all()
        orphaned_pages = []
        
        # Store page info before deletion
        page_info = {
            'id': str(page_id),
            'title': page.title,
            'slug': page.slug
        }
        
        # Store children info before deletion
        for child in children:
            orphaned_pages.append({
                'id': str(child.id),
                'title': child.title,
                'slug': child.slug
            })
        
        # Delete file
        FileService.delete_page_file(page)
        
        # Delete related versions first (SQLite doesn't handle CASCADE well)
        from app.models.page_version import PageVersion
        PageVersion.query.filter_by(page_id=page_id).delete()
        
        # Delete page
        db.session.delete(page)
        db.session.commit()
        
        # Handle orphans (will be done by OrphanageService in Phase 4.2)
        # For now, just return the list
        return {
            'deleted_page': page_info,
            'orphaned_pages': orphaned_pages
        }
    
    @staticmethod
    def get_page(page_id: uuid.UUID, user_role: str = 'viewer', user_id: Optional[uuid.UUID] = None) -> Optional[Page]:
        """
        Get a page by ID with permission checking.
        
        Args:
            page_id: ID of page to retrieve
            user_role: Role of requesting user ('viewer', 'player', 'writer', 'admin')
            user_id: Optional user ID for draft visibility check
            
        Returns:
            Page instance or None if not found/not accessible
        """
        page = Page.query.get(page_id)
        if not page:
            return None
        
        # Check draft visibility
        if page.status == 'draft':
            # Only writers and admins can see drafts
            # Writers can see their own drafts, admins can see all
            if user_role not in ['writer', 'admin']:
                return None
            
            if user_role == 'writer' and user_id and page.created_by != user_id:
                return None
        
        return page
    
    @staticmethod
    def list_pages(
        user_role: str = 'viewer',
        user_id: Optional[uuid.UUID] = None,
        parent_id: Optional[uuid.UUID] = None,
        section: Optional[str] = None,
        status: Optional[str] = None,
        include_drafts: bool = False
    ) -> List[Page]:
        """
        List pages with filtering and permission checking.
        
        Args:
            user_role: Role of requesting user
            user_id: Optional user ID for draft filtering
            parent_id: Filter by parent ID
            section: Filter by section
            status: Filter by status ('published' or 'draft')
            include_drafts: Whether to include drafts (requires writer/admin role)
            
        Returns:
            List of Page instances
        """
        query = Page.query
        
        # Filter by parent
        if parent_id is not None:
            query = query.filter_by(parent_id=parent_id)
        else:
            # Only root pages (no parent)
            query = query.filter(Page.parent_id.is_(None))
        
        # Filter by section
        if section is not None:
            query = query.filter_by(section=section)
        
        # Filter by status
        if status:
            query = query.filter_by(status=status)
        elif not include_drafts:
            # Draft visibility based on role
            if user_role in ['writer', 'admin']:
                if user_id:
                    # Show published + own drafts
                    from sqlalchemy import or_, and_
                    query = query.filter(
                        or_(
                            Page.status == 'published',
                            and_(Page.status == 'draft', Page.created_by == user_id)
                        )
                    )
                else:
                    # No user ID, only published
                    query = query.filter_by(status='published')
            else:
                # Viewers/players only see published
                query = query.filter_by(status='published')
        
        return query.order_by(Page.order_index, Page.title).all()
    
    @staticmethod
    def can_edit(page: Page, user_role: str, user_id: Optional[uuid.UUID]) -> bool:
        """Check if user can edit a page"""
        if user_role == 'admin':
            return True
        if user_role == 'writer':
            # Writers can only edit pages they created
            return user_id is not None and page.created_by == user_id
        return False
    
    @staticmethod
    def can_delete(page: Page, user_role: str, user_id: Optional[uuid.UUID]) -> bool:
        """Check if user can delete a page"""
        if page.is_system_page:
            return False  # System pages cannot be deleted
        if user_role == 'admin':
            return True
        if user_role == 'writer':
            # Writers can only delete pages they created
            return user_id is not None and page.created_by == user_id
        return False
    
    @staticmethod
    def _build_file_content(page: Page, frontmatter: Dict, markdown_content: str) -> str:
        """Build complete file content with frontmatter"""
        # Update frontmatter with page metadata
        frontmatter['title'] = page.title
        frontmatter['slug'] = page.slug
        if page.parent_id:
            parent = Page.query.get(page.parent_id)
            if parent:
                frontmatter['parent_slug'] = parent.slug
        if page.section:
            frontmatter['section'] = page.section
        if page.status:
            frontmatter['status'] = page.status
        
        # Build YAML frontmatter
        frontmatter_yaml = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
        
        return f"---\n{frontmatter_yaml}---\n{markdown_content}"
    
    @staticmethod
    def _build_file_content_from_values(
        title: str,
        slug: str,
        parent_id: Optional[uuid.UUID],
        section: Optional[str],
        status: str,
        frontmatter: Dict,
        markdown_content: str
    ) -> str:
        """Build complete file content with frontmatter from values (avoids lazy loading)"""
        # Update frontmatter with page metadata
        frontmatter['title'] = title
        frontmatter['slug'] = slug
        # Note: parent_slug is optional and can be added later if needed
        # We skip parent lookup here to avoid SQLite UUID conversion issues
        if section:
            frontmatter['section'] = section
        if status:
            frontmatter['status'] = status
        
        # Build YAML frontmatter
        frontmatter_yaml = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
        
        return f"---\n{frontmatter_yaml}---\n{markdown_content}"
    
    @staticmethod
    def _create_version(page: Page, user_id: uuid.UUID, change_summary: str):
        """Create a version record for a page"""
        # Get previous version for diff calculation
        prev_version = PageVersion.query.filter_by(
            page_id=page.id
        ).order_by(PageVersion.version.desc()).first()
        
        # Calculate simple diff data (store as JSON)
        diff_data = {}
        if prev_version:
            # Simple diff: store line-by-line comparison
            old_lines = prev_version.content.split('\n')
            new_lines = page.content.split('\n')
            diff_data = {
                'old_line_count': len(old_lines),
                'new_line_count': len(new_lines),
                'lines_added': max(0, len(new_lines) - len(old_lines)),
                'lines_removed': max(0, len(old_lines) - len(new_lines))
            }
        
        # Create version with current page version number
        version = PageVersion(
            page_id=page.id,
            title=page.title,
            content=page.content,
            change_summary=change_summary,
            changed_by=user_id,
            version=page.version,
            diff_data=diff_data
        )
        
        db.session.add(version)
        
        # Increment page version
        page.version += 1
        db.session.commit()

