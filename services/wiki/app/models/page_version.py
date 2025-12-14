"""PageVersion model for version history"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, ForeignKey, Text, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import JSON
from sqlalchemy.orm import relationship
from app import db


class PageVersion(db.Model):
    """Version history for wiki pages"""
    __tablename__ = 'page_versions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    page_id = Column(UUID(as_uuid=True), ForeignKey('pages.id', ondelete='CASCADE'), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)  # Full markdown content
    changed_by = Column(UUID(as_uuid=True), nullable=False)
    change_summary = Column(Text, nullable=True)
    # Use JSONB for PostgreSQL, JSON for SQLite (fallback)
    diff_data = Column(JSON, nullable=True)  # Stores diff information
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    page = relationship('Page', backref='versions')
    
    # Ensure unique version per page
    __table_args__ = (
        UniqueConstraint('page_id', 'version', name='unique_page_version'),
    )
    
    def __repr__(self):
        return f'<PageVersion {self.page_id} v{self.version}>'
    
    def to_dict(self):
        """Convert version to dictionary"""
        return {
            'id': str(self.id),
            'page_id': str(self.page_id),
            'version': self.version,
            'title': self.title,
            'content': self.content,
            'changed_by': str(self.changed_by),
            'change_summary': self.change_summary,
            'diff_data': self.diff_data,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

