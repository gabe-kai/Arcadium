"""Orphanage service for managing orphaned pages"""
import os
import uuid
from typing import List, Dict, Optional
from app import db
from app.models.page import Page
from app.services.page_service import PageService
from app.services.file_service import FileService


class OrphanageService:
    """Service for managing orphaned pages"""
    
    ORPHANAGE_SLUG = "orphanage"
    
    @staticmethod
    def get_or_create_orphanage(user_id: uuid.UUID) -> Page:
        """
        Get or create the orphanage system page.
        
        Args:
            user_id: ID of user (for creation if needed)
            
        Returns:
            Orphanage page
        """
        # Look for existing orphanage
        from app import db
        orphanage = db.session.query(Page).filter_by(
            slug=OrphanageService.ORPHANAGE_SLUG,
            is_system_page=True
        ).first()
        
        if orphanage:
            return orphanage
        
        # Create orphanage page
        # First create the page normally
        orphanage = PageService.create_page(
            title="Orphanage",
            content="# Orphanage\n\nThis page contains pages that have been orphaned after their parent was deleted.",
            user_id=user_id,
            slug=OrphanageService.ORPHANAGE_SLUG,
            status="published",
            is_public=True
        )
        
        # Mark as system page (page is already committed by create_page)
        orphanage.is_system_page = True
        db.session.commit()
        
        return orphanage
    
    @staticmethod
    def orphan_pages(page_ids: List[uuid.UUID], deleted_parent_id: uuid.UUID) -> List[Page]:
        """
        Mark pages as orphaned and assign them to the orphanage.
        
        Args:
            page_ids: List of page IDs to orphan
            deleted_parent_id: ID of the deleted parent page
            
        Returns:
            List of orphaned Page instances
        """
        orphanage = OrphanageService.get_or_create_orphanage(
            # Use a system user ID - in production, this would come from config
            uuid.UUID('00000000-0000-0000-0000-000000000001')
        )
        
        orphaned_pages = []
        
        for page_id in page_ids:
            from app import db
            page = db.session.get(Page, page_id)
            if not page:
                continue
            
            # Mark as orphaned
            page.is_orphaned = True
            page.orphaned_from = deleted_parent_id
            page.parent_id = orphanage.id
            
            # Recalculate file path (now under orphanage)
            # Pass orphanage as parent to avoid SQLite UUID lookup issues
            old_file_path = page.file_path
            page.file_path = FileService.calculate_file_path(page, parent=orphanage)
            
            # Move file if path changed
            if old_file_path != page.file_path:
                FileService.move_page_file(page, old_file_path, page.file_path)
            
            orphaned_pages.append(page)
        
        db.session.commit()
        
        return orphaned_pages
    
    @staticmethod
    def get_orphaned_pages(grouped: bool = False) -> List[Page]:
        """
        Get all orphaned pages.
        
        Args:
            grouped: If True, return pages grouped by original parent
            
        Returns:
            List of orphaned Page instances (or dict if grouped=True)
        """
        from app import db
        orphaned = db.session.query(Page).filter_by(is_orphaned=True).order_by(
            Page.orphaned_from,
            Page.title
        ).all()
        
        if not grouped:
            return orphaned
        
        # Group by original parent
        grouped_pages = {}
        for page in orphaned:
            # Convert UUID to string safely
            try:
                parent_id = str(page.orphaned_from) if page.orphaned_from else 'unknown'
            except Exception:
                parent_id = 'unknown'
            if parent_id not in grouped_pages:
                grouped_pages[parent_id] = []
            grouped_pages[parent_id].append(page)
        
        return grouped_pages
    
    @staticmethod
    def reassign_page(page_id: uuid.UUID, new_parent_id: Optional[uuid.UUID], user_id: uuid.UUID) -> Page:
        """
        Reassign an orphaned page to a new parent.
        
        Args:
            page_id: ID of orphaned page to reassign
            new_parent_id: ID of new parent (None for root)
            user_id: ID of user making the reassignment
            
        Returns:
            Updated Page instance
            
        Raises:
            ValueError: If page not found or not orphaned
        """
        from app import db
        page = db.session.get(Page, page_id)
        if not page:
            raise ValueError(f"Page not found: {page_id}")
        
        if not page.is_orphaned:
            raise ValueError(f"Page is not orphaned: {page_id}")
        
        # Validate new parent if provided
        if new_parent_id:
            new_parent = Page.query.get(new_parent_id)
            if not new_parent:
                raise ValueError(f"New parent not found: {new_parent_id}")
            
            # Check for cycles
            current = new_parent
            while current:
                if current.id == page_id:
                    raise ValueError("Cannot reassign: would create circular reference")
                current = current.parent
        
        # Update page
        old_file_path = page.file_path
        page.parent_id = new_parent_id
        page.is_orphaned = False
        page.orphaned_from = None
        page.updated_by = user_id
        
        # Recalculate file path
        # Get new parent if provided to avoid SQLite UUID lookup issues
        new_parent_obj = None
        if new_parent_id:
            try:
                new_parent_obj = db.session.get(Page, new_parent_id)
            except Exception:
                pass
        page.file_path = FileService.calculate_file_path(page, parent=new_parent_obj)
        
        # Move file if path changed
        if old_file_path != page.file_path:
            FileService.move_page_file(page, old_file_path, page.file_path)
        
        # Update file content (recalculate path in file)
        from app.utils.markdown_service import parse_frontmatter
        from app.services.page_service import PageService
        frontmatter, markdown_content = parse_frontmatter(page.content)
        
        # Update frontmatter with new parent (skip parent_slug to avoid SQLite UUID issues)
        if 'parent_slug' in frontmatter and not new_parent_id:
            del frontmatter['parent_slug']
        
        # Build file content using the helper method
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
        
        return page
    
    @staticmethod
    def bulk_reassign_pages(
        page_ids: List[uuid.UUID],
        new_parent_id: Optional[uuid.UUID],
        user_id: uuid.UUID
    ) -> List[Page]:
        """
        Reassign multiple orphaned pages to a new parent.
        
        Args:
            page_ids: List of orphaned page IDs to reassign
            new_parent_id: ID of new parent (None for root)
            user_id: ID of user making the reassignment
            
        Returns:
            List of updated Page instances
        """
        reassigned = []
        
        for page_id in page_ids:
            try:
                page = OrphanageService.reassign_page(page_id, new_parent_id, user_id)
                reassigned.append(page)
            except ValueError as e:
                # Log error but continue with other pages
                print(f"Error reassigning page {page_id}: {e}")
                continue
        
        return reassigned
    
    @staticmethod
    def clear_orphanage(user_id: uuid.UUID) -> Dict:
        """
        Clear the orphanage by reassigning all orphaned pages to root.
        
        Args:
            user_id: ID of user clearing the orphanage
            
        Returns:
            Dict with count of reassigned pages
        """
        orphaned = OrphanageService.get_orphaned_pages()
        
        reassigned = []
        for page in orphaned:
            try:
                reassigned_page = OrphanageService.reassign_page(page.id, None, user_id)
                reassigned.append(reassigned_page)
            except ValueError as e:
                print(f"Error reassigning page {page.id}: {e}")
                continue
        
        return {
            'reassigned_count': len(reassigned),
            'pages': [{'id': str(p.id), 'title': p.title, 'slug': p.slug} for p in reassigned]
        }
    
    @staticmethod
    def get_orphanage_stats() -> Dict:
        """
        Get statistics about the orphanage.
        
        Returns:
            Dict with orphanage statistics
        """
        from app import db
        orphaned = db.session.query(Page).filter_by(is_orphaned=True).all()
        
        # Group by original parent
        by_parent = {}
        for page in orphaned:
            # Convert UUID to string safely
            try:
                parent_id = str(page.orphaned_from) if page.orphaned_from else 'unknown'
            except Exception:
                parent_id = 'unknown'
            if parent_id not in by_parent:
                by_parent[parent_id] = []
            by_parent[parent_id].append(page)
        
        return {
            'total_orphaned': len(orphaned),
            'groups': len(by_parent),
            'by_parent': {
                parent_id: len(pages)
                for parent_id, pages in by_parent.items()
            }
        }

