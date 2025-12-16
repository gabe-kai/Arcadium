"""Additional edge case tests for Notification Service client to fill coverage gaps"""
from unittest.mock import patch, MagicMock
import pytest
import requests
from app.services.notification_service_client import NotificationServiceClient


def test_send_notification_400_bad_request():
    """Test notification sending with 400 bad request"""
    client = NotificationServiceClient(base_url='http://localhost:8006')
    
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "Invalid recipient_ids"
    
    with patch('app.services.notification_service_client.requests.post', return_value=mock_response):
        result = client.send_notification(
            recipient_ids=['invalid-id'],
            subject='Test',
            content='Content'
        )
        assert result is False


def test_send_notification_403_forbidden():
    """Test notification sending with 403 forbidden"""
    client = NotificationServiceClient(base_url='http://localhost:8006')
    
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.text = "Forbidden"
    
    with patch('app.services.notification_service_client.requests.post', return_value=mock_response):
        result = client.send_notification(
            recipient_ids=['user-id'],
            subject='Test',
            content='Content'
        )
        assert result is False


def test_send_notification_500_server_error():
    """Test notification sending with 500 server error"""
    client = NotificationServiceClient(base_url='http://localhost:8006')
    
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal server error"
    
    with patch('app.services.notification_service_client.requests.post', return_value=mock_response):
        result = client.send_notification(
            recipient_ids=['user-id'],
            subject='Test',
            content='Content'
        )
        assert result is False


def test_send_notification_json_decode_error():
    """Test notification sending with malformed JSON response"""
    client = NotificationServiceClient(base_url='http://localhost:8006')
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.side_effect = ValueError("Invalid JSON")
    
    with patch('app.services.notification_service_client.requests.post', return_value=mock_response):
        result = client.send_notification(
            recipient_ids=['user-id'],
            subject='Test',
            content='Content'
        )
        # Should still return True if status is 200, even if JSON decode fails
        # (we don't check the response body)
        assert result is True


def test_send_notification_multiple_recipients():
    """Test sending notification to multiple recipients"""
    client = NotificationServiceClient(
        base_url='http://localhost:8006',
        service_token='test-token'
    )
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'message_id': '123e4567-e89b-12d3-a456-426614174000',
        'sent_to': 3,
        'created_at': '2024-01-01T00:00:00Z'
    }
    
    with patch('app.services.notification_service_client.requests.post', return_value=mock_response) as mock_post:
        result = client.send_notification(
            recipient_ids=['user-1', 'user-2', 'user-3'],
            subject='Test Subject',
            content='Test Content',
            notification_type='system'
        )
        
        assert result is True
        # Verify all recipients were sent
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        assert len(payload['recipient_ids']) == 3


def test_send_notification_empty_recipients():
    """Test sending notification with empty recipient list"""
    client = NotificationServiceClient(base_url='http://localhost:8006')
    
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "No recipients"
    
    with patch('app.services.notification_service_client.requests.post', return_value=mock_response):
        result = client.send_notification(
            recipient_ids=[],
            subject='Test',
            content='Content'
        )
        assert result is False


def test_send_notification_with_service_token():
    """Test notification sending with service token authentication"""
    client = NotificationServiceClient(
        base_url='http://localhost:8006',
        service_token='test-service-token'
    )
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    
    with patch('app.services.notification_service_client.requests.post', return_value=mock_response) as mock_post:
        result = client.send_notification(
            recipient_ids=['user-id'],
            subject='Test',
            content='Content'
        )
        
        assert result is True
        # Verify service token was used
        call_args = mock_post.call_args
        headers = call_args[1]['headers']
        assert headers['Authorization'] == 'Service-Token test-service-token'


def test_send_notification_with_metadata():
    """Test sending notification with metadata"""
    client = NotificationServiceClient(base_url='http://localhost:8006')
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    
    metadata = {
        'page_id': '123e4567-e89b-12d3-a456-426614174000',
        'custom_field': 'custom_value'
    }
    
    with patch('app.services.notification_service_client.requests.post', return_value=mock_response) as mock_post:
        result = client.send_notification(
            recipient_ids=['user-id'],
            subject='Test',
            content='Content',
            metadata=metadata
        )
        
        assert result is True
        # Verify metadata was included
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        assert payload['metadata'] == metadata


def test_send_oversized_page_notification_multiple_pages():
    """Test sending oversized page notification with edge case values"""
    client = NotificationServiceClient(base_url='http://localhost:8006')
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    
    with patch('app.services.notification_service_client.requests.post', return_value=mock_response) as mock_post:
        # Test with very large sizes
        result = client.send_oversized_page_notification(
            recipient_id='user-id',
            page_title='Very Large Page',
            page_slug='very-large-page',
            current_size_kb=9999.99,
            max_size_kb=500.0,
            due_date='2024-12-31T23:59:59Z'
        )
        
        assert result is True
        # Verify content includes the large size (formatted)
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        assert '10000.0' in payload['content'] or '9999.99' in payload['content']  # May be rounded
        assert '500.0' in payload['content']
        assert 'Very Large Page' in payload['content']


def test_send_notification_generic_exception():
    """Test notification sending with unexpected exception"""
    client = NotificationServiceClient(base_url='http://localhost:8006')
    
    with patch('app.services.notification_service_client.requests.post', side_effect=Exception("Unexpected error")):
        result = client.send_notification(
            recipient_ids=['user-id'],
            subject='Test',
            content='Content'
        )
        assert result is False
