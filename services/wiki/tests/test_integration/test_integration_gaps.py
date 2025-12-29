"""Additional integration tests to fill coverage gaps"""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from app import db
from app.middleware.auth import get_user_from_token
from app.models.page import Page
from app.services.size_monitoring_service import SizeMonitoringService


def test_auth_middleware_with_service_down():
    """Test that auth middleware handles Auth Service being down gracefully"""
    # Mock Auth Service connection error
    with patch(
        "app.services.auth_service_client.requests.post",
        side_effect=Exception("Service unavailable"),
    ):
        result = get_user_from_token("test-token")
        assert result is None


def test_notification_failure_doesnt_break_flow(app):
    """Test that notification failures don't break the oversized page notification flow"""
    test_user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    with app.app_context():
        # Create oversized page
        page = Page(
            title="Test Page",
            slug="test-page",
            content="x" * 600000,
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            file_path="test-page.md",
        )
        db.session.add(page)
        db.session.commit()

        from app.utils.size_calculator import calculate_content_size_kb

        page.content_size_kb = calculate_content_size_kb(page.content)
        db.session.commit()

        # Mock Notification Service to fail
        with patch(
            "app.services.notification_service_client.requests.post",
            side_effect=Exception("Service down"),
        ):
            # Should not raise exception, should continue
            due_date = datetime.now(timezone.utc) + timedelta(days=7)
            notifications = SizeMonitoringService.create_oversized_notifications(
                max_size_kb=500.0, resolution_due_date=due_date, user_ids=[test_user_id]
            )

            # Notification record should still be created even if sending fails
            assert len(notifications) == 1
            assert notifications[0].page_id == page.id


def test_multiple_oversized_pages_notifications(app):
    """Test that multiple oversized pages trigger multiple notifications"""
    test_user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    with app.app_context():
        # Create multiple oversized pages
        page1 = Page(
            title="Oversized Page 1",
            slug="oversized-1",
            content="x" * 600000,
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            file_path="oversized-1.md",
        )
        page2 = Page(
            title="Oversized Page 2",
            slug="oversized-2",
            content="x" * 700000,
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            file_path="oversized-2.md",
        )
        db.session.add(page1)
        db.session.add(page2)
        db.session.commit()

        from app.utils.size_calculator import calculate_content_size_kb

        page1.content_size_kb = calculate_content_size_kb(page1.content)
        page2.content_size_kb = calculate_content_size_kb(page2.content)
        db.session.commit()

        # Mock Notification Service
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch(
            "app.services.notification_service_client.requests.post",
            return_value=mock_response,
        ) as mock_post:
            due_date = datetime.now(timezone.utc) + timedelta(days=7)
            notifications = SizeMonitoringService.create_oversized_notifications(
                max_size_kb=500.0, resolution_due_date=due_date, user_ids=[test_user_id]
            )

            # Should create 2 notifications
            assert len(notifications) == 2

            # Should send 2 notifications (one per page)
            assert mock_post.call_count == 2


def test_notification_with_invalid_user_id(app):
    """Test that invalid user IDs in notified_users are handled gracefully"""
    test_user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    with app.app_context():
        # Create oversized page
        page = Page(
            title="Test Page",
            slug="test-page",
            content="x" * 600000,
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            file_path="test-page.md",
        )
        db.session.add(page)
        db.session.commit()

        from app.utils.size_calculator import calculate_content_size_kb

        page.content_size_kb = calculate_content_size_kb(page.content)
        db.session.commit()

        # Create notification with invalid user ID in notified_users
        from app.models.oversized_page_notification import OversizedPageNotification

        notification = OversizedPageNotification(
            page_id=page.id,
            current_size_kb=600.0,
            max_size_kb=500.0,
            resolution_due_date=datetime.now(timezone.utc) + timedelta(days=7),
            notified_users=[
                "invalid-uuid",
                str(test_user_id),
            ],  # Mix of invalid and valid
            resolved=False,
        )
        db.session.add(notification)
        db.session.commit()

        # Mock Notification Service
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch(
            "app.services.notification_service_client.requests.post",
            return_value=mock_response,
        ) as mock_post:
            # Re-trigger notification sending
            due_date = datetime.now(timezone.utc) + timedelta(days=7)
            SizeMonitoringService.create_oversized_notifications(
                max_size_kb=500.0, resolution_due_date=due_date, user_ids=[test_user_id]
            )

            # Should only send to valid user ID, skip invalid one
            # Should have at least one call (for valid user)
            assert mock_post.call_count >= 1
