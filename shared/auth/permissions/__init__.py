"""Shared permission checking and RBAC utilities"""

from .rbac import ROLE_HIERARCHY, can_access_resource, has_permission, has_role

__all__ = [
    "ROLE_HIERARCHY",
    "has_role",
    "has_permission",
    "can_access_resource",
]
