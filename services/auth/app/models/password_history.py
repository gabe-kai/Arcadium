"""Password history model for password reuse prevention"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app import db


class PasswordHistory(db.Model):
    """Password history to prevent password reuse"""
    __tablename__ = 'password_history'
    __table_args__ = {'schema': 'auth'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('auth.users.id', ondelete='CASCADE'), nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    
    # Relationship
    user = relationship('User', backref='password_history')
    
    def __repr__(self):
        return f'<PasswordHistory {self.user_id}>'
