"""Refresh token model for token refresh functionality"""

import uuid
from datetime import datetime, timezone

from app import db
from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class RefreshToken(db.Model):
    """Refresh token for access token renewal"""

    __tablename__ = "refresh_tokens"
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash = Column(
        String(255), nullable=False, unique=True, index=True
    )  # Hashed refresh token
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    last_used_at = Column(DateTime, nullable=True)

    # Relationship - passive_deletes=True lets database handle CASCADE
    user = relationship("User", backref="refresh_tokens", passive_deletes=True)

    def __repr__(self):
        return f"<RefreshToken {self.user_id}>"

    def is_expired(self):
        """Check if refresh token is expired"""
        # Convert stored datetime to UTC-aware for comparison
        # (stored as naive but represents UTC time)
        expires_at_aware = self.expires_at
        if expires_at_aware.tzinfo is None:
            expires_at_aware = expires_at_aware.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) > expires_at_aware
