"""Authentication and authorization middleware"""
import uuid
from functools import wraps
from flask import request, jsonify, current_app
from typing import Optional, Callable, List


def get_auth_token() -> Optional[str]:
    """
    Extract JWT token from Authorization header.
    
    Returns:
        Token string if found, None otherwise
    """
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header[7:]  # Remove 'Bearer ' prefix
    return None


def get_user_from_token(token: str) -> Optional[dict]:
    """
    Validate JWT token and extract user information.
    
    For now, this is a placeholder that will be replaced with actual
    Auth Service integration. In production, this should:
    1. Call Auth Service /api/auth/verify endpoint, OR
    2. Use shared JWT validation library from shared/auth/
    
    Args:
        token: JWT token string
        
    Returns:
        Dict with user_id, username, role if valid, None otherwise
    """
    # TODO: Integrate with Auth Service
    # For now, return None to indicate no authentication
    # This allows public endpoints to work
    return None


def require_auth(f: Callable) -> Callable:
    """
    Decorator to require authentication for an endpoint.
    
    Sets request.user_id and request.user_role if token is valid.
    Returns 401 if token is missing or invalid.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_auth_token()
        if not token:
            return jsonify({'error': 'Authentication required'}), 401
        
        user = get_user_from_token(token)
        if not user:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Attach user info to request object
        request.user_id = uuid.UUID(user['user_id'])
        request.user_role = user['role']
        request.username = user.get('username', '')
        
        return f(*args, **kwargs)
    
    return decorated_function


def require_role(allowed_roles: List[str]):
    """
    Decorator to require specific role(s) for an endpoint.
    
    Must be used after @require_auth or will return 401.
    
    Args:
        allowed_roles: List of allowed roles (e.g., ['writer', 'admin'])
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if user is authenticated
            if not hasattr(request, 'user_role'):
                return jsonify({'error': 'Authentication required'}), 401
            
            user_role = request.user_role
            
            # Role hierarchy: admin > writer > player > viewer
            role_hierarchy = {
                'admin': 4,
                'writer': 3,
                'player': 2,
                'viewer': 1
            }
            
            user_level = role_hierarchy.get(user_role, 0)
            
            # Check if user has one of the allowed roles
            for role in allowed_roles:
                required_level = role_hierarchy.get(role, 0)
                if user_level >= required_level:
                    return f(*args, **kwargs)
            
            return jsonify({
                'error': 'Insufficient permissions',
                'required_role': allowed_roles[0] if len(allowed_roles) == 1 else allowed_roles
            }), 403
        
        return decorated_function
    return decorator


def optional_auth(f: Callable) -> Callable:
    """
    Decorator to optionally authenticate if token is provided.
    
    Sets request.user_id and request.user_role if token is valid.
    Does not return error if token is missing (for public endpoints).
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_auth_token()
        if token:
            user = get_user_from_token(token)
            if user:
                request.user_id = uuid.UUID(user['user_id'])
                request.user_role = user['role']
                request.username = user.get('username', '')
            else:
                # Invalid token, but don't fail - treat as unauthenticated
                request.user_id = None
                request.user_role = 'viewer'
                request.username = None
        else:
            # No token, treat as viewer
            request.user_id = None
            request.user_role = 'viewer'
            request.username = None
        
        return f(*args, **kwargs)
    
    return decorated_function


def get_current_user() -> Optional[dict]:
    """
    Get current authenticated user information from request.
    
    Returns:
        Dict with user_id, role, username if authenticated, None otherwise
    """
    if hasattr(request, 'user_id') and request.user_id:
        return {
            'user_id': request.user_id,
            'role': getattr(request, 'user_role', 'viewer'),
            'username': getattr(request, 'username', '')
        }
    return None

