"""Image model for uploaded images"""

import uuid
from datetime import datetime, timezone

from app import db
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class Image(db.Model):
    """Image metadata model"""

    __tablename__ = "images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    uuid = Column(
        String(255), unique=True, nullable=False, index=True
    )  # UUID used in filename
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    mime_type = Column(String(100), nullable=True)
    size_bytes = Column(Integer, nullable=True)
    uploaded_by = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    pages = relationship(
        "PageImage", back_populates="image", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Image {self.uuid}>"

    def to_dict(self):
        """Convert image to dictionary"""
        return {
            "id": str(self.id),
            "uuid": self.uuid,
            "original_filename": self.original_filename,
            "file_path": self.file_path,
            "mime_type": self.mime_type,
            "size_bytes": self.size_bytes,
            "uploaded_by": str(self.uploaded_by),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PageImage(db.Model):
    """Junction table for page-image associations"""

    __tablename__ = "page_images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    page_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    image_id = Column(
        UUID(as_uuid=True),
        ForeignKey("images.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    page = relationship("Page", backref="page_images")
    image = relationship("Image", back_populates="pages")

    # Ensure unique page-image pairs
    __table_args__ = (
        UniqueConstraint("page_id", "image_id", name="unique_page_image"),
    )

    def __repr__(self):
        return f"<PageImage {self.page_id} <-> {self.image_id}>"
