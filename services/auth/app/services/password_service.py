"""
Password service for hashing, validation, and history management.
"""
import bcrypt
import re
from typing import Tuple
from datetime import datetime, timezone
from flask import current_app
from app import db
from app.models.user import User
from app.models.password_history import PasswordHistory


class PasswordService:
    """Service for password operations"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password string
        """
        rounds = current_app.config.get('BCRYPT_ROUNDS', 12)
        salt = bcrypt.gensalt(rounds=rounds)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def check_password(password: str, password_hash: str) -> bool:
        """
        Verify password against hash.
        
        Args:
            password: Plain text password
            password_hash: Hashed password
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                password_hash.encode('utf-8')
            )
        except Exception:
            return False
    
    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, str]:
        """
        Validate password strength requirements.
        
        Requirements:
        - Minimum 8 characters
        - Must contain: uppercase, lowercase, number
        - Recommended: special character
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r'\d', password):
            return False, "Password must contain at least one number"
        
        # Special character is recommended but not required
        # We'll just return True if all required checks pass
        
        return True, ""
    
    @staticmethod
    def check_password_history(user_id: str, password: str, max_history: int = 3) -> bool:
        """
        Check if password was recently used (in last max_history passwords).
        
        Args:
            user_id: User UUID
            password: Plain text password to check
            max_history: Maximum number of recent passwords to check
            
        Returns:
            True if password is in history (should not be reused), False otherwise
        """
        # Get recent password history
        recent_passwords = db.session.query(PasswordHistory).filter_by(
            user_id=user_id
        ).order_by(
            PasswordHistory.created_at.desc()
        ).limit(max_history).all()
        
        # Check if password matches any recent password
        for password_history in recent_passwords:
            if PasswordService.check_password(password, password_history.password_hash):
                return True  # Password was recently used
        
        return False  # Password is not in recent history
    
    @staticmethod
    def save_password_history(user_id: str, password_hash: str):
        """
        Save password to history.
        
        Args:
            user_id: User UUID
            password_hash: Hashed password to save
        """
        password_history = PasswordHistory(
            user_id=user_id,
            password_hash=password_hash,
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(password_history)
        db.session.commit()
        
        # Clean up old password history (keep only last 10 per user)
        # This prevents the table from growing too large
        all_passwords = db.session.query(PasswordHistory).filter_by(
            user_id=user_id
        ).order_by(
            PasswordHistory.created_at.desc()
        ).all()
        
        if len(all_passwords) > 10:
            # Delete oldest passwords beyond the limit
            for old_password in all_passwords[10:]:
                db.session.delete(old_password)
            db.session.commit()
