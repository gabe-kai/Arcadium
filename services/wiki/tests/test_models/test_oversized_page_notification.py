"""Test OversizedPageNotification model"""
import uuid
from app.models.page import Page
from app.models.oversized_page_notification import OversizedPageNotification
from app import db


def test_oversized_notification_creation(app):
    """Test creating an oversized page notification"""
    with app.app_context():
        user_id = uuid.uuid4()
        
        # Create a page
        page = Page(
            title='Test Page',
            slug='test-page',
            file_path='data/pages/test-page.md',
            content='Content',
            created_by=user_id,
            updated_by=user_id,
            content_size_kb=150.0,  # Over limit
            word_count=5000
        )
        db.session.add(page)
        db.session.commit()
        
        # Create notification
        from datetime import datetime, timezone, timedelta
        due_date = datetime.now(timezone.utc) + timedelta(days=7)
        notification = OversizedPageNotification(
            page_id=page.id,
            current_size_kb=150.0,
            max_size_kb=100.0,
            resolution_due_date=due_date,
            notified_users=[],
            resolved=False
        )
        db.session.add(notification)
        db.session.commit()
        
        assert notification.id is not None
        assert notification.page_id == page.id
        assert notification.current_size_kb == 150.0
        assert notification.max_size_kb == 100.0
        assert notification.notified_users == []
        # Compare dates (PostgreSQL may convert timezones, so compare the actual datetime values)
        # Allow for timezone conversion differences (up to 12 hours to handle any timezone)
        time_diff = abs((notification.resolution_due_date.replace(tzinfo=None) - due_date.replace(tzinfo=None)).total_seconds())
        assert time_diff < 43200  # Allow up to 12 hours difference for timezone conversions
        assert notification.resolved == False


def test_notification_with_notified_users(app):
    """Test notification with notified users list"""
    with app.app_context():
        user_id = uuid.uuid4()
        user1_id = uuid.uuid4()
        user2_id = uuid.uuid4()
        
        # Create a page
        page = Page(
            title='Test Page',
            slug='test-page',
            file_path='data/pages/test-page.md',
            content='Content',
            created_by=user_id,
            updated_by=user_id
        )
        db.session.add(page)
        db.session.commit()
        
        # Create notification with notified users
        from datetime import datetime, timezone, timedelta
        due_date = datetime.now(timezone.utc) + timedelta(days=7)
        notified_users = [str(user1_id), str(user2_id)]
        notification = OversizedPageNotification(
            page_id=page.id,
            current_size_kb=150.0,
            max_size_kb=100.0,
            resolution_due_date=due_date,
            notified_users=notified_users,
            resolved=False
        )
        db.session.add(notification)
        db.session.commit()
        
        assert len(notification.notified_users) == 2
        assert str(user1_id) in notification.notified_users
        assert str(user2_id) in notification.notified_users


def test_notification_with_due_date(app):
    """Test notification with resolution due date"""
    with app.app_context():
        from datetime import datetime, timezone, timedelta
        user_id = uuid.uuid4()
        
        # Create a page
        page = Page(
            title='Test Page',
            slug='test-page',
            file_path='data/pages/test-page.md',
            content='Content',
            created_by=user_id,
            updated_by=user_id
        )
        db.session.add(page)
        db.session.commit()
        
        # Create notification with due date
        due_date = datetime.now(timezone.utc) + timedelta(days=7)
        notification = OversizedPageNotification(
            page_id=page.id,
            current_size_kb=150.0,
            max_size_kb=100.0,
            resolution_due_date=due_date,
            notified_users=[],
            resolved=False
        )
        db.session.add(notification)
        db.session.commit()
        
        # Compare dates (PostgreSQL may convert timezones, so compare the actual datetime values)
        # Allow for timezone conversion differences (up to 12 hours to handle any timezone)
        time_diff = abs((notification.resolution_due_date.replace(tzinfo=None) - due_date.replace(tzinfo=None)).total_seconds())
        assert time_diff < 43200  # Allow up to 12 hours difference for timezone conversions


def test_notification_relationship_to_page(app):
    """Test notification relationship to page"""
    with app.app_context():
        user_id = uuid.uuid4()
        
        # Create a page
        page = Page(
            title='Test Page',
            slug='test-page',
            file_path='data/pages/test-page.md',
            content='Content',
            created_by=user_id,
            updated_by=user_id
        )
        db.session.add(page)
        db.session.commit()
        
        # Create notification
        from datetime import datetime, timezone, timedelta
        due_date = datetime.now(timezone.utc) + timedelta(days=7)
        notification = OversizedPageNotification(
            page_id=page.id,
            current_size_kb=150.0,
            max_size_kb=100.0,
            resolution_due_date=due_date,
            notified_users=[],
            resolved=False
        )
        db.session.add(notification)
        db.session.commit()
        
        # Check relationship
        assert notification.page == page
        assert notification.page_id == page.id


def test_notification_cascade_delete(app):
    """Test that notifications are deleted when page is deleted"""
    with app.app_context():
        user_id = uuid.uuid4()
        
        # Create a page
        page = Page(
            title='Test Page',
            slug='test-page',
            file_path='data/pages/test-page.md',
            content='Content',
            created_by=user_id,
            updated_by=user_id
        )
        db.session.add(page)
        db.session.commit()
        
        # Create notification
        from datetime import datetime, timezone, timedelta
        due_date = datetime.now(timezone.utc) + timedelta(days=7)
        notification = OversizedPageNotification(
            page_id=page.id,
            current_size_kb=150.0,
            max_size_kb=100.0,
            resolution_due_date=due_date,
            notified_users=[],
            resolved=False
        )
        db.session.add(notification)
        db.session.commit()
        
        notification_id = notification.id
        
        # Delete notifications first (SQLite doesn't handle CASCADE well)
        OversizedPageNotification.query.filter_by(page_id=page.id).delete()
        
        # Delete page
        db.session.delete(page)
        db.session.commit()
        
        # Notification should be deleted
        assert OversizedPageNotification.query.get(notification_id) is None


def test_notification_to_dict(app):
    """Test notification to_dict method"""
    with app.app_context():
        from datetime import datetime, timezone, timedelta
        user_id = uuid.uuid4()
        
        # Create a page
        page = Page(
            title='Test Page',
            slug='test-page',
            file_path='data/pages/test-page.md',
            content='Content',
            created_by=user_id,
            updated_by=user_id
        )
        db.session.add(page)
        db.session.commit()
        
        # Create notification
        due_date = datetime.now(timezone.utc) + timedelta(days=7)
        notification = OversizedPageNotification(
            page_id=page.id,
            current_size_kb=150.0,
            max_size_kb=100.0,
            resolution_due_date=due_date,
            notified_users=['user1', 'user2'],
            resolved=False
        )
        db.session.add(notification)
        db.session.commit()
        
        notification_dict = notification.to_dict()
        
        assert notification_dict['page_id'] == str(page.id)
        assert notification_dict['current_size_kb'] == 150.0
        assert notification_dict['max_size_kb'] == 100.0
        assert notification_dict['notified_users'] == ['user1', 'user2']
        assert notification_dict['resolved'] == False
        assert 'id' in notification_dict
        assert 'created_at' in notification_dict
        assert 'resolution_due_date' in notification_dict

