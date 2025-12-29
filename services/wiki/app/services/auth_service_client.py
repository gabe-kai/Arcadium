"""
Auth Service client for JWT validation and user profile retrieval.

This module provides integration with the Auth Service for:
- JWT token validation
- User profile retrieval
- Role verification
"""

import logging
import os
from typing import Dict, Optional

import requests

logger = logging.getLogger(__name__)


class AuthServiceClient:
    """Client for interacting with Auth Service"""

    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize Auth Service client.

        Args:
            base_url: Auth Service base URL (defaults to AUTH_SERVICE_URL env var)
        """
        self.base_url = base_url or os.getenv(
            "AUTH_SERVICE_URL", "http://localhost:8000"
        ).rstrip("/")
        self.timeout = 5.0  # 5 second timeout

    def verify_token(self, token: str) -> Optional[Dict]:
        """
        Verify JWT token with Auth Service.

        Args:
            token: JWT token string

        Returns:
            Dict with user information if valid:
            {
                'user_id': str (UUID),
                'username': str,
                'role': str,
                'email': str (optional)
            }
            None if token is invalid or expired
        """
        url = f"{self.base_url}/api/auth/verify"
        headers = {"Content-Type": "application/json"}
        payload = {"token": token}

        try:
            logger.debug(f"Verifying token with Auth Service at {url}")
            response = requests.post(
                url, json=payload, headers=headers, timeout=self.timeout
            )

            logger.debug(
                f"Auth Service response: status={response.status_code}, url={url}"
            )

            if response.status_code == 200:
                data = response.json()
                logger.debug(f"Auth Service response data: {data}")
                if data.get("valid"):
                    # Normalize response format
                    user_data = data.get("user", {})
                    result = {
                        "user_id": user_data.get("id") or user_data.get("user_id"),
                        "username": user_data.get("username", ""),
                        "role": user_data.get("role", "viewer"),
                        "email": user_data.get("email", ""),
                    }
                    logger.debug(
                        f"Token verified successfully. User: {result.get('username')}, Role: {result.get('role')}"
                    )
                    return result
                else:
                    # Token is invalid
                    logger.warning(
                        f"Token verification returned valid=false. Response: {data}"
                    )
                    return None
            elif response.status_code == 401:
                # Token is invalid or expired
                logger.warning(
                    f"Token verification failed with 401. Response: {response.text}"
                )
                return None
            else:
                logger.warning(
                    f"Unexpected status code from Auth Service: {response.status_code}. "
                    f"URL: {url}, Response: {response.text}"
                )
                return None

        except requests.exceptions.Timeout:
            logger.error(
                f"Auth Service timeout during token verification. URL: {url}, Timeout: {self.timeout}s"
            )
            return None
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Failed to connect to Auth Service at {url}. Error: {str(e)}")
            logger.error(
                f"Please ensure the Auth Service is running at {self.base_url}"
            )
            return None
        except Exception as e:
            logger.error(f"Error verifying token: {str(e)}", exc_info=True)
            return None

    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """
        Get user profile by ID from Auth Service.

        Args:
            user_id: User UUID string

        Returns:
            Dict with user information:
            {
                'id': str (UUID),
                'username': str,
                'email': str,
                'role': str,
                'created_at': str (ISO datetime)
            }
            None if user not found or error
        """
        url = f"{self.base_url}/api/users/{user_id}"

        try:
            response = requests.get(url, timeout=self.timeout)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.debug(f"User not found: {user_id}")
                return None
            else:
                logger.warning(
                    f"Unexpected status code from Auth Service: {response.status_code}"
                )
                return None

        except requests.exceptions.Timeout:
            logger.error("Auth Service timeout during user profile retrieval")
            return None
        except requests.exceptions.ConnectionError:
            logger.error("Failed to connect to Auth Service")
            return None
        except Exception as e:
            logger.error(f"Error retrieving user profile: {str(e)}")
            return None

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """
        Get user profile by username from Auth Service.

        Args:
            username: Username string

        Returns:
            Dict with user information:
            {
                'id': str (UUID),
                'username': str,
                'email': str,
                'role': str,
                'created_at': str (ISO datetime)
            }
            None if user not found or error
        """
        url = f"{self.base_url}/api/users/username/{username}"

        try:
            response = requests.get(url, timeout=self.timeout)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.debug(f"User not found: {username}")
                return None
            else:
                logger.warning(
                    f"Unexpected status code from Auth Service: {response.status_code}"
                )
                return None

        except requests.exceptions.Timeout:
            logger.error("Auth Service timeout during user lookup")
            return None
        except requests.exceptions.ConnectionError:
            logger.error("Failed to connect to Auth Service")
            return None
        except Exception as e:
            logger.error(f"Error retrieving user by username: {str(e)}")
            return None


# Singleton instance
_auth_client = None


def get_auth_client() -> AuthServiceClient:
    """
    Get singleton Auth Service client instance.

    Returns:
        AuthServiceClient instance
    """
    global _auth_client
    if _auth_client is None:
        _auth_client = AuthServiceClient()
    return _auth_client
