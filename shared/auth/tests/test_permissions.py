"""Tests for permission checking utilities"""

from shared.auth.permissions.rbac import (
    ROLE_HIERARCHY,
    can_access_resource,
    has_permission,
    has_role,
)


class TestRoleHierarchy:
    """Tests for ROLE_HIERARCHY constant"""

    def test_role_hierarchy_exists(self):
        """Test that ROLE_HIERARCHY is defined"""
        assert ROLE_HIERARCHY is not None
        assert isinstance(ROLE_HIERARCHY, dict)

    def test_role_hierarchy_values(self):
        """Test that role hierarchy has correct values"""
        assert ROLE_HIERARCHY["viewer"] == 0
        assert ROLE_HIERARCHY["player"] == 1
        assert ROLE_HIERARCHY["writer"] == 2
        assert ROLE_HIERARCHY["admin"] == 3

    def test_role_hierarchy_ordering(self):
        """Test that roles are ordered correctly"""
        assert ROLE_HIERARCHY["viewer"] < ROLE_HIERARCHY["player"]
        assert ROLE_HIERARCHY["player"] < ROLE_HIERARCHY["writer"]
        assert ROLE_HIERARCHY["writer"] < ROLE_HIERARCHY["admin"]


class TestHasRole:
    """Tests for has_role function"""

    def test_admin_meets_writer_requirement(self):
        """Test that admin role meets writer requirement"""
        assert has_role("admin", "writer") is True

    def test_writer_meets_player_requirement(self):
        """Test that writer role meets player requirement"""
        assert has_role("writer", "player") is True

    def test_player_does_not_meet_writer_requirement(self):
        """Test that player role does not meet writer requirement"""
        assert has_role("player", "writer") is False

    def test_same_role_meets_requirement(self):
        """Test that same role meets requirement"""
        assert has_role("writer", "writer") is True
        assert has_role("admin", "admin") is True
        assert has_role("player", "player") is True
        assert has_role("viewer", "viewer") is True

    def test_viewer_does_not_meet_admin_requirement(self):
        """Test that viewer role does not meet admin requirement"""
        assert has_role("viewer", "admin") is False

    def test_invalid_user_role(self):
        """Test with invalid user role"""
        assert has_role("invalid_role", "player") is False

    def test_invalid_required_role(self):
        """Test with invalid required role"""
        assert has_role("admin", "invalid_role") is False

    def test_all_valid_combinations(self):
        """Test all valid role combinations"""
        # Admin can do everything
        assert has_role("admin", "viewer") is True
        assert has_role("admin", "player") is True
        assert has_role("admin", "writer") is True
        assert has_role("admin", "admin") is True

        # Writer can do viewer, player, writer
        assert has_role("writer", "viewer") is True
        assert has_role("writer", "player") is True
        assert has_role("writer", "writer") is True
        assert has_role("writer", "admin") is False

        # Player can do viewer, player
        assert has_role("player", "viewer") is True
        assert has_role("player", "player") is True
        assert has_role("player", "writer") is False
        assert has_role("player", "admin") is False

        # Viewer can only do viewer
        assert has_role("viewer", "viewer") is True
        assert has_role("viewer", "player") is False
        assert has_role("viewer", "writer") is False
        assert has_role("viewer", "admin") is False


class TestHasPermission:
    """Tests for has_permission function"""

    def test_read_permission(self):
        """Test read permission (requires viewer)"""
        assert has_permission("viewer", "read") is True
        assert has_permission("player", "read") is True
        assert has_permission("writer", "read") is True
        assert has_permission("admin", "read") is True

    def test_play_permission(self):
        """Test play permission (requires player)"""
        assert has_permission("viewer", "play") is False
        assert has_permission("player", "play") is True
        assert has_permission("writer", "play") is True
        assert has_permission("admin", "play") is True

    def test_write_permission(self):
        """Test write permission (requires writer)"""
        assert has_permission("viewer", "write") is False
        assert has_permission("player", "write") is False
        assert has_permission("writer", "write") is True
        assert has_permission("admin", "write") is True

    def test_admin_permission(self):
        """Test admin permission (requires admin)"""
        assert has_permission("viewer", "admin") is False
        assert has_permission("player", "admin") is False
        assert has_permission("writer", "admin") is False
        assert has_permission("admin", "admin") is True

    def test_invalid_permission(self):
        """Test with invalid permission"""
        assert has_permission("admin", "invalid_permission") is False

    def test_invalid_role(self):
        """Test with invalid role"""
        assert has_permission("invalid_role", "read") is False


class TestCanAccessResource:
    """Tests for can_access_resource function"""

    def test_admin_accesses_player_resource(self):
        """Test that admin can access player-level resource"""
        assert can_access_resource("admin", "player") is True

    def test_writer_accesses_player_resource(self):
        """Test that writer can access player-level resource"""
        assert can_access_resource("writer", "player") is True

    def test_player_accesses_player_resource(self):
        """Test that player can access player-level resource"""
        assert can_access_resource("player", "player") is True

    def test_viewer_cannot_access_player_resource(self):
        """Test that viewer cannot access player-level resource"""
        assert can_access_resource("viewer", "player") is False

    def test_writer_cannot_access_admin_resource(self):
        """Test that writer cannot access admin-level resource"""
        assert can_access_resource("writer", "admin") is False

    def test_all_valid_combinations(self):
        """Test all valid resource access combinations"""
        # Admin can access everything
        assert can_access_resource("admin", "viewer") is True
        assert can_access_resource("admin", "player") is True
        assert can_access_resource("admin", "writer") is True
        assert can_access_resource("admin", "admin") is True

        # Writer can access viewer, player, writer
        assert can_access_resource("writer", "viewer") is True
        assert can_access_resource("writer", "player") is True
        assert can_access_resource("writer", "writer") is True
        assert can_access_resource("writer", "admin") is False

        # Player can access viewer, player
        assert can_access_resource("player", "viewer") is True
        assert can_access_resource("player", "player") is True
        assert can_access_resource("player", "writer") is False
        assert can_access_resource("player", "admin") is False

        # Viewer can only access viewer
        assert can_access_resource("viewer", "viewer") is True
        assert can_access_resource("viewer", "player") is False
        assert can_access_resource("viewer", "writer") is False
        assert can_access_resource("viewer", "admin") is False
