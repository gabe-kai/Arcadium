"""WikiConfig model for system configuration"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, ForeignKey, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app import db


class WikiConfig(db.Model):
    """System configuration stored as key-value pairs"""
    __tablename__ = 'wiki_config'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    updated_by = Column(UUID(as_uuid=True), nullable=False)
    
    def __repr__(self):
        return f'<WikiConfig {self.key}={self.value}>'
    
    def to_dict(self):
        """Convert config to dictionary"""
        return {
            'id': str(self.id),
            'key': self.key,
            'value': self.value,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'updated_by': str(self.updated_by)
        }

