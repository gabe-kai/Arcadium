"""Integration tests for Notification Service integration"""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from app import db
from app.models.page import Page
from app.services.notification_service_client import NotificationServiceClient
from app.services.size_monitoring_service import SizeMonitoringService


def test_oversized_page_notification_integration(app):
    """Test that oversized page notifications trigger Notification Service calls"""
    test_user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    with app.app_context():
        # Create oversized page
        page = Page(
            title="Oversized Test Page",
            slug="oversized-test",
            content="x" * 600000,  # Large content
            created_by=test_user_id,
            updated_by=test_user_id,
            status="published",
            section="Regression-Testing",
            file_path="oversized-test.md",
        )
        db.session.add(page)
        db.session.commit()

        # Calculate size
        from app.utils.size_calculator import calculate_content_size_kb

        page.content_size_kb = calculate_content_size_kb(page.content)
        db.session.commit()

        # Mock Notification Service
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch(
            "app.services.notification_service_client.requests.post",
            return_value=mock_response,
        ) as mock_post:
            # Create notifications
            due_date = datetime.now(timezone.utc) + timedelta(days=7)
            notifications = SizeMonitoringService.create_oversized_notifications(
                max_size_kb=500.0, resolution_due_date=due_date, user_ids=[test_user_id]
            )

            # Verify notification was created
            assert len(notifications) == 1

            # Verify Notification Service was called
            assert mock_post.called

            # Verify the notification payload
            call_args = mock_post.call_args
            payload = call_args[1]["json"]
            assert payload["recipient_ids"] == [str(test_user_id)]
            assert payload["type"] == "warning"
            assert "Page Size Limit Exceeded" in payload["subject"]
            assert "Oversized Test Page" in payload["content"]
            assert payload["action_url"] == "/wiki/pages/oversized-test"


def test_notification_service_client_integration():
    """Test Notification Service client integration"""
    client = NotificationServiceClient(base_url="http://localhost:8006")

    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch(
        "app.services.notification_service_client.requests.post",
        return_value=mock_response,
    ):
        result = client.send_oversized_page_notification(
            recipient_id="user-id",
            page_title="Test Page",
            page_slug="test-page",
            current_size_kb=600.0,
            max_size_kb=500.0,
        )

        assert result is True
