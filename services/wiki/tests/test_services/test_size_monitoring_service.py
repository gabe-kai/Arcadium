"""Tests for size monitoring service"""
import uuid
from datetime import datetime, timezone, timedelta
import pytest
from app import db
from app.models.page import Page
from app.models.wiki_config import WikiConfig
from app.models.oversized_page_notification import OversizedPageNotification
from app.services.size_monitoring_service import SizeMonitoringService


@pytest.fixture
def test_user_id():
    """Test user ID"""
    return uuid.UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def test_pages(app, test_user_id):
    """Create test pages with different sizes"""
    with app.app_context():
        pages = []
        
        # Small page
        page1 = Page(
            title="Small Page",
            slug="small-page",
            content="# Small",
            created_by=test_user_id,
            updated_by=test_user_id,
            content_size_kb=5.0,
            word_count=100,
            file_path="small-page.md"
        )
        db.session.add(page1)
        pages.append(page1)
        
        # Medium page
        page2 = Page(
            title="Medium Page",
            slug="medium-page",
            content="# Medium",
            created_by=test_user_id,
            updated_by=test_user_id,
            content_size_kb=50.0,
            word_count=500,
            file_path="medium-page.md"
        )
        db.session.add(page2)
        pages.append(page2)
        
        # Large page
        page3 = Page(
            title="Large Page",
            slug="large-page",
            content="# Large",
            created_by=test_user_id,
            updated_by=test_user_id,
            content_size_kb=600.0,
            word_count=5000,
            file_path="large-page.md"
        )
        db.session.add(page3)
        pages.append(page3)
        
        # Very large page
        page4 = Page(
            title="Very Large Page",
            slug="very-large-page",
            content="# Very Large",
            created_by=test_user_id,
            updated_by=test_user_id,
            content_size_kb=1200.0,
            word_count=12000,
            file_path="very-large-page.md"
        )
        db.session.add(page4)
        pages.append(page4)
        
        db.session.commit()
        
        # Return page IDs
        return [p.id for p in pages]


def test_get_max_page_size_kb_not_configured(app):
    """Test getting max page size when not configured"""
    with app.app_context():
        # Clear any existing config
        db.session.query(WikiConfig).filter_by(key="page_max_size_kb").delete()
        db.session.commit()
        
        max_size = SizeMonitoringService.get_max_page_size_kb()
        assert max_size is None


def test_get_max_page_size_kb_configured(app, test_user_id):
    """Test getting max page size when configured"""
    with app.app_context():
        # Set config
        config = WikiConfig(
            key="page_max_size_kb",
            value="500.0",
            updated_by=test_user_id
        )
        db.session.add(config)
        db.session.commit()
        
        max_size = SizeMonitoringService.get_max_page_size_kb()
        assert max_size == 500.0


def test_get_oversized_pages_no_limit(app, test_pages):
    """Test getting oversized pages when no limit is set"""
    with app.app_context():
        # Clear config
        db.session.query(WikiConfig).filter_by(key="page_max_size_kb").delete()
        db.session.commit()
        
        oversized = SizeMonitoringService.get_oversized_pages()
        assert len(oversized) == 0


def test_get_oversized_pages_with_limit(app, test_pages):
    """Test getting oversized pages with a limit"""
    with app.app_context():
        # Set limit to 100 KB
        oversized = SizeMonitoringService.get_oversized_pages(max_size_kb=100.0)
        
        # Should find pages with size > 100 KB
        # Pages: 5KB, 50KB, 600KB, 1200KB
        # Oversized: 600KB, 1200KB
        assert len(oversized) == 2
        sizes = [p.content_size_kb for p in oversized]
        assert 600.0 in sizes
        assert 1200.0 in sizes


def test_create_oversized_notifications(app, test_pages, test_user_id):
    """Test creating oversized page notifications"""
    with app.app_context():
        # Clear existing notifications
        db.session.query(OversizedPageNotification).delete()
        db.session.commit()
        
        due_date = datetime.now(timezone.utc) + timedelta(days=7)
        
        # Create notifications with limit of 100 KB
        notifications = SizeMonitoringService.create_oversized_notifications(
            max_size_kb=100.0,
            resolution_due_date=due_date
        )
        
        # Should create 2 notifications (for 600KB and 1200KB pages)
        assert len(notifications) == 2
        
        # Verify notification details
        for notif in notifications:
            assert notif.max_size_kb == 100.0
            # Compare dates (handle timezone differences - database may store naive datetime)
            notif_date = notif.resolution_due_date
            if notif_date.tzinfo is None:
                notif_date = notif_date.replace(tzinfo=timezone.utc)
            # Allow up to 1 day difference for timezone issues
            assert abs((notif_date - due_date).total_seconds()) < 86400
            assert notif.resolved is False
            assert notif.current_size_kb > 100.0


def test_create_oversized_notifications_updates_existing(app, test_pages, test_user_id):
    """Test that creating notifications updates existing ones"""
    with app.app_context():
        # Create initial notification
        page = db.session.query(Page).filter_by(slug="large-page").first()
        due_date1 = datetime.now(timezone.utc) + timedelta(days=7)
        
        notif1 = OversizedPageNotification(
            page_id=page.id,
            current_size_kb=600.0,
            max_size_kb=500.0,
            resolution_due_date=due_date1,
            notified_users=[],
            resolved=False
        )
        db.session.add(notif1)
        db.session.commit()
        
        # Update page size
        page.content_size_kb = 700.0
        db.session.commit()
        
        # Create notifications again with new limit
        due_date2 = datetime.now(timezone.utc) + timedelta(days=14)
        notifications = SizeMonitoringService.create_oversized_notifications(
            max_size_kb=500.0,
            resolution_due_date=due_date2
        )
        
        # Should update existing notification
        db.session.refresh(notif1)
        assert notif1.current_size_kb == 700.0
        assert notif1.max_size_kb == 500.0
        # Compare dates (handle timezone differences - database may store naive datetime)
        notif_date = notif1.resolution_due_date
        if notif_date.tzinfo is None:
            notif_date = notif_date.replace(tzinfo=timezone.utc)
        # Allow up to 1 day difference for timezone issues
        assert abs((notif_date - due_date2).total_seconds()) < 86400


def test_check_and_resolve_oversized_pages(app, test_pages, test_user_id):
    """Test auto-resolving oversized pages that are now under limit"""
    with app.app_context():
        # Set limit to 100 KB
        config = WikiConfig(
            key="page_max_size_kb",
            value="100.0",
            updated_by=test_user_id
        )
        db.session.add(config)
        db.session.commit()
        
        # Create notifications for oversized pages
        due_date = datetime.now(timezone.utc) + timedelta(days=7)
        notifications = SizeMonitoringService.create_oversized_notifications(
            max_size_kb=100.0,
            resolution_due_date=due_date
        )
        
        # Reduce size of one page to be under limit
        large_page = db.session.query(Page).filter_by(slug="large-page").first()
        large_page.content_size_kb = 50.0
        db.session.commit()
        
        # Check and resolve
        result = SizeMonitoringService.check_and_resolve_oversized_pages()
        
        # Should resolve 1 page (the one we reduced)
        assert result['resolved'] == 1
        assert result['still_oversized'] == 1
        
        # Verify notification was marked as resolved
        notif = db.session.query(OversizedPageNotification).filter_by(
            page_id=large_page.id
        ).first()
        assert notif.resolved is True
        assert notif.resolved_at is not None


def test_get_size_distribution(app, test_pages):
    """Test getting size distribution"""
    with app.app_context():
        distribution = SizeMonitoringService.get_size_distribution()
        
        assert 'by_size_kb' in distribution
        assert 'by_word_count' in distribution
        
        # Verify buckets exist
        assert '0-10' in distribution['by_size_kb']
        assert '10-50' in distribution['by_size_kb']
        assert '50-100' in distribution['by_size_kb']
        assert '100-500' in distribution['by_size_kb']
        assert '500-1000' in distribution['by_size_kb']
        assert '1000+' in distribution['by_size_kb']
        
        # Verify word count buckets exist
        assert '0-500' in distribution['by_word_count']
        assert '500-1000' in distribution['by_word_count']
        assert '1000-2500' in distribution['by_word_count']
        assert '2500-5000' in distribution['by_word_count']
        assert '5000-10000' in distribution['by_word_count']
        assert '10000+' in distribution['by_word_count']
        
        # Verify counts match number of pages
        total_size = sum(distribution['by_size_kb'].values())
        total_words = sum(distribution['by_word_count'].values())
        assert total_size == 4
        assert total_words == 4


def test_get_oversized_pages_with_notifications(app, test_pages, test_user_id):
    """Test getting oversized pages with notification details"""
    with app.app_context():
        # Create notifications
        due_date = datetime.now(timezone.utc) + timedelta(days=7)
        notifications = SizeMonitoringService.create_oversized_notifications(
            max_size_kb=100.0,
            resolution_due_date=due_date
        )
        
        # Get pages with notifications
        pages = SizeMonitoringService.get_oversized_pages_with_notifications()
        
        # Should return 2 pages
        assert len(pages) == 2
        
        # Verify structure
        for page_info in pages:
            assert 'id' in page_info
            assert 'title' in page_info
            assert 'current_size_kb' in page_info
            assert 'max_size_kb' in page_info
            assert 'word_count' in page_info
            assert 'due_date' in page_info
            assert 'status' in page_info
            assert page_info['status'] == 'pending'
            assert page_info['current_size_kb'] > page_info['max_size_kb']


def test_create_oversized_notifications_with_user_ids(app, test_pages, test_user_id):
    """Test creating notifications with specific user IDs"""
    with app.app_context():
        # Clear existing notifications
        db.session.query(OversizedPageNotification).delete()
        db.session.commit()
        
        due_date = datetime.now(timezone.utc) + timedelta(days=7)
        custom_user_id = uuid.UUID("00000000-0000-0000-0000-000000000002")
        
        notifications = SizeMonitoringService.create_oversized_notifications(
            max_size_kb=100.0,
            resolution_due_date=due_date,
            user_ids=[custom_user_id]
        )
        
        # Verify user IDs were set
        for notif in notifications:
            assert str(custom_user_id) in notif.notified_users
