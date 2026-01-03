# Permission Checking Utilities

Shared RBAC (Role-Based Access Control) utilities for use across all services.

## Usage

### Role Hierarchy

The role hierarchy is:
- `viewer` (level 0) - Read-only access
- `player` (level 1) - Can play/interact
- `writer` (level 2) - Can create/edit content
- `admin` (level 3) - Full administrative access

### Check Role Access

```python
from shared.auth.permissions import has_role, ROLE_HIERARCHY

# Check if user role meets required role
user_role = "writer"
required_role = "player"

if has_role(user_role, required_role):
    print("User has sufficient privileges")
else:
    print("Access denied")

# Access role hierarchy constant
print(f"Admin level: {ROLE_HIERARCHY['admin']}")
```

### Check Permissions

```python
from shared.auth.permissions import has_permission

user_role = "writer"

# Check common permissions
if has_permission(user_role, "write"):
    print("User can write")
if has_permission(user_role, "admin"):
    print("User is admin")  # This will be False for writer
```

### Resource Access Checks

```python
from shared.auth.permissions import can_access_resource

user_role = "writer"
resource_requires = "player"  # Resource requires player level or higher

if can_access_resource(user_role, resource_requires):
    print("User can access resource")
```

## Functions

### `has_role(user_role: str, required_role: str) -> bool`

Check if a user's role meets or exceeds the required role level.

**Examples:**
- `has_role("admin", "writer")` → `True` (admin >= writer)
- `has_role("player", "writer")` → `False` (player < writer)
- `has_role("writer", "writer")` → `True` (writer >= writer)

### `has_permission(user_role: str, permission: str) -> bool`

Check if a user's role has a specific permission.

**Permission mapping:**
- `"read"` → requires `viewer` role
- `"play"` → requires `player` role
- `"write"` → requires `writer` role
- `"admin"` → requires `admin` role

### `can_access_resource(user_role: str, resource_role: str) -> bool`

Check if a user can access a resource based on role requirements.

**Examples:**
- `can_access_resource("writer", "player")` → `True`
- `can_access_resource("viewer", "writer")` → `False`

### `ROLE_HIERARCHY`

Dictionary mapping roles to their hierarchy levels:
```python
ROLE_HIERARCHY = {
    "viewer": 0,
    "player": 1,
    "writer": 2,
    "admin": 3,
}
```
