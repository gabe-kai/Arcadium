"""Tests for user management endpoints"""

import pytest
from app import db
from app.models.user import User
from app.services.auth_service import AuthService
from app.services.token_service import TokenService


@pytest.fixture
def admin_user_id(app):
    """Create an admin user (first user) and return user ID"""
    with app.app_context():
        user, _ = AuthService.register_user(
            username="admin", email="admin@example.com", password="AdminPass123"
        )
        db.session.commit()
        return str(user.id)


@pytest.fixture
def test_user_id(app, admin_user_id):
    """Create a test user (non-admin, second user) and return user ID"""
    with app.app_context():
        user, _ = AuthService.register_user(
            username="testuser", email="test@example.com", password="TestPass123"
        )
        db.session.commit()
        return str(user.id)


@pytest.fixture
def test_user_with_token(app, admin_user_id, test_user_id):
    """Create a test user (non-admin) and return user info with access token"""
    with app.app_context():
        result = AuthService.login_user("testuser", "TestPass123")
        if result:
            user, access_token, refresh_token = result
            db.session.commit()
            return {
                "user_id": str(user.id),
                "username": user.username,
                "access_token": access_token,
            }
        return None


@pytest.fixture
def admin_user_with_token(app, admin_user_id):
    """Get admin user token (reuses admin_user_id fixture)"""
    with app.app_context():
        result = AuthService.login_user("admin", "AdminPass123")
        if result:
            admin_user, access_token, refresh_token = result
            db.session.commit()
            return {
                "user_id": str(admin_user.id),
                "username": admin_user.username,
                "access_token": access_token,
            }
        return None


class TestGetUserProfile:
    """Tests for GET /api/users/{user_id}"""

    def test_get_user_profile_as_self(self, client, app, test_user_with_token):
        """Test getting own user profile"""
        with app.app_context():
            tokens = test_user_with_token
            if not tokens:
                pytest.skip("Failed to create test user with token")

            user_id = tokens["user_id"]
            access_token = tokens["access_token"]

            response = client.get(
                f"/api/users/{user_id}",
                headers={"Authorization": f"Bearer {access_token}"},
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data["id"] == user_id
            assert data["username"] == "testuser"
            assert "email" in data  # Email included for self
            assert data["email"] == "test@example.com"

    def test_get_user_profile_as_admin(
        self, client, app, admin_user_with_token, test_user_id
    ):
        """Test admin getting another user's profile"""
        with app.app_context():
            admin_tokens = admin_user_with_token
            if not admin_tokens:
                pytest.skip("Failed to create admin user with token")

            admin_token = admin_tokens["access_token"]

            response = client.get(
                f"/api/users/{test_user_id}",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data["id"] == test_user_id
            assert data["username"] == "testuser"
            assert "email" in data  # Email included for admin
            assert data["email"] == "test@example.com"

    def test_get_user_profile_unauthorized(
        self, client, app, test_user_with_token, admin_user_with_token
    ):
        """Test non-admin user trying to get another user's profile"""
        with app.app_context():
            tokens = test_user_with_token
            admin_tokens = admin_user_with_token
            if not tokens or not admin_tokens:
                pytest.skip("Failed to create test users")

            user_token = tokens["access_token"]
            admin_user_id = admin_tokens["user_id"]

            response = client.get(
                f"/api/users/{admin_user_id}",
                headers={"Authorization": f"Bearer {user_token}"},
            )

            assert response.status_code == 403
            data = response.get_json()
            assert "error" in data

    def test_get_user_profile_not_found(self, client, app, admin_user_with_token):
        """Test getting non-existent user profile"""
        with app.app_context():
            admin_tokens = admin_user_with_token
            if not admin_tokens:
                pytest.skip("Failed to create admin user with token")

            admin_token = admin_tokens["access_token"]

            response = client.get(
                "/api/users/00000000-0000-0000-0000-000000000000",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

            assert response.status_code == 404
            data = response.get_json()
            assert "error" in data

    def test_get_user_profile_invalid_id(self, client, app, admin_user_with_token):
        """Test getting user profile with invalid UUID"""
        with app.app_context():
            admin_tokens = admin_user_with_token
            if not admin_tokens:
                pytest.skip("Failed to create admin user with token")

            admin_token = admin_tokens["access_token"]

            response = client.get(
                "/api/users/invalid-uuid",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

            assert response.status_code == 400
            data = response.get_json()
            assert "error" in data

    def test_get_user_profile_no_auth(self, client, app, test_user_id):
        """Test getting user profile without authentication"""
        response = client.get(f"/api/users/{test_user_id}")

        assert response.status_code == 401
        data = response.get_json()
        assert "error" in data


class TestUpdateUserProfile:
    """Tests for PUT /api/users/{user_id}"""

    def test_update_user_profile_email_as_self(self, client, app, test_user_with_token):
        """Test updating own email"""
        with app.app_context():
            tokens = test_user_with_token
            if not tokens:
                pytest.skip("Failed to create test user with token")

            user_id = tokens["user_id"]
            access_token = tokens["access_token"]

            response = client.put(
                f"/api/users/{user_id}",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"email": "newemail@example.com"},
                content_type="application/json",
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data["email"] == "newemail@example.com"

            # Verify in database
            user = db.session.query(User).filter_by(id=user_id).first()
            assert user.email == "newemail@example.com"

    def test_update_user_profile_password_as_self(
        self, client, app, test_user_with_token
    ):
        """Test updating own password"""
        with app.app_context():
            tokens = test_user_with_token
            if not tokens:
                pytest.skip("Failed to create test user with token")

            user_id = tokens["user_id"]
            access_token = tokens["access_token"]

            response = client.put(
                f"/api/users/{user_id}",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"password": "NewPassword123"},
                content_type="application/json",
            )

            assert response.status_code == 200

            # Verify password was changed by checking database
            from app.services.password_service import PasswordService

            user = db.session.query(User).filter_by(id=user_id).first()
            assert PasswordService.check_password("NewPassword123", user.password_hash)

    def test_update_user_profile_as_admin(
        self, client, app, admin_user_with_token, test_user_id
    ):
        """Test admin updating another user's profile"""
        with app.app_context():
            admin_tokens = admin_user_with_token
            if not admin_tokens:
                pytest.skip("Failed to create admin user with token")

            admin_token = admin_tokens["access_token"]

            response = client.put(
                f"/api/users/{test_user_id}",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={"email": "adminupdated@example.com"},
                content_type="application/json",
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data["email"] == "adminupdated@example.com"

    def test_update_user_profile_unauthorized(
        self, client, app, test_user_with_token, admin_user_with_token
    ):
        """Test non-admin user trying to update another user's profile"""
        with app.app_context():
            tokens = test_user_with_token
            admin_tokens = admin_user_with_token
            if not tokens or not admin_tokens:
                pytest.skip("Failed to create test users")

            user_token = tokens["access_token"]
            admin_user_id = admin_tokens["user_id"]

            response = client.put(
                f"/api/users/{admin_user_id}",
                headers={"Authorization": f"Bearer {user_token}"},
                json={"email": "hacked@example.com"},
                content_type="application/json",
            )

            assert response.status_code == 403
            data = response.get_json()
            assert "error" in data

    def test_update_user_profile_duplicate_email(
        self, client, app, test_user_with_token, admin_user_with_token
    ):
        """Test updating email to one that's already taken"""
        with app.app_context():
            tokens = test_user_with_token
            admin_tokens = admin_user_with_token
            if not tokens or not admin_tokens:
                pytest.skip("Failed to create test users")

            user_token = tokens["access_token"]
            user_id = tokens["user_id"]
            admin_email = "admin@example.com"  # From admin_user_with_token fixture

            response = client.put(
                f"/api/users/{user_id}",
                headers={"Authorization": f"Bearer {user_token}"},
                json={"email": admin_email},
                content_type="application/json",
            )

            assert response.status_code == 400
            data = response.get_json()
            assert "error" in data
            assert "email" in data["error"].lower()

    def test_update_user_profile_invalid_email(self, client, app, test_user_with_token):
        """Test updating with invalid email format"""
        with app.app_context():
            tokens = test_user_with_token
            if not tokens:
                pytest.skip("Failed to create test user with token")

            user_id = tokens["user_id"]
            access_token = tokens["access_token"]

            response = client.put(
                f"/api/users/{user_id}",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"email": "invalid-email"},
                content_type="application/json",
            )

            assert response.status_code == 400
            data = response.get_json()
            assert "error" in data

    def test_update_user_profile_invalid_password(
        self, client, app, test_user_with_token
    ):
        """Test updating with invalid password (too weak)"""
        with app.app_context():
            tokens = test_user_with_token
            if not tokens:
                pytest.skip("Failed to create test user with token")

            user_id = tokens["user_id"]
            access_token = tokens["access_token"]

            response = client.put(
                f"/api/users/{user_id}",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"password": "weak"},
                content_type="application/json",
            )

            assert response.status_code == 400
            data = response.get_json()
            assert "error" in data


class TestGetUserByUsername:
    """Tests for GET /api/users/username/{username}"""

    def test_get_user_by_username_success(self, client, app, test_user_id):
        """Test getting user by username (public endpoint)"""
        response = client.get("/api/users/username/testuser")

        assert response.status_code == 200
        data = response.get_json()
        assert data["username"] == "testuser"
        assert "email" not in data  # Email not included in public endpoint

    def test_get_user_by_username_not_found(self, client, app):
        """Test getting non-existent user by username"""
        response = client.get("/api/users/username/nonexistent")

        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data


class TestUpdateUserRole:
    """Tests for PUT /api/users/{user_id}/role"""

    def test_update_user_role_as_admin(
        self, client, app, admin_user_with_token, test_user_id
    ):
        """Test admin updating user role"""
        with app.app_context():
            admin_tokens = admin_user_with_token
            if not admin_tokens:
                pytest.skip("Failed to create admin user with token")

            admin_token = admin_tokens["access_token"]

            response = client.put(
                f"/api/users/{test_user_id}/role",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={"role": "writer"},
                content_type="application/json",
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data["role"] == "writer"

            # Verify in database
            user = db.session.query(User).filter_by(id=test_user_id).first()
            assert user.role == "writer"

    def test_update_user_role_unauthorized(
        self, client, app, test_user_with_token, test_user_id
    ):
        """Test non-admin user trying to update role"""
        with app.app_context():
            tokens = test_user_with_token
            if not tokens:
                pytest.skip("Failed to create test user with token")

            user_token = tokens["access_token"]

            response = client.put(
                f"/api/users/{test_user_id}/role",
                headers={"Authorization": f"Bearer {user_token}"},
                json={"role": "writer"},
                content_type="application/json",
            )

            assert response.status_code == 403
            data = response.get_json()
            assert "error" in data

    def test_update_user_role_invalid_role(
        self, client, app, admin_user_with_token, test_user_id
    ):
        """Test updating role with invalid role value"""
        with app.app_context():
            admin_tokens = admin_user_with_token
            if not admin_tokens:
                pytest.skip("Failed to create admin user with token")

            admin_token = admin_tokens["access_token"]

            response = client.put(
                f"/api/users/{test_user_id}/role",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={"role": "invalid-role"},
                content_type="application/json",
            )

            assert response.status_code == 400
            data = response.get_json()
            assert "error" in data

    def test_update_first_user_role(self, client, app, admin_user_with_token):
        """Test trying to update first user's role (should fail)"""
        with app.app_context():
            admin_tokens = admin_user_with_token
            if not admin_tokens:
                pytest.skip("Failed to create admin user with token")

            admin_token = admin_tokens["access_token"]
            admin_user_id = admin_tokens["user_id"]

            # First user is admin
            user = db.session.query(User).filter_by(id=admin_user_id).first()
            assert user.is_first_user is True

            response = client.put(
                f"/api/users/{admin_user_id}/role",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={"role": "player"},
                content_type="application/json",
            )

            assert response.status_code == 403
            data = response.get_json()
            assert "error" in data
            assert "first user" in data["error"].lower()


class TestListUsers:
    """Tests for GET /api/users"""

    def test_list_users_as_admin(self, client, app, admin_user_with_token):
        """Test admin listing users"""
        with app.app_context():
            admin_tokens = admin_user_with_token
            if not admin_tokens:
                pytest.skip("Failed to create admin user with token")

            admin_token = admin_tokens["access_token"]

            response = client.get(
                "/api/users", headers={"Authorization": f"Bearer {admin_token}"}
            )

            assert response.status_code == 200
            data = response.get_json()
            assert "users" in data
            assert "total" in data
            assert "limit" in data
            assert "offset" in data
            assert len(data["users"]) > 0

    def test_list_users_with_role_filter(self, client, app, admin_user_with_token):
        """Test listing users filtered by role"""
        with app.app_context():
            admin_tokens = admin_user_with_token
            if not admin_tokens:
                pytest.skip("Failed to create admin user with token")

            admin_token = admin_tokens["access_token"]

            response = client.get(
                "/api/users?role=admin",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

            assert response.status_code == 200
            data = response.get_json()
            assert all(user["role"] == "admin" for user in data["users"])

    def test_list_users_with_pagination(self, client, app, admin_user_with_token):
        """Test listing users with pagination"""
        with app.app_context():
            admin_tokens = admin_user_with_token
            if not admin_tokens:
                pytest.skip("Failed to create admin user with token")

            admin_token = admin_tokens["access_token"]

            response = client.get(
                "/api/users?limit=1&offset=0",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data["limit"] == 1
            assert data["offset"] == 0
            assert len(data["users"]) <= 1

    def test_list_users_unauthorized(self, client, app, test_user_with_token):
        """Test non-admin user trying to list users"""
        with app.app_context():
            tokens = test_user_with_token
            if not tokens:
                pytest.skip("Failed to create test user with token")

            user_token = tokens["access_token"]

            response = client.get(
                "/api/users", headers={"Authorization": f"Bearer {user_token}"}
            )

            assert response.status_code == 403
            data = response.get_json()
            assert "error" in data


class TestCreateSystemUser:
    """Tests for POST /api/users/system"""

    def test_create_system_user_with_service_token(self, client, app):
        """Test creating system user with valid service token"""
        with app.app_context():
            # Generate a service token
            service_token = TokenService.generate_service_token(
                "test-service", "test-id"
            )

            response = client.post(
                "/api/users/system",
                headers={"Authorization": f"Service-Token {service_token}"},
                json={
                    "username": "systemuser",
                    "email": "system@example.com",
                    "role": "admin",
                },
                content_type="application/json",
            )

            assert response.status_code == 201
            data = response.get_json()
            assert data["username"] == "systemuser"
            assert data["is_system_user"] is True
            assert data["role"] == "admin"

            # Verify in database
            user = db.session.query(User).filter_by(username="systemuser").first()
            assert user is not None
            assert user.is_system_user is True

    def test_create_system_user_with_user_token(
        self, client, app, admin_user_with_token
    ):
        """Test creating system user with user token (should fail)"""
        with app.app_context():
            admin_tokens = admin_user_with_token
            if not admin_tokens:
                pytest.skip("Failed to create admin user with token")

            admin_token = admin_tokens["access_token"]

            response = client.post(
                "/api/users/system",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "username": "systemuser2",
                    "email": "system2@example.com",
                    "role": "admin",
                },
                content_type="application/json",
            )

            assert response.status_code == 401
            data = response.get_json()
            assert "error" in data

    def test_create_system_user_duplicate_username(self, client, app):
        """Test creating system user with duplicate username"""
        with app.app_context():
            # Generate a service token
            service_token = TokenService.generate_service_token(
                "test-service", "test-id"
            )

            # Create first system user
            response1 = client.post(
                "/api/users/system",
                headers={"Authorization": f"Service-Token {service_token}"},
                json={
                    "username": "duplicateuser",
                    "email": "dup1@example.com",
                    "role": "admin",
                },
                content_type="application/json",
            )
            assert response1.status_code == 201

            # Try to create another with same username
            response2 = client.post(
                "/api/users/system",
                headers={"Authorization": f"Service-Token {service_token}"},
                json={
                    "username": "duplicateuser",
                    "email": "dup2@example.com",
                    "role": "admin",
                },
                content_type="application/json",
            )

            assert response2.status_code == 400
            data = response2.get_json()
            assert "error" in data
            assert "username" in data["error"].lower()

    def test_create_system_user_invalid_role(self, client, app):
        """Test creating system user with invalid role"""
        with app.app_context():
            service_token = TokenService.generate_service_token(
                "test-service", "test-id"
            )

            response = client.post(
                "/api/users/system",
                headers={"Authorization": f"Service-Token {service_token}"},
                json={
                    "username": "invalidroleuser",
                    "email": "invalid@example.com",
                    "role": "invalid-role",
                },
                content_type="application/json",
            )

            assert response.status_code == 400
            data = response.get_json()
            assert "error" in data
