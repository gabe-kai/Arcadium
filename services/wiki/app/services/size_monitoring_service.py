"""
Size monitoring service for tracking page sizes and detecting oversized pages.

This service:
- Detects pages exceeding size limits
- Creates oversized page notifications
- Tracks resolution status
- Integrates with notification service
"""
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict
from sqlalchemy import func
from app import db
from app.models.page import Page
from app.models.wiki_config import WikiConfig
from app.models.oversized_page_notification import OversizedPageNotification
from app.services.notification_service_client import get_notification_client


class SizeMonitoringService:
    """Service for monitoring page sizes and managing oversized pages"""
    
    @staticmethod
    def get_max_page_size_kb() -> Optional[float]:
        """
        Get the configured maximum page size in KB.
        
        Returns:
            Maximum size in KB, or None if not configured
        """
        config = db.session.query(WikiConfig).filter_by(
            key="page_max_size_kb"
        ).first()
        
        if config:
            try:
                return float(config.value)
            except (ValueError, TypeError):
                return None
        
        return None
    
    @staticmethod
    def get_oversized_pages(max_size_kb: Optional[float] = None) -> List[Page]:
        """
        Get all pages that exceed the size limit.
        
        Args:
            max_size_kb: Maximum size in KB (if None, uses configured limit)
            
        Returns:
            List of Page objects exceeding the limit
        """
        if max_size_kb is None:
            max_size_kb = SizeMonitoringService.get_max_page_size_kb()
        
        if max_size_kb is None:
            return []
        
        return db.session.query(Page).filter(
            Page.content_size_kb > max_size_kb
        ).all()
    
    @staticmethod
    def create_oversized_notifications(
        max_size_kb: float,
        resolution_due_date: datetime,
        user_ids: Optional[List[uuid.UUID]] = None
    ) -> List[OversizedPageNotification]:
        """
        Create oversized page notifications for all pages exceeding the limit.
        
        Args:
            max_size_kb: Maximum size in KB
            resolution_due_date: Due date for resolution
            user_ids: List of user IDs to notify (if None, uses page authors)
            
        Returns:
            List of created OversizedPageNotification objects
        """
        oversized_pages = SizeMonitoringService.get_oversized_pages(max_size_kb)
        
        notifications = []
        for page in oversized_pages:
            # Check if notification already exists for this page
            existing = db.session.query(OversizedPageNotification).filter_by(
                page_id=page.id,
                resolved=False
            ).first()
            
            if existing:
                # Update existing notification
                existing.current_size_kb = page.content_size_kb
                existing.max_size_kb = max_size_kb
                existing.resolution_due_date = resolution_due_date
                if user_ids:
                    existing.notified_users = [str(uid) for uid in user_ids]
                notifications.append(existing)
            else:
                # Create new notification
                notified_users = user_ids or []
                if page.created_by:
                    # Add page author if not already in list
                    if page.created_by not in notified_users:
                        notified_users.append(page.created_by)
                
                notification = OversizedPageNotification(
                    page_id=page.id,
                    current_size_kb=page.content_size_kb,
                    max_size_kb=max_size_kb,
                    resolution_due_date=resolution_due_date,
                    notified_users=[str(uid) for uid in notified_users],
                    resolved=False
                )
                db.session.add(notification)
                notifications.append(notification)
        
        db.session.commit()
        
        # Send notifications via Notification Service
        notification_client = get_notification_client()
        due_date_str = resolution_due_date.isoformat() if resolution_due_date else None
        
        for notification in notifications:
            page = db.session.query(Page).filter_by(id=notification.page_id).first()
            if page:
                # Send notification to each user in notified_users
                for user_id_str in notification.notified_users:
                    try:
                        user_id = uuid.UUID(user_id_str)
                        notification_client.send_oversized_page_notification(
                            recipient_id=user_id_str,
                            page_title=page.title,
                            page_slug=page.slug,
                            current_size_kb=notification.current_size_kb,
                            max_size_kb=notification.max_size_kb,
                            due_date=due_date_str
                        )
                    except (ValueError, TypeError) as e:
                        # Invalid UUID, skip this user
                        continue
        
        return notifications
    
    @staticmethod
    def check_and_resolve_oversized_pages() -> Dict[str, int]:
        """
        Check all oversized page notifications and auto-resolve those that
        are now under the limit.
        
        Returns:
            Dictionary with counts: {'resolved': int, 'still_oversized': int}
        """
        max_size_kb = SizeMonitoringService.get_max_page_size_kb()
        if max_size_kb is None:
            return {'resolved': 0, 'still_oversized': 0}
        
        # Get all unresolved notifications
        unresolved = db.session.query(OversizedPageNotification).filter_by(
            resolved=False
        ).all()
        
        resolved_count = 0
        still_oversized_count = 0
        
        for notification in unresolved:
            # Check if page is now under limit
            page = db.session.query(Page).filter_by(id=notification.page_id).first()
            if page and page.content_size_kb <= max_size_kb:
                # Auto-resolve
                notification.resolved = True
                notification.resolved_at = datetime.now(timezone.utc)
                resolved_count += 1
            else:
                # Update current size if page still exists
                if page:
                    notification.current_size_kb = page.content_size_kb
                still_oversized_count += 1
        
        db.session.commit()
        
        return {
            'resolved': resolved_count,
            'still_oversized': still_oversized_count
        }
    
    @staticmethod
    def get_size_distribution() -> Dict[str, Dict[str, int]]:
        """
        Get page size and word count distribution buckets.
        
        Returns:
            Dictionary with 'by_size_kb' and 'by_word_count' distributions
        """
        # Define buckets
        size_buckets = {
            "0-10": (0, 10),
            "10-50": (10, 50),
            "50-100": (50, 100),
            "100-500": (100, 500),
            "500-1000": (500, 1000),
            "1000+": (1000, None),
        }
        
        word_buckets = {
            "0-500": (0, 500),
            "500-1000": (500, 1000),
            "1000-2500": (1000, 2500),
            "2500-5000": (2500, 5000),
            "5000-10000": (5000, 10000),
            "10000+": (10000, None),
        }
        
        by_size_kb = {}
        for label, (start, end) in size_buckets.items():
            query = db.session.query(func.count(Page.id))
            if end is None:
                query = query.filter(Page.content_size_kb >= start)
            else:
                query = query.filter(
                    Page.content_size_kb >= start,
                    Page.content_size_kb < end
                )
            by_size_kb[label] = int(query.scalar() or 0)
        
        by_word_count = {}
        for label, (start, end) in word_buckets.items():
            query = db.session.query(func.count(Page.id))
            if end is None:
                query = query.filter(Page.word_count >= start)
            else:
                query = query.filter(
                    Page.word_count >= start,
                    Page.word_count < end
                )
            by_word_count[label] = int(query.scalar() or 0)
        
        return {
            'by_size_kb': by_size_kb,
            'by_word_count': by_word_count
        }
    
    @staticmethod
    def get_oversized_pages_with_notifications() -> List[Dict]:
        """
        Get all oversized pages with their notification details.
        
        Returns:
            List of dictionaries with page and notification information
        """
        results = (
            db.session.query(OversizedPageNotification, Page)
            .join(Page, OversizedPageNotification.page_id == Page.id)
            .filter(OversizedPageNotification.resolved.is_(False))
            .all()
        )
        
        pages = []
        for notif, page in results:
            pages.append({
                'id': str(page.id),
                'title': page.title,
                'slug': page.slug,
                'current_size_kb': notif.current_size_kb,
                'max_size_kb': notif.max_size_kb,
                'word_count': page.word_count,
                'due_date': notif.resolution_due_date.isoformat() if notif.resolution_due_date else None,
                'status': 'resolved' if notif.resolved else 'pending',
                'created_at': notif.created_at.isoformat() if notif.created_at else None,
                'notification_id': str(notif.id)
            })
        
        return pages
