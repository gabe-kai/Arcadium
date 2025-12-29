"""OversizedPageNotification model for tracking oversized pages"""

import uuid
from datetime import datetime, timezone

from app import db
from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class OversizedPageNotification(db.Model):
    """Notification for pages exceeding size limits"""

    __tablename__ = "oversized_page_notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    page_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    current_size_kb = Column(Float, nullable=False)
    max_size_kb = Column(Float, nullable=False)
    resolution_due_date = Column(DateTime, nullable=False, index=True)
    notified_users = Column(
        JSON, nullable=False
    )  # Array of user IDs (stored as JSON for SQLite compatibility)
    resolved = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    page = relationship("Page", backref="oversized_notifications")

    def __repr__(self):
        return f"<OversizedPageNotification {self.page_id}>"

    def to_dict(self):
        """Convert notification to dictionary"""
        return {
            "id": str(self.id),
            "page_id": str(self.page_id),
            "current_size_kb": self.current_size_kb,
            "max_size_kb": self.max_size_kb,
            "resolution_due_date": (
                self.resolution_due_date.isoformat()
                if self.resolution_due_date
                else None
            ),
            "notified_users": (
                [str(uid) for uid in self.notified_users] if self.notified_users else []
            ),
            "resolved": self.resolved,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }
