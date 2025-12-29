"""
Notification Service client for sending notifications.

This module provides integration with the Notification Service for:
- Sending oversized page notifications
- Internal messaging
"""

import logging
import os
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class NotificationServiceClient:
    """Client for interacting with Notification Service"""

    def __init__(
        self, base_url: Optional[str] = None, service_token: Optional[str] = None
    ):
        """
        Initialize Notification Service client.

        Args:
            base_url: Notification Service base URL (defaults to NOTIFICATION_SERVICE_URL env var)
            service_token: Service token for authentication (defaults to WIKI_SERVICE_TOKEN env var)
        """
        self.base_url = base_url or os.getenv(
            "NOTIFICATION_SERVICE_URL", "http://localhost:8006"
        ).rstrip("/")
        self.service_token = service_token or os.getenv("WIKI_SERVICE_TOKEN", "")
        self.timeout = 5.0  # 5 second timeout

    def send_notification(
        self,
        recipient_ids: List[str],
        subject: str,
        content: str,
        notification_type: str = "system",
        action_url: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> bool:
        """
        Send notification to users.

        Args:
            recipient_ids: List of user UUID strings
            subject: Notification subject
            content: Notification content
            notification_type: Type of notification ('system', 'user', 'warning', 'info')
            action_url: Optional URL to link to (e.g., page URL)
            metadata: Optional metadata dictionary

        Returns:
            True if notification sent successfully, False otherwise
        """
        url = f"{self.base_url}/api/notifications/send"
        headers = {"Content-Type": "application/json"}

        # Use service token if available, otherwise use Bearer token
        if self.service_token:
            headers["Authorization"] = f"Service-Token {self.service_token}"
        else:
            # Fallback: try to get token from request context
            try:
                from flask import request

                auth_header = request.headers.get("Authorization", "")
                if auth_header:
                    headers["Authorization"] = auth_header
            except RuntimeError:
                # Not in request context
                pass

        payload = {
            "recipient_ids": recipient_ids,
            "subject": subject,
            "content": content,
            "type": notification_type,
        }

        if action_url:
            payload["action_url"] = action_url

        if metadata:
            payload["metadata"] = metadata

        try:
            response = requests.post(
                url, json=payload, headers=headers, timeout=self.timeout
            )

            if response.status_code in (200, 201):
                logger.info(f"Notification sent to {len(recipient_ids)} recipient(s)")
                return True
            else:
                logger.warning(
                    f"Failed to send notification: {response.status_code} - {response.text}"
                )
                return False

        except requests.exceptions.Timeout:
            logger.error("Notification Service timeout")
            return False
        except requests.exceptions.ConnectionError:
            logger.error("Failed to connect to Notification Service")
            return False
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            return False

    def send_oversized_page_notification(
        self,
        recipient_id: str,
        page_title: str,
        page_slug: str,
        current_size_kb: float,
        max_size_kb: float,
        due_date: Optional[str] = None,
    ) -> bool:
        """
        Send oversized page notification to a user.

        Args:
            recipient_id: User UUID string
            page_title: Title of the oversized page
            page_slug: Slug of the page (for URL)
            current_size_kb: Current page size in KB
            max_size_kb: Maximum allowed size in KB
            due_date: ISO datetime string for resolution due date (optional)

        Returns:
            True if notification sent successfully, False otherwise
        """
        subject = "Page Size Limit Exceeded"
        content = (
            f"Your page '{page_title}' exceeds the maximum size limit.\n\n"
            f"Current size: {current_size_kb:.1f} KB\n"
            f"Maximum allowed: {max_size_kb:.1f} KB\n"
        )

        if due_date:
            content += f"Resolution due date: {due_date}\n"

        content += "\nPlease reduce the page size to meet the limit."

        action_url = f"/wiki/pages/{page_slug}"

        metadata = {
            "page_title": page_title,
            "page_slug": page_slug,
            "current_size_kb": current_size_kb,
            "max_size_kb": max_size_kb,
            "notification_type": "oversized_page",
        }

        if due_date:
            metadata["due_date"] = due_date

        return self.send_notification(
            recipient_ids=[recipient_id],
            subject=subject,
            content=content,
            notification_type="warning",
            action_url=action_url,
            metadata=metadata,
        )


# Singleton instance
_notification_client = None


def get_notification_client() -> NotificationServiceClient:
    """
    Get singleton Notification Service client instance.

    Returns:
        NotificationServiceClient instance
    """
    global _notification_client
    if _notification_client is None:
        _notification_client = NotificationServiceClient()
    return _notification_client
