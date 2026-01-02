"""Token blacklist model for revoked tokens"""

import uuid
from datetime import datetime, timezone

from app import db
from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID


class TokenBlacklist(db.Model):
    """Token blacklist for revoked JWT tokens"""

    __tablename__ = "token_blacklist"
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token_id = Column(String(255), nullable=False, index=True)  # JWT jti claim
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    def __repr__(self):
        return f"<TokenBlacklist {self.token_id}>"

    def is_expired(self):
        """Check if token is expired"""
        # Convert stored datetime to UTC-aware for comparison
        # (stored as naive but represents UTC time)
        expires_at_aware = self.expires_at
        if expires_at_aware.tzinfo is None:
            expires_at_aware = expires_at_aware.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) > expires_at_aware
