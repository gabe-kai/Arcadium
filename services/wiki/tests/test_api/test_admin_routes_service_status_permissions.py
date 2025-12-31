"""Tests for service status endpoint permissions and role-based access"""

from unittest.mock import MagicMock, patch

from tests.test_api.conftest import auth_headers, mock_auth


def test_get_service_status_requires_auth(client):
    """Get service status should require authentication"""
    # Request without authentication should return 401
    # Note: We don't need to mock check_all_services since the auth check happens first
    resp = client.get("/api/admin/service-status")
    assert resp.status_code == 401


@patch("app.routes.admin_routes.ServiceStatusService.check_all_services")
def test_get_service_status_allows_authenticated_users(
    mock_check_all, client, app, test_writer_id
):
    """Get service status should allow any authenticated user (not just admin)"""
    mock_check_all.return_value = {
        "wiki": {
            "status": "healthy",
            "response_time_ms": 5.0,
            "error": None,
            "details": {"service": "wiki"},
        },
        "auth": {
            "status": "healthy",
            "response_time_ms": 12.0,
            "error": None,
            "details": {"service": "auth"},
        },
    }

    # Writer (non-admin) should be able to access
    with mock_auth(test_writer_id, "writer"):
        headers = auth_headers(test_writer_id, "writer")
        resp = client.get("/api/admin/service-status", headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "services" in data
        assert "wiki" in data["services"]
        assert data["services"]["wiki"]["status"] == "healthy"


@patch("app.routes.admin_routes.ServiceStatusService.check_all_services")
def test_get_service_status_allows_viewer_role(
    mock_check_all, client, app, test_viewer_id
):
    """Get service status should allow viewer role (lowest privilege)"""
    mock_check_all.return_value = {
        "wiki": {
            "status": "healthy",
            "response_time_ms": 5.0,
            "error": None,
            "details": {"service": "wiki"},
        }
    }

    # Viewer should be able to access
    with mock_auth(test_viewer_id, "viewer"):
        headers = auth_headers(test_viewer_id, "viewer")
        resp = client.get("/api/admin/service-status", headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "services" in data


@patch("app.routes.admin_routes.ServiceStatusService.check_all_services")
def test_get_service_status_allows_admin_role(
    mock_check_all, client, app, test_admin_id
):
    """Get service status should allow admin role"""
    mock_check_all.return_value = {
        "wiki": {
            "status": "healthy",
            "response_time_ms": 5.0,
            "error": None,
            "details": {"service": "wiki"},
        }
    }

    # Admin should be able to access
    with mock_auth(test_admin_id, "admin"):
        headers = auth_headers(test_admin_id, "admin")
        resp = client.get("/api/admin/service-status", headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "services" in data


@patch("app.routes.admin_routes.ServiceStatusService.create_or_update_status_page")
@patch("app.routes.admin_routes.ServiceStatusService.check_all_services")
def test_refresh_service_status_requires_auth(mock_check_all, mock_create_page, client):
    """Refresh service status should require authentication"""
    mock_check_all.return_value = {
        "wiki": {
            "status": "healthy",
            "response_time_ms": 5.0,
            "error": None,
            "details": {},
        }
    }

    # Request without authentication should return 401
    resp = client.post("/api/admin/service-status/refresh")
    assert resp.status_code == 401


@patch("app.routes.admin_routes.ServiceStatusService.create_or_update_status_page")
@patch("app.routes.admin_routes.ServiceStatusService.check_all_services")
def test_refresh_service_status_allows_authenticated_users(
    mock_check_all, mock_create_page, client, app, test_writer_id
):
    """Refresh service status should allow any authenticated user (not just admin)"""
    import uuid

    from app.models.page import Page

    mock_check_all.return_value = {
        "wiki": {
            "status": "healthy",
            "response_time_ms": 5.0,
            "error": None,
            "details": {},
        }
    }

    mock_page = MagicMock(spec=Page)
    mock_page.id = uuid.UUID("12345678-1234-1234-1234-123456789012")
    mock_page.slug = "service-status"
    mock_create_page.return_value = mock_page

    # Writer (non-admin) should be able to refresh
    with app.app_context():
        # Use client context to preserve request/app context during the call
        with client:
            with mock_auth(test_writer_id, "writer"):
                headers = auth_headers(test_writer_id, "writer")
                resp = client.post("/api/admin/service-status/refresh", headers=headers)
                assert resp.status_code == 200
                data = resp.get_json()
                assert data["success"] is True


def test_get_service_logs_requires_auth(client):
    """Get service logs should require authentication"""
    resp = client.get("/api/admin/logs")
    assert resp.status_code == 401


@patch("app.utils.log_handler.get_log_handler")
def test_get_service_logs_requires_admin(
    mock_get_log_handler, client, app, test_writer_id
):
    """Get service logs should require admin role"""
    mock_handler = MagicMock()
    mock_handler.get_recent_logs.return_value = []
    mock_get_log_handler.return_value = mock_handler

    # Writer (non-admin) should be denied
    with mock_auth(test_writer_id, "writer"):
        headers = auth_headers(test_writer_id, "writer")
        resp = client.get("/api/admin/logs", headers=headers)
        assert resp.status_code == 403


@patch("app.utils.log_handler.get_log_handler")
def test_get_service_logs_allows_admin(
    mock_get_log_handler, client, app, test_admin_id
):
    """Get service logs should allow admin role"""
    mock_handler = MagicMock()
    mock_handler.get_recent_logs.return_value = [
        {
            "timestamp": "2024-01-01T12:00:00",
            "level": "INFO",
            "message": "Test log",
            "raw_message": "Test log",
        }
    ]
    mock_get_log_handler.return_value = mock_handler

    # Admin should be able to access
    with mock_auth(test_admin_id, "admin"):
        headers = auth_headers(test_admin_id, "admin")
        resp = client.get("/api/admin/logs", headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "logs" in data


def test_control_service_requires_auth(client):
    """Control service should require authentication"""
    resp = client.post(
        "/api/admin/service-status/wiki/control",
        json={"action": "start"},
    )
    assert resp.status_code == 401


def test_control_service_requires_admin(client, app, test_writer_id):
    """Control service should require admin role"""
    # Writer (non-admin) should be denied
    with mock_auth(test_writer_id, "writer"):
        headers = auth_headers(test_writer_id, "writer")
        resp = client.post(
            "/api/admin/service-status/wiki/control",
            json={"action": "start"},
            headers=headers,
        )
        assert resp.status_code == 403


@patch(
    "app.services.service_status_service.ServiceStatusService.get_service_process_info"
)
def test_control_service_allows_admin(
    mock_get_process_info, client, app, test_admin_id
):
    """Control service should allow admin role"""
    # Mock that service is not running
    mock_get_process_info.return_value = None

    # Admin should be able to control services
    with mock_auth(test_admin_id, "admin"):
        headers = auth_headers(test_admin_id, "admin")
        resp = client.post(
            "/api/admin/service-status/wiki/control",
            json={"action": "start"},
            headers=headers,
        )
        # Should either succeed (if service can be started) or return appropriate error
        # The important thing is it's not 401 or 403
        assert resp.status_code in (200, 400, 500)  # Not auth/forbidden error
