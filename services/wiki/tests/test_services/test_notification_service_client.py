"""Tests for Notification Service client"""

from unittest.mock import MagicMock, patch

import requests
from app.services.notification_service_client import (
    NotificationServiceClient,
    get_notification_client,
)


def test_send_notification_success():
    """Test successful notification sending"""
    client = NotificationServiceClient(
        base_url="http://localhost:8006", service_token="test-token"
    )

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "message_id": "123e4567-e89b-12d3-a456-426614174000",
        "sent_to": 1,
        "created_at": "2024-01-01T00:00:00Z",
    }

    with patch(
        "app.services.notification_service_client.requests.post",
        return_value=mock_response,
    ):
        result = client.send_notification(
            recipient_ids=["user-id"],
            subject="Test Subject",
            content="Test Content",
            notification_type="system",
        )

        assert result is True


def test_send_notification_with_action_url():
    """Test sending notification with action URL"""
    client = NotificationServiceClient(base_url="http://localhost:8006")

    mock_response = MagicMock()
    mock_response.status_code = 201

    with patch(
        "app.services.notification_service_client.requests.post",
        return_value=mock_response,
    ):
        result = client.send_notification(
            recipient_ids=["user-id"],
            subject="Test",
            content="Content",
            action_url="/wiki/pages/test",
        )

        assert result is True


def test_send_notification_timeout():
    """Test notification sending with timeout"""
    client = NotificationServiceClient(base_url="http://localhost:8006")

    with patch(
        "app.services.notification_service_client.requests.post",
        side_effect=requests.exceptions.Timeout(),
    ):
        result = client.send_notification(
            recipient_ids=["user-id"], subject="Test", content="Content"
        )

        assert result is False


def test_send_notification_connection_error():
    """Test notification sending with connection error"""
    client = NotificationServiceClient(base_url="http://localhost:8006")

    with patch(
        "app.services.notification_service_client.requests.post",
        side_effect=requests.exceptions.ConnectionError(),
    ):
        result = client.send_notification(
            recipient_ids=["user-id"], subject="Test", content="Content"
        )

        assert result is False


def test_send_oversized_page_notification():
    """Test sending oversized page notification"""
    client = NotificationServiceClient(base_url="http://localhost:8006")

    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch(
        "app.services.notification_service_client.requests.post",
        return_value=mock_response,
    ) as mock_post:
        result = client.send_oversized_page_notification(
            recipient_id="user-id",
            page_title="Test Page",
            page_slug="test-page",
            current_size_kb=600.0,
            max_size_kb=500.0,
            due_date="2024-02-01T00:00:00Z",
        )

        assert result is True
        # Verify the payload
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        assert payload["recipient_ids"] == ["user-id"]
        assert payload["type"] == "warning"
        assert "Page Size Limit Exceeded" in payload["subject"]
        assert "Test Page" in payload["content"]
        assert payload["action_url"] == "/wiki/pages/test-page"
        assert payload["metadata"]["notification_type"] == "oversized_page"


def test_send_oversized_page_notification_without_due_date():
    """Test sending oversized page notification without due date"""
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


def test_get_notification_client_singleton():
    """Test that get_notification_client returns singleton"""
    client1 = get_notification_client()
    client2 = get_notification_client()

    assert client1 is client2
    assert isinstance(client1, NotificationServiceClient)
