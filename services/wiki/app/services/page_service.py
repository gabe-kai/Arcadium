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
        
        # Store values before commit to avoid SQLite UUID issues
        stored_file_path = page.file_path
        stored_title = page.title
        stored_content = page.content
        stored_version = page.version
        
        db.session.add(page)
        
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ValueError(f"Failed to create page: slug may already exist")
        
        # Get page_id after commit using raw SQL (avoid SQLite UUID issues)
        try:
            result = db.session.execute(
                db.text("SELECT id FROM pages WHERE slug = :slug"),
                {"slug": slug}
            ).first()
            if result:
                # Convert string UUID to UUID object if needed
                import uuid
                stored_page_id = uuid.UUID(result[0]) if isinstance(result[0], str) else result[0]
            else:
                raise ValueError(f"Could not retrieve page after creation: {slug}")
        except Exception as e:
            raise ValueError(f"Could not retrieve page ID after creation: {slug} - {str(e)}")
        
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
        FileService.write_page_file(page, file_content, file_path=stored_file_path)
        
        # Create initial version
        # Pass stored values to avoid SQLite UUID issues
        PageService._create_version(
            page, user_id, "Initial version",
            page_id=stored_page_id,
            page_slug=slug,
            page_title=stored_title,
            page_content=stored_content,
            page_version=stored_version
        )
        
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
        
        # Store original version before version creation
        original_version = page.version
        
        # Create version if content changed
        if content is not None and content != old_content:
            PageService._create_version(page, user_id, "Page updated")
            # The version was incremented in the database via raw SQL in _create_version
            # Manually increment the page object's version to reflect the database change
            # This is necessary because the page object is stale after _create_version commits
            page.version = original_version + 1
        
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
        
        # Clean up links before deletion
        from app.services.link_service import LinkService
        LinkService.handle_page_deletion(page_id)
        
        # Delete file
        FileService.delete_page_file(page)
        
        # Delete related versions first (SQLite doesn't handle CASCADE well)
        from app.models.page_version import PageVersion
        PageVersion.query.filter_by(page_id=page_id).delete()
        
        # Delete page
        db.session.delete(page)
        db.session.commit()
        
        # Handle orphans using OrphanageService
        orphaned_page_objects = []
        if orphaned_pages:
            from app.services.orphanage_service import OrphanageService
            child_ids = [uuid.UUID(child['id']) for child in orphaned_pages]
            orphaned_page_objects = OrphanageService.orphan_pages(child_ids, page_id)  # page_id is the deleted parent
        
        return {
            'deleted_page': page_info,
            'orphaned_pages': orphaned_page_objects  # Return Page objects, not dicts
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
    def _create_version(
        page: Page, user_id: uuid.UUID, change_summary: str,
        page_id: Optional[uuid.UUID] = None,
        page_slug: Optional[str] = None,
        page_title: Optional[str] = None,
        page_content: Optional[str] = None,
        page_version: Optional[int] = None
    ):
        """Create a version record for a page"""
        # Get page_id, handling SQLite UUID conversion issues
        if not page_id:
            try:
                page_id = page.id
            except (AttributeError, TypeError):
                # SQLite UUID conversion issue - use raw SQL to get page ID
                if page_slug:
                    try:
                        # Use raw SQL to avoid SQLAlchemy UUID conversion issues
                        result = db.session.execute(
                            db.text("SELECT id FROM pages WHERE slug = :slug"),
                            {"slug": page_slug}
                        ).first()
                        if result:
                            # Convert string UUID to UUID object
                            import uuid
                            page_id = uuid.UUID(result[0]) if isinstance(result[0], str) else result[0]
                    except Exception as e:
                        # If raw SQL also fails, try one more time with Page.query
                        try:
                            page_from_db = Page.query.filter_by(slug=page_slug).first()
                            if page_from_db:
                                page_id = page_from_db.id
                        except:
                            page_id = None
                else:
                    page_id = None
        
        if not page_id:
            raise ValueError(f"Page ID not available (slug: {page_slug or 'unknown'})")
        
        # Get previous version for diff calculation
        prev_version = PageVersion.query.filter_by(
            page_id=page_id
        ).order_by(PageVersion.version.desc()).first()
        
        # Calculate simple diff data (store as JSON)
        # Use page_content if provided, otherwise try to get from page object
        content_for_diff = page_content
        if content_for_diff is None:
            try:
                content_for_diff = page.content
            except (AttributeError, TypeError):
                # SQLite UUID conversion issue - use raw SQL
                try:
                    result = db.session.execute(
                        db.text("SELECT content FROM pages WHERE id = :page_id"),
                        {"page_id": str(page_id)}
                    ).first()
                    if result:
                        content_for_diff = result[0]
                except:
                    content_for_diff = ""
        
        diff_data = {}
        if prev_version:
            # Simple diff: store line-by-line comparison
            old_lines = prev_version.content.split('\n')
            new_lines = content_for_diff.split('\n')
            diff_data = {
                'old_line_count': len(old_lines),
                'new_line_count': len(new_lines),
                'lines_added': max(0, len(new_lines) - len(old_lines)),
                'lines_removed': max(0, len(old_lines) - len(new_lines))
            }
        
        # Get page attributes, using stored values if provided, otherwise try to access from page object
        # Only access page object if we're missing values
        if page_title is None or page_content is None or page_version is None:
            # Use raw SQL to avoid SQLite UUID conversion issues
            try:
                # For SQLite, we need to handle UUID conversion
                # Try querying by slug if we have it, otherwise by ID
                if page_slug:
                    result = db.session.execute(
                        db.text("SELECT title, content, version FROM pages WHERE slug = :slug"),
                        {"slug": page_slug}
                    ).first()
                else:
                    result = db.session.execute(
                        db.text("SELECT title, content, version FROM pages WHERE id = :page_id"),
                        {"page_id": str(page_id)}
                    ).first()
                
                if result:
                    if page_title is None:
                        page_title = result[0]
                    if page_content is None:
                        page_content = result[1]
                    if page_version is None:
                        page_version = result[2]
                else:
                    raise ValueError(f"Page not found in database (id: {page_id}, slug: {page_slug})")
            except Exception as e:
                # Last resort: try page object access (will likely fail with SQLite)
                try:
                    if page_title is None:
                        page_title = page.title
                    if page_content is None:
                        page_content = page.content
                    if page_version is None:
                        page_version = page.version
                except (AttributeError, TypeError):
                    raise ValueError(f"Could not access page attributes: {page_id} - {str(e)}")
        
        # Get the next version number by querying existing versions
        # This avoids issues with page.version being stale after commits
        latest_version = PageVersion.query.filter_by(
            page_id=page_id
        ).order_by(PageVersion.version.desc()).first()
        
        if latest_version:
            next_version = latest_version.version + 1
        else:
            # No versions exist yet, use page_version (should be 1 for new pages)
            next_version = page_version if page_version > 0 else 1
        
        # Create version with the next version number
        version = PageVersion(
            page_id=page_id,
            title=page_title,
            content=page_content,
            change_summary=change_summary,
            changed_by=user_id,
            version=next_version,
            diff_data=diff_data
        )
        
        db.session.add(version)
        
        # Increment page version using raw SQL to avoid SQLite UUID issues
        # Do this after adding the version record to avoid conflicts
        try:
            db.session.execute(
                db.text("UPDATE pages SET version = :next_version WHERE id = :page_id"),
                {"page_id": str(page_id), "next_version": next_version + 1}
            )
        except Exception:
            # Fallback to page object access (will likely fail with SQLite)
            try:
                page.version = next_version + 1
            except (AttributeError, TypeError):
                # If page object access fails, skip increment (version will be updated on next access)
                pass
        
        db.session.commit()

