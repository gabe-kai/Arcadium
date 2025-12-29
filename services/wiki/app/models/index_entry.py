"""IndexEntry model for search indexing"""

import uuid
from datetime import datetime, timezone

from app import db
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class IndexEntry(db.Model):
    """Search index entry for pages"""

    __tablename__ = "index_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    page_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    term = Column(String(255), nullable=False, index=True)
    context = Column(Text, nullable=True)
    position = Column(Integer, nullable=True)
    is_keyword = Column(
        Boolean, default=False, index=True
    )  # True for keywords, False for full-text
    is_manual = Column(Boolean, default=False, index=True)  # True if manually tagged
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    page = relationship("Page", backref="index_entries")

    def __repr__(self):
        return f"<IndexEntry {self.term}>"

    def to_dict(self):
        """Convert index entry to dictionary"""
        return {
            "id": str(self.id),
            "page_id": str(self.page_id),
            "term": self.term,
            "context": self.context,
            "position": self.position,
            "is_keyword": self.is_keyword,
            "is_manual": self.is_manual,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
