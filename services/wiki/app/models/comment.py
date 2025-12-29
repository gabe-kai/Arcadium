"""Comment model for wiki page comments"""

import uuid
from datetime import datetime, timezone

from app import db
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class Comment(db.Model):
    """Comment model for wiki pages"""

    __tablename__ = "comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    page_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_comment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("comments.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    user_id = Column(UUID(as_uuid=True), nullable=False)
    content = Column(Text, nullable=False)
    is_recommendation = Column(Boolean, default=False)
    thread_depth = Column(Integer, default=1, index=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    parent_comment = relationship(
        "Comment", remote_side=[id], foreign_keys=[parent_comment_id], backref="replies"
    )
    page = relationship("Page", backref="comments")

    # Constraint: Maximum depth is 5
    __table_args__ = (CheckConstraint("thread_depth <= 5", name="max_thread_depth"),)

    def __repr__(self):
        return f"<Comment {self.id}>"

    def to_dict(self):
        """Convert comment to dictionary"""
        return {
            "id": str(self.id),
            "page_id": str(self.page_id),
            "parent_comment_id": (
                str(self.parent_comment_id) if self.parent_comment_id else None
            ),
            "user_id": str(self.user_id),
            "content": self.content,
            "is_recommendation": self.is_recommendation,
            "thread_depth": self.thread_depth,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
