"""
Auth service for user registration, login, and token management.
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from flask import current_app
from app import db
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.services.password_service import PasswordService
from app.services.token_service import TokenService
from app.utils.validators import validate_username, validate_email, validate_password, sanitize_username


class AuthService:
    """Service for authentication operations"""
    
    @staticmethod
    def register_user(username: str, email: str, password: str) -> Tuple[User, bool]:
        """
        Register a new user.
        
        First user becomes admin, subsequent users are players.
        
        Args:
            username: Username
            email: Email address
            password: Plain text password
            
        Returns:
            Tuple of (User instance, is_first_user boolean)
            
        Raises:
            ValueError: If validation fails or user already exists
        """
        # Validate inputs
        username = sanitize_username(username)
        is_valid, error = validate_username(username)
        if not is_valid:
            raise ValueError(f"Invalid username: {error}")
        
        is_valid, error = validate_email(email)
        if not is_valid:
            raise ValueError(f"Invalid email: {error}")
        
        is_valid, error = validate_password(password)
        if not is_valid:
            raise ValueError(f"Invalid password: {error}")
        
        # Check if username already exists
        existing_user = db.session.query(User).filter_by(username=username).first()
        if existing_user:
            raise ValueError("Username already exists")
        
        # Check if email already exists
        existing_email = db.session.query(User).filter_by(email=email).first()
        if existing_email:
            raise ValueError("Email already exists")
        
        # Check if this is the first user
        user_count = db.session.query(User).count()
        is_first_user = user_count == 0
        
        # Determine role
        role = 'admin' if is_first_user else 'player'
        
        # Hash password
        password_hash = PasswordService.hash_password(password)
        
        # Create user
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            role=role,
            is_first_user=is_first_user,
            email_verified=False,  # Email verification not implemented yet
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Save password to history
        PasswordService.save_password_history(str(user.id), password_hash)
        
        return user, is_first_user
    
    @staticmethod
    def login_user(username: str, password: str) -> Optional[Tuple[User, str, str]]:
        """
        Login user and generate tokens.
        
        Args:
            username: Username
            password: Plain text password
            
        Returns:
            Tuple of (User, access_token, refresh_token) if successful, None otherwise
        """
        # Sanitize username
        username = sanitize_username(username)
        
        # Find user by username
        user = db.session.query(User).filter_by(username=username).first()
        if not user:
            return None
        
        # Verify password
        if not PasswordService.check_password(password, user.password_hash):
            return None
        
        # Update last login
        user.last_login = datetime.now(timezone.utc)
        user.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        # Generate tokens
        access_token = TokenService.generate_access_token(user)
        refresh_token_str = TokenService.generate_refresh_token(user)
        
        # Store refresh token in database
        expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=current_app.config.get('JWT_REFRESH_TOKEN_EXPIRATION', 604800)
        )
        
        refresh_token = RefreshToken(
            user_id=user.id,
            token_hash=refresh_token_str,  # In production, hash this
            expires_at=expires_at,
            created_at=datetime.now(timezone.utc),
            last_used_at=datetime.now(timezone.utc)
        )
        
        db.session.add(refresh_token)
        db.session.commit()
        
        return user, access_token, refresh_token_str
    
    @staticmethod
    def verify_user_token(token: str) -> Optional[dict]:
        """
        Verify token and return user info.
        
        Args:
            token: JWT access token
            
        Returns:
            Dictionary with user info and token expiration if valid, None otherwise
        """
        payload = TokenService.verify_token(token)
        if not payload:
            return None
        
        # Get user from database
        user_id = payload.get('user_id')
        user = db.session.query(User).filter_by(id=user_id).first()
        if not user:
            return None
        
        return {
            'user_id': str(user.id),
            'username': user.username,
            'role': user.role,
            'expires_at': datetime.fromtimestamp(payload['exp'], tz=timezone.utc).isoformat()
        }
    
    @staticmethod
    def refresh_access_token(refresh_token_str: str) -> Optional[Tuple[str, str]]:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token_str: Refresh token string
            
        Returns:
            Tuple of (new_access_token, new_refresh_token) if valid, None otherwise
        """
        # Find refresh token in database
        refresh_token = db.session.query(RefreshToken).filter_by(
            token_hash=refresh_token_str
        ).first()
        
        if not refresh_token:
            return None
        
        # Check if expired
        if refresh_token.is_expired():
            db.session.delete(refresh_token)
            db.session.commit()
            return None
        
        # Get user
        user = db.session.query(User).filter_by(id=refresh_token.user_id).first()
        if not user:
            return None
        
        # Update refresh token last_used_at
        refresh_token.last_used_at = datetime.now(timezone.utc)
        db.session.commit()
        
        # Generate new access token
        new_access_token = TokenService.generate_access_token(user)
        
        # Optionally rotate refresh token (for now, return same one)
        # In production, you might want to generate a new refresh token
        new_refresh_token = refresh_token_str
        
        return new_access_token, new_refresh_token
    
    @staticmethod
    def logout_user(token: str, user_id: str):
        """
        Logout user by blacklisting token.
        
        Args:
            token: JWT access token
            user_id: User UUID
        """
        # Verify token to get token ID
        payload = TokenService.verify_token(token)
        if not payload:
            return  # Invalid token, nothing to blacklist
        
        token_id = payload.get('jti')
        expires_at = datetime.fromtimestamp(payload['exp'], tz=timezone.utc)
        
        if token_id:
            TokenService.blacklist_token(token_id, user_id, expires_at)
    
    @staticmethod
    def revoke_token(token_id: str, user_id: str, revoke_all: bool = False):
        """
        Revoke token(s).
        
        Args:
            token_id: JWT ID to revoke
            user_id: User UUID
            revoke_all: If True, revoke all user's refresh tokens
        """
        if revoke_all:
            # Revoke all refresh tokens for user
            refresh_tokens = db.session.query(RefreshToken).filter_by(
                user_id=user_id
            ).all()
            
            for refresh_token in refresh_tokens:
                db.session.delete(refresh_token)
            
            db.session.commit()
        else:
            # Revoke specific token
            # For access tokens, add to blacklist
            # For refresh tokens, delete from database
            refresh_token = db.session.query(RefreshToken).filter_by(
                token_hash=token_id
            ).first()
            
            if refresh_token:
                db.session.delete(refresh_token)
                db.session.commit()
