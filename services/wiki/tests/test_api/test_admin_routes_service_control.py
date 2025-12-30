"""Tests for service control admin endpoints"""

import json
from unittest.mock import patch

from tests.test_api.conftest import auth_headers, mock_auth


def test_control_service_requires_auth(client):
    """Service control should require authentication"""
    resp = client.post(
        "/api/admin/service-status/wiki/control",
        json={"action": "start"},
    )
    # Should return 401 or 403 (depending on auth setup)
    assert resp.status_code in (401, 403)


@patch("app.routes.admin_routes.ServiceStatusService.start_service")
@mock_auth
def test_control_service_start_success(mock_start_service, client, app, test_admin_id):
    """Test starting a service via API"""
    mock_start_service.return_value = {
        "success": True,
        "message": "Service wiki started successfully",
        "pid": 54321,
    }

    resp = client.post(
        "/api/admin/service-status/wiki/control",
        json={"action": "start"},
        headers=auth_headers(test_admin_id, role="admin"),
    )

    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["success"] is True
    assert "started successfully" in data["message"].lower()
    assert data["pid"] == 54321
    mock_start_service.assert_called_once_with("wiki")


@patch("app.routes.admin_routes.ServiceStatusService.stop_service")
@mock_auth
def test_control_service_stop_success(mock_stop_service, client, app, test_admin_id):
    """Test stopping a service via API"""
    mock_stop_service.return_value = {
        "success": True,
        "message": "Service wiki stopped successfully",
        "pid": 12345,
    }

    resp = client.post(
        "/api/admin/service-status/wiki/control",
        json={"action": "stop"},
        headers=auth_headers(test_admin_id, role="admin"),
    )

    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["success"] is True
    assert "stopped successfully" in data["message"].lower()
    assert data["pid"] == 12345
    mock_stop_service.assert_called_once_with("wiki")


@patch("app.routes.admin_routes.ServiceStatusService.restart_service")
@mock_auth
def test_control_service_restart_success(
    mock_restart_service, client, app, test_admin_id
):
    """Test restarting a service via API"""
    mock_restart_service.return_value = {
        "success": True,
        "message": "Service wiki restarted successfully",
        "pid": 54321,
    }

    resp = client.post(
        "/api/admin/service-status/wiki/control",
        json={"action": "restart"},
        headers=auth_headers(test_admin_id, role="admin"),
    )

    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["success"] is True
    assert (
        "restarted" in data["message"].lower() or "started" in data["message"].lower()
    )
    mock_restart_service.assert_called_once_with("wiki")


@mock_auth
def test_control_service_invalid_action(client, app, test_admin_id):
    """Test control service with invalid action"""
    resp = client.post(
        "/api/admin/service-status/wiki/control",
        json={"action": "invalid"},
        headers=auth_headers(test_admin_id, role="admin"),
    )

    assert resp.status_code == 400
    data = json.loads(resp.data)
    assert "error" in data
    assert "invalid action" in data["error"].lower()


@mock_auth
def test_control_service_missing_action(client, app, test_admin_id):
    """Test control service without action"""
    resp = client.post(
        "/api/admin/service-status/wiki/control",
        json={},
        headers=auth_headers(test_admin_id, role="admin"),
    )

    assert resp.status_code == 400
    data = json.loads(resp.data)
    assert "error" in data
    assert "invalid action" in data["error"].lower()


@mock_auth
def test_control_service_unknown_service(client, app, test_admin_id):
    """Test control service for unknown service"""
    resp = client.post(
        "/api/admin/service-status/unknown-service/control",
        json={"action": "start"},
        headers=auth_headers(test_admin_id, role="admin"),
    )

    assert resp.status_code == 400
    data = json.loads(resp.data)
    assert "error" in data
    assert "unknown service" in data["error"].lower()


@mock_auth
def test_control_service_non_controllable_service(client, app, test_admin_id):
    """Test control service for service that cannot be controlled"""
    resp = client.post(
        "/api/admin/service-status/game-server/control",
        json={"action": "start"},
        headers=auth_headers(test_admin_id, role="admin"),
    )

    assert resp.status_code == 400
    data = json.loads(resp.data)
    assert "error" in data
    assert "cannot be controlled automatically" in data["error"].lower()


@patch("app.routes.admin_routes.ServiceStatusService.start_service")
@mock_auth
def test_control_service_start_fails(mock_start_service, client, app, test_admin_id):
    """Test starting a service that fails"""
    mock_start_service.return_value = {
        "success": False,
        "message": "Service wiki is already running (PID: 12345)",
    }

    resp = client.post(
        "/api/admin/service-status/wiki/control",
        json={"action": "start"},
        headers=auth_headers(test_admin_id, role="admin"),
    )

    assert resp.status_code == 400
    data = json.loads(resp.data)
    assert data["success"] is False
    assert "already running" in data["message"].lower()


@patch("app.routes.admin_routes.ServiceStatusService.stop_service")
@mock_auth
def test_control_service_stop_fails(mock_stop_service, client, app, test_admin_id):
    """Test stopping a service that fails"""
    mock_stop_service.return_value = {
        "success": False,
        "message": "Service wiki is not running",
    }

    resp = client.post(
        "/api/admin/service-status/wiki/control",
        json={"action": "stop"},
        headers=auth_headers(test_admin_id, role="admin"),
    )

    assert resp.status_code == 400
    data = json.loads(resp.data)
    assert data["success"] is False
    assert "not running" in data["message"].lower()


@mock_auth
def test_control_service_requires_admin_role(client, app, test_admin_id):
    """Test that service control requires admin role"""
    # Try with viewer role
    resp = client.post(
        "/api/admin/service-status/wiki/control",
        json={"action": "start"},
        headers=auth_headers(test_admin_id, role="viewer"),
    )

    # Should return 403 Forbidden
    assert resp.status_code == 403


@patch("app.routes.admin_routes.ServiceStatusService.start_service")
@mock_auth
def test_control_service_auth_success(mock_start_service, client, app, test_admin_id):
    """Test controlling auth service"""
    mock_start_service.return_value = {
        "success": True,
        "message": "Service auth started successfully",
        "pid": 23456,
    }

    resp = client.post(
        "/api/admin/service-status/auth/control",
        json={"action": "start"},
        headers=auth_headers(test_admin_id, role="admin"),
    )

    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["success"] is True
    mock_start_service.assert_called_once_with("auth")


@patch("app.routes.admin_routes.ServiceStatusService.start_service")
@mock_auth
def test_control_service_web_client_success(
    mock_start_service, client, app, test_admin_id
):
    """Test controlling web-client service"""
    mock_start_service.return_value = {
        "success": True,
        "message": "Service web-client started successfully",
        "pid": 34567,
    }

    resp = client.post(
        "/api/admin/service-status/web-client/control",
        json={"action": "start"},
        headers=auth_headers(test_admin_id, role="admin"),
    )

    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["success"] is True
    mock_start_service.assert_called_once_with("web-client")


@patch("app.routes.admin_routes.ServiceStatusService.start_service")
@mock_auth
def test_control_service_file_watcher_success(
    mock_start_service, client, app, test_admin_id
):
    """Test controlling file-watcher service"""
    mock_start_service.return_value = {
        "success": True,
        "message": "Service file-watcher started successfully",
        "pid": 45678,
    }

    resp = client.post(
        "/api/admin/service-status/file-watcher/control",
        json={"action": "start"},
        headers=auth_headers(test_admin_id, role="admin"),
    )

    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["success"] is True
    mock_start_service.assert_called_once_with("file-watcher")
