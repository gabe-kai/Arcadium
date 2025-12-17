"""User model for authentication"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app import db


class User(db.Model):
    """User model for authentication and authorization"""
    __tablename__ = 'users'
    __table_args__ = {'schema': 'auth'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default='player', nullable=False, index=True)
    
    # User flags
    is_system_user = Column(Boolean, default=False, nullable=False)
    is_first_user = Column(Boolean, default=False, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False, index=True)
    email_verification_token = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def to_dict(self, include_email=False):
        """Convert user to dictionary"""
        data = {
            'id': str(self.id),
            'username': self.username,
            'role': self.role,
            'is_system_user': self.is_system_user,
            'is_first_user': self.is_first_user,
            'email_verified': self.email_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
        }
        if include_email:
            data['email'] = self.email
        return data
    
    def is_admin(self):
        """Check if user is admin"""
        return self.role == 'admin'
    
    def is_writer(self):
        """Check if user is writer or admin"""
        return self.role in ('writer', 'admin')
    
    def is_player(self):
        """Check if user is player, writer, or admin"""
        return self.role in ('player', 'writer', 'admin')
    
    def has_role(self, required_role):
        """Check if user has required role or higher"""
        role_hierarchy = {
            'viewer': 0,
            'player': 1,
            'writer': 2,
            'admin': 3
        }
        user_level = role_hierarchy.get(self.role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        return user_level >= required_level
