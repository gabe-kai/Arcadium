"""PageLink model for tracking links between pages"""

import uuid
from datetime import datetime, timezone

from app import db
from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class PageLink(db.Model):
    """Link relationship between pages"""

    __tablename__ = "page_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_page_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    to_page_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    link_text = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    from_page = relationship(
        "Page", foreign_keys=[from_page_id], backref="outgoing_links"
    )
    to_page = relationship("Page", foreign_keys=[to_page_id], backref="incoming_links")

    # Ensure unique link pairs
    __table_args__ = (
        UniqueConstraint("from_page_id", "to_page_id", name="unique_page_link"),
    )

    def __repr__(self):
        return f"<PageLink {self.from_page_id} -> {self.to_page_id}>"

    def to_dict(self):
        """Convert link to dictionary"""
        return {
            "id": str(self.id),
            "from_page_id": str(self.from_page_id),
            "to_page_id": str(self.to_page_id),
            "link_text": self.link_text,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
