"""
Role-Based Access Control (RBAC) utilities for shared use across services.

These utilities provide permission checking functionality that can be used
by any service that needs to validate user permissions based on roles.
"""

# Role hierarchy: higher number = higher privilege
ROLE_HIERARCHY = {
    "viewer": 0,
    "player": 1,
    "writer": 2,
    "admin": 3,
}

# Valid roles
VALID_ROLES = set(ROLE_HIERARCHY.keys())


def has_role(user_role: str, required_role: str) -> bool:
    """
    Check if a user's role meets or exceeds the required role level.

    Args:
        user_role: The user's role (viewer, player, writer, admin)
        required_role: The required role level

    Returns:
        True if user_role >= required_role in hierarchy, False otherwise

    Examples:
        >>> has_role("admin", "writer")  # True - admin >= writer
        >>> has_role("player", "writer")  # False - player < writer
        >>> has_role("writer", "writer")  # True - writer >= writer
    """
    user_level = ROLE_HIERARCHY.get(user_role, -1)
    required_level = ROLE_HIERARCHY.get(required_role, -1)

    # Invalid roles return False
    if user_level == -1 or required_level == -1:
        return False

    return user_level >= required_level


def has_permission(user_role: str, permission: str) -> bool:
    """
    Check if a user's role has a specific permission.

    This is a convenience function that maps common permissions to role requirements.
    For custom permission logic, use has_role() directly.

    Args:
        user_role: The user's role
        permission: The permission to check (maps to a role requirement)

    Returns:
        True if user has permission, False otherwise

    Permission mapping:
        - "read" -> viewer
        - "play" -> player
        - "write" -> writer
        - "admin" -> admin
    """
    permission_to_role = {
        "read": "viewer",
        "play": "player",
        "write": "writer",
        "admin": "admin",
    }

    required_role = permission_to_role.get(permission)
    if not required_role:
        return False

    return has_role(user_role, required_role)


def can_access_resource(user_role: str, resource_role: str) -> bool:
    """
    Check if a user can access a resource based on role requirements.

    This is useful for checking if a user can access a resource that has
    a minimum role requirement.

    Args:
        user_role: The user's role
        resource_role: The minimum role required to access the resource

    Returns:
        True if user can access resource, False otherwise

    Examples:
        >>> can_access_resource("writer", "player")  # True - writer can access player resources
        >>> can_access_resource("viewer", "writer")  # False - viewer cannot access writer resources
    """
    return has_role(user_role, resource_role)
