"""Version service for wiki page history"""
import uuid
import difflib
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timezone
from app import db
from app.models.page import Page
from app.models.page_version import PageVersion
from app.services.page_service import PageService


class VersionService:
    """Service for managing page version history"""
    
    @staticmethod
    def create_version(
        page_id: uuid.UUID,
        user_id: uuid.UUID,
        change_summary: str = None
    ) -> PageVersion:
        """
        Create a new version snapshot of a page.
        
        Args:
            page_id: ID of the page
            user_id: ID of the user making the change
            change_summary: Optional summary of changes
            
        Returns:
            Created PageVersion instance
        """
        page = Page.query.get(page_id)
        if not page:
            raise ValueError(f"Page not found: {page_id}")
        
        # Get the next version number
        # Use page.version which is already incremented by PageService
        # If no versions exist yet, start at 1
        latest_version = PageVersion.query.filter_by(
            page_id=page_id
        ).order_by(PageVersion.version.desc()).first()
        
        if latest_version:
            next_version = latest_version.version + 1
        else:
            # No versions exist, check page.version
            # If page.version is 1, that means PageService hasn't created version 1 yet
            # So we should create version 1
            next_version = max(1, page.version)
        
        # Calculate diff if previous version exists
        diff_data = None
        if latest_version:
            diff_data = VersionService._calculate_diff(
                latest_version.content,
                page.content
            )
        
        # Create version
        version = PageVersion(
            page_id=page_id,
            version=next_version,
            title=page.title,
            content=page.content,
            changed_by=user_id,
            change_summary=change_summary,
            diff_data=diff_data
        )
        
        db.session.add(version)
        db.session.commit()
        
        return version
    
    @staticmethod
    def _calculate_diff(old_content: str, new_content: str) -> Dict:
        """
        Calculate diff between two content versions.
        
        Args:
            old_content: Previous version content
            new_content: New version content
            
        Returns:
            Dictionary with diff information
        """
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)
        
        # Calculate line-based diff
        diff = list(difflib.unified_diff(
            old_lines,
            new_lines,
            lineterm='',
            n=3  # Context lines
        ))
        
        # Count changes
        added_lines = sum(1 for line in diff if line.startswith('+') and not line.startswith('+++'))
        removed_lines = sum(1 for line in diff if line.startswith('-') and not line.startswith('---'))
        
        # Calculate character-level changes
        old_char_count = len(old_content)
        new_char_count = len(new_content)
        char_diff = new_char_count - old_char_count
        
        return {
            'diff': diff,
            'added_lines': added_lines,
            'removed_lines': removed_lines,
            'old_line_count': len(old_lines),
            'new_line_count': len(new_lines),
            'old_char_count': old_char_count,
            'new_char_count': new_char_count,
            'char_diff': char_diff
        }
    
    @staticmethod
    def get_version(page_id: uuid.UUID, version: int) -> Optional[PageVersion]:
        """
        Get a specific version of a page.
        
        Args:
            page_id: ID of the page
            version: Version number
            
        Returns:
            PageVersion instance or None if not found
        """
        return PageVersion.query.filter_by(
            page_id=page_id,
            version=version
        ).first()
    
    @staticmethod
    def get_all_versions(page_id: uuid.UUID) -> List[PageVersion]:
        """
        Get all versions of a page, ordered by version number (newest first).
        
        Args:
            page_id: ID of the page
            
        Returns:
            List of PageVersion instances
        """
        return PageVersion.query.filter_by(
            page_id=page_id
        ).order_by(PageVersion.version.desc()).all()
    
    @staticmethod
    def get_latest_version(page_id: uuid.UUID) -> Optional[PageVersion]:
        """
        Get the latest version of a page.
        
        Args:
            page_id: ID of the page
            
        Returns:
            Latest PageVersion instance or None if no versions exist
        """
        return PageVersion.query.filter_by(
            page_id=page_id
        ).order_by(PageVersion.version.desc()).first()
    
    @staticmethod
    def compare_versions(
        page_id: uuid.UUID,
        version1: int,
        version2: int
    ) -> Dict:
        """
        Compare two versions of a page.
        
        Args:
            page_id: ID of the page
            version1: First version number
            version2: Second version number
            
        Returns:
            Dictionary with comparison data
        """
        v1 = VersionService.get_version(page_id, version1)
        v2 = VersionService.get_version(page_id, version2)
        
        if not v1 or not v2:
            raise ValueError("One or both versions not found")
        
        # Calculate diff
        diff_data = VersionService._calculate_diff(v1.content, v2.content)
        
        return {
            'version1': v1.to_dict(),
            'version2': v2.to_dict(),
            'diff': diff_data
        }
    
    @staticmethod
    def rollback_to_version(
        page_id: uuid.UUID,
        version: int,
        user_id: uuid.UUID,
        user_role: str = 'viewer'
    ) -> Page:
        """
        Rollback a page to a specific version.
        Creates a new version with the rolled-back content.
        
        Args:
            page_id: ID of the page
            version: Version number to rollback to
            user_id: ID of the user performing rollback
            user_role: Role of the user (for permission check)
            
        Returns:
            Updated Page instance
            
        Raises:
            ValueError: If version not found or user lacks permission
        """
        page = Page.query.get(page_id)
        if not page:
            raise ValueError(f"Page not found: {page_id}")
        
        # Check permissions
        # Writers can only rollback their own pages, Admins can rollback any
        if user_role not in ['admin', 'writer']:
            raise PermissionError("Only Writers and Admins can rollback pages")
        
        if user_role == 'writer' and page.created_by != user_id:
            raise PermissionError("Writers can only rollback pages they created")
        
        # Get the version to rollback to
        target_version = VersionService.get_version(page_id, version)
        if not target_version:
            raise ValueError(f"Version {version} not found")
        
        # Save current state as a version before rollback
        VersionService.create_version(
            page_id=page_id,
            user_id=user_id,
            change_summary=f"Pre-rollback snapshot before rolling back to version {version}"
        )
        
        # Restore content from target version
        page.title = target_version.title
        page.content = target_version.content
        page.updated_by = user_id
        
        db.session.commit()
        
        # Create a new version with the rolled-back content
        VersionService.create_version(
            page_id=page_id,
            user_id=user_id,
            change_summary=f"Rolled back to version {version}"
        )
        
        return page
    
    @staticmethod
    def get_version_history_summary(page_id: uuid.UUID) -> List[Dict]:
        """
        Get a summary of version history for a page.
        
        Args:
            page_id: ID of the page
            
        Returns:
            List of version summary dictionaries
        """
        versions = VersionService.get_all_versions(page_id)
        
        summaries = []
        for version in versions:
            summaries.append({
                'version': version.version,
                'title': version.title,
                'changed_by': str(version.changed_by),
                'change_summary': version.change_summary,
                'created_at': version.created_at.isoformat() if version.created_at else None,
                'diff_stats': version.diff_data.get('added_lines', 0) + version.diff_data.get('removed_lines', 0) if version.diff_data else 0
            })
        
        return summaries
    
    @staticmethod
    def get_version_diff(
        page_id: uuid.UUID,
        version1: int,
        version2: int
    ) -> Dict:
        """
        Get diff between two versions.
        
        Args:
            page_id: ID of the page
            version1: First version number
            version2: Second version number
            
        Returns:
            Dictionary with diff data
        """
        v1 = VersionService.get_version(page_id, version1)
        v2 = VersionService.get_version(page_id, version2)
        
        if not v1 or not v2:
            raise ValueError("One or both versions not found")
        
        return VersionService._calculate_diff(v1.content, v2.content)
    
    @staticmethod
    def get_version_count(page_id: uuid.UUID) -> int:
        """
        Get the total number of versions for a page.
        
        Args:
            page_id: ID of the page
            
        Returns:
            Number of versions
        """
        return PageVersion.query.filter_by(page_id=page_id).count()
    
    @staticmethod
    def delete_version(page_id: uuid.UUID, version: int) -> bool:
        """
        Delete a specific version.
        Note: According to requirements, all versions should be kept indefinitely.
        This method is provided for admin use only if needed.
        
        Args:
            page_id: ID of the page
            version: Version number to delete
            
        Returns:
            True if deleted, False if not found
        """
        version_obj = VersionService.get_version(page_id, version)
        if version_obj:
            db.session.delete(version_obj)
            db.session.commit()
            return True
        return False

