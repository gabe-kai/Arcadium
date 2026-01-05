"""Password history model for password reuse prevention"""

import uuid
from datetime import datetime, timezone

from app import db
from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class PasswordHistory(db.Model):
    """Password history to prevent password reuse"""

    __tablename__ = "password_history"
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    password_hash = Column(String(255), nullable=False)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )

    # Relationship - passive_deletes=True lets database handle CASCADE
    user = relationship("User", backref="password_history", passive_deletes=True)

    def __repr__(self):
        return f"<PasswordHistory {self.user_id}>"
