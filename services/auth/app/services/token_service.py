"""
Token service for JWT generation and verification.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

import jwt
from app import db
from app.models.token_blacklist import TokenBlacklist
from app.models.user import User
from flask import current_app


class TokenService:
    """Service for JWT token operations"""

    @staticmethod
    def generate_access_token(user: User) -> str:
        """
        Generate JWT access token for user.

        Args:
            user: User instance

        Returns:
            JWT access token string
        """
        now = datetime.now(timezone.utc)
        expires_in = current_app.config.get(
            "JWT_ACCESS_TOKEN_EXPIRATION", 3600
        )  # Default 1 hour
        expires_at = now + timedelta(seconds=expires_in)

        # Generate unique token ID
        token_id = str(uuid.uuid4())

        payload = {
            "user_id": str(user.id),
            "username": user.username,
            "role": user.role,
            "jti": token_id,  # JWT ID
            "iat": int(now.timestamp()),  # Issued at
            "exp": int(expires_at.timestamp()),  # Expiration
        }

        secret_key = current_app.config.get("JWT_SECRET_KEY")
        algorithm = current_app.config.get("JWT_ALGORITHM", "HS256")

        token = jwt.encode(payload, secret_key, algorithm=algorithm)
        return token

    @staticmethod
    def generate_refresh_token(user: User) -> str:
        """
        Generate refresh token for user.

        Args:
            user: User instance

        Returns:
            Refresh token string (UUID)
        """
        # Refresh tokens are stored in database, so we just generate a UUID
        return str(uuid.uuid4())

    @staticmethod
    def verify_token(token: str) -> Optional[Dict]:
        """
        Verify and decode JWT token.

        Args:
            token: JWT token string

        Returns:
            Decoded token payload if valid, None otherwise
        """
        try:
            secret_key = current_app.config.get("JWT_SECRET_KEY")
            algorithm = current_app.config.get("JWT_ALGORITHM", "HS256")

            payload = jwt.decode(token, secret_key, algorithms=[algorithm])

            # Check if token is blacklisted
            token_id = payload.get("jti")
            if token_id and TokenService.is_token_blacklisted(token_id):
                return None

            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    @staticmethod
    def is_token_blacklisted(token_id: str) -> bool:
        """
        Check if token is blacklisted.

        Args:
            token_id: JWT ID (jti claim)

        Returns:
            True if token is blacklisted, False otherwise
        """
        blacklisted = (
            db.session.query(TokenBlacklist).filter_by(token_id=token_id).first()
        )

        if not blacklisted:
            return False

        # Check if blacklist entry is expired (cleanup)
        if blacklisted.is_expired():
            # Remove expired blacklist entry
            db.session.delete(blacklisted)
            db.session.commit()
            return False

        return True

    @staticmethod
    def blacklist_token(token_id: str, user_id: str, expires_at: datetime):
        """
        Add token to blacklist.

        Args:
            token_id: JWT ID (jti claim)
            user_id: User UUID
            expires_at: Token expiration time
        """
        # Check if already blacklisted
        existing = db.session.query(TokenBlacklist).filter_by(token_id=token_id).first()

        if existing:
            return  # Already blacklisted

        # Convert timezone-aware datetime to naive UTC for storage
        # PostgreSQL DateTime columns don't store timezone, so we store as naive UTC
        expires_at_naive = expires_at
        if expires_at.tzinfo is not None:
            expires_at_naive = expires_at.replace(tzinfo=None)

        blacklist_entry = TokenBlacklist(
            token_id=token_id,
            user_id=user_id,
            expires_at=expires_at_naive,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )

        db.session.add(blacklist_entry)
        db.session.flush()  # Flush to ensure it's visible in this session
        db.session.commit()

    @staticmethod
    def generate_service_token(service_name: str, service_id: str) -> str:
        """
        Generate service token for service-to-service authentication.

        Args:
            service_name: Name of the service
            service_id: Unique service identifier

        Returns:
            JWT service token
        """
        now = datetime.now(timezone.utc)
        # Service tokens have longer expiration (30 days)
        expires_at = now + timedelta(days=30)

        payload = {
            "service_name": service_name,
            "service_id": service_id,
            "type": "service",
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
        }

        secret_key = current_app.config.get("JWT_SECRET_KEY")
        algorithm = current_app.config.get("JWT_ALGORITHM", "HS256")

        token = jwt.encode(payload, secret_key, algorithm=algorithm)
        return token
