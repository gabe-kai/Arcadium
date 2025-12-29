"""Page model for wiki pages"""

import uuid
from datetime import datetime, timezone

from app import db
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class Page(db.Model):
    """Wiki page model"""

    __tablename__ = "pages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    file_path = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)

    # Relationships
    parent_id = Column(UUID(as_uuid=True), ForeignKey("pages.id"), nullable=True)
    parent = relationship(
        "Page", remote_side=[id], foreign_keys=[parent_id], backref="children"
    )

    # Organization
    section = Column(String(100), nullable=True, index=True)
    order_index = Column(Integer, default=0)

    # Status
    status = Column(String(20), default="published")  # 'draft' or 'published'
    is_public = Column(Boolean, default=True)

    # Metrics
    word_count = Column(Integer, default=0)
    content_size_kb = Column(Float, default=0.0)

    # Orphanage
    is_orphaned = Column(Boolean, default=False, index=True)
    orphaned_from = Column(UUID(as_uuid=True), ForeignKey("pages.id"), nullable=True)

    # System pages
    is_system_page = Column(Boolean, default=False, index=True)

    # Metadata
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    created_by = Column(UUID(as_uuid=True), nullable=False)
    updated_by = Column(UUID(as_uuid=True), nullable=False)
    version = Column(Integer, default=1)

    def __repr__(self):
        return f"<Page {self.slug}>"

    def to_dict(self):
        """Convert page to dictionary"""
        return {
            "id": str(self.id),
            "title": self.title,
            "slug": self.slug,
            "parent_id": str(self.parent_id) if self.parent_id else None,
            "section": self.section,
            "order": self.order_index,
            "status": self.status,
            "word_count": self.word_count,
            "content_size_kb": self.content_size_kb,
            "is_orphaned": self.is_orphaned,
            "is_system_page": self.is_system_page,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": str(self.created_by),
            "updated_by": str(self.updated_by),
            "version": self.version,
        }
