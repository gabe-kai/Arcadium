"""Tests for service management admin endpoints - logs, refresh, status notes"""

from unittest.mock import MagicMock, patch

from app import db
from app.models.wiki_config import WikiConfig
from tests.test_api.conftest import auth_headers, mock_auth


def test_get_service_logs_requires_auth(client):
    """Get service logs should require authentication"""
    resp = client.get("/api/admin/logs")
    assert resp.status_code == 401


@patch("app.utils.log_handler.get_log_handler")
def test_get_service_logs_success(mock_get_log_handler, client, app, test_admin_id):
    """Get service logs should return recent logs"""
    # Mock log handler
    mock_handler = MagicMock()
    mock_handler.get_recent_logs.return_value = [
        {
            "timestamp": "2024-01-01T12:00:00.123456",
            "level": "ERROR",
            "message": "Test error message",
            "raw_message": "Test error message",
            "pathname": "/app/test.py",
            "lineno": 42,
            "funcName": "test_func",
            "process": 12345,
            "thread": 140234567890,
            "threadName": "MainThread",
        },
        {
            "timestamp": "2024-01-01T12:00:01.123456",
            "level": "INFO",
            "message": "Test info message",
            "raw_message": "Test info message",
            "pathname": "/app/test.py",
            "lineno": 43,
            "funcName": "test_func",
            "process": 12345,
            "thread": 140234567890,
            "threadName": "MainThread",
        },
    ]
    mock_get_log_handler.return_value = mock_handler

    with mock_auth(test_admin_id, "admin"):
        headers = auth_headers(test_admin_id, "admin")
        resp = client.get("/api/admin/logs", headers=headers)

    assert resp.status_code == 200
    data = resp.get_json()
    assert "logs" in data
    assert len(data["logs"]) == 2
    assert data["logs"][0]["level"] == "ERROR"
    assert data["logs"][1]["level"] == "INFO"


@patch("app.utils.log_handler.get_log_handler")
def test_get_service_logs_with_limit(mock_get_log_handler, client, app, test_admin_id):
    """Get service logs should respect limit parameter"""
    mock_handler = MagicMock()
    mock_handler.get_recent_logs.return_value = [
        {"timestamp": "2024-01-01T12:00:00", "level": "INFO", "message": "Test"}
    ]
    mock_get_log_handler.return_value = mock_handler

    with mock_auth(test_admin_id, "admin"):
        headers = auth_headers(test_admin_id, "admin")
        resp = client.get("/api/admin/logs?limit=50", headers=headers)

    assert resp.status_code == 200
    mock_handler.get_recent_logs.assert_called_with(limit=50, level=None)


@patch("app.utils.log_handler.get_log_handler")
def test_get_service_logs_with_level_filter(
    mock_get_log_handler, client, app, test_admin_id
):
    """Get service logs should filter by level"""
    mock_handler = MagicMock()
    mock_handler.get_recent_logs.return_value = []
    mock_get_log_handler.return_value = mock_handler

    with mock_auth(test_admin_id, "admin"):
        headers = auth_headers(test_admin_id, "admin")
        resp = client.get("/api/admin/logs?level=ERROR", headers=headers)

    assert resp.status_code == 200
    mock_handler.get_recent_logs.assert_called_with(limit=100, level="ERROR")


@patch("app.utils.log_handler.get_log_handler")
def test_get_service_logs_max_limit(mock_get_log_handler, client, app, test_admin_id):
    """Get service logs should cap limit at 500"""
    mock_handler = MagicMock()
    mock_handler.get_recent_logs.return_value = []
    mock_get_log_handler.return_value = mock_handler

    with mock_auth(test_admin_id, "admin"):
        headers = auth_headers(test_admin_id, "admin")
        resp = client.get("/api/admin/logs?limit=1000", headers=headers)

    assert resp.status_code == 200
    mock_handler.get_recent_logs.assert_called_with(limit=500, level=None)


@patch("app.utils.log_handler.get_log_handler")
def test_get_service_logs_error_handling(
    mock_get_log_handler, client, app, test_admin_id
):
    """Get service logs should handle errors gracefully"""
    mock_handler = MagicMock()
    mock_handler.get_recent_logs.side_effect = Exception("Handler error")
    mock_get_log_handler.return_value = mock_handler

    with mock_auth(test_admin_id, "admin"):
        headers = auth_headers(test_admin_id, "admin")
        resp = client.get("/api/admin/logs", headers=headers)

    assert resp.status_code == 500
    data = resp.get_json()
    assert "error" in data


@patch("app.routes.admin_routes.ServiceStatusService.create_or_update_status_page")
@patch("app.routes.admin_routes.ServiceStatusService.check_all_services")
def test_refresh_service_status_success(
    mock_check_all, mock_create_page, client, app, test_admin_id
):
    """Refresh service status should trigger new health checks"""
    mock_check_all.return_value = {
        "wiki": {
            "status": "healthy",
            "response_time_ms": 5.0,
            "error": None,
            "details": {},
        }
    }
    # Mock the page creation
    import uuid

    from app.models.page import Page

    mock_page = MagicMock(spec=Page)
    mock_page.id = uuid.UUID("12345678-1234-1234-1234-123456789012")
    mock_page.slug = "service-status"
    mock_create_page.return_value = mock_page

    with app.app_context():
        # Use client context to preserve request/app context during the call
        with client:
            with mock_auth(test_admin_id, "admin"):
                headers = auth_headers(test_admin_id, "admin")
                resp = client.post("/api/admin/service-status/refresh", headers=headers)

        if resp.status_code != 200:
            print(f"Response status: {resp.status_code}")
            print(f"Response data: {resp.get_json()}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "message" in data
        assert (
            "page_id" in data
        )  # Changed from last_updated to page_id based on actual response
        mock_check_all.assert_called_once()
        mock_create_page.assert_called_once()


def test_refresh_service_status_requires_auth(client):
    """Refresh service status should require authentication"""
    resp = client.post("/api/admin/service-status/refresh")
    assert resp.status_code == 401


@patch("app.routes.admin_routes.ServiceStatusService.create_or_update_status_page")
@patch("app.routes.admin_routes.ServiceStatusService.check_all_services")
def test_refresh_service_status_allows_authenticated_users(
    mock_check_all, mock_create_page, client, app, test_writer_id
):
    """Refresh service status should allow any authenticated user (not just admin)"""
    import uuid
    from unittest.mock import MagicMock

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


@patch("app.routes.admin_routes.ServiceStatusService.check_all_services")
def test_refresh_service_status_error_handling(
    mock_check_all, client, app, test_admin_id
):
    """Refresh service status should handle errors"""
    mock_check_all.side_effect = Exception("Check failed")

    with mock_auth(test_admin_id, "admin"):
        headers = auth_headers(test_admin_id, "admin")
        resp = client.post("/api/admin/service-status/refresh", headers=headers)

    assert resp.status_code == 500
    data = resp.get_json()
    assert "error" in data


@patch("app.routes.admin_routes.ServiceStatusService.check_all_services")
def test_get_service_status_includes_status_reason(
    mock_check_all, client, app, test_admin_id
):
    """Get service status should include status_reason for non-healthy services"""
    mock_check_all.return_value = {
        "wiki": {
            "status": "healthy",
            "response_time_ms": 5.0,
            "error": None,
            "status_reason": None,
            "details": {},
        },
        "auth": {
            "status": "degraded",
            "response_time_ms": 1107.0,
            "error": None,
            "status_reason": "Slow response time (1107ms exceeds 1500ms threshold)",
            "details": {},
        },
    }

    with mock_auth(test_admin_id, "admin"):
        headers = auth_headers(test_admin_id, "admin")
        resp = client.get("/api/admin/service-status", headers=headers)

    assert resp.status_code == 200
    data = resp.get_json()
    assert "wiki" in data["services"]
    assert data["services"]["wiki"]["status_reason"] is None
    assert "auth" in data["services"]
    assert "status_reason" in data["services"]["auth"]
    assert "Slow response time" in data["services"]["auth"]["status_reason"]


@patch("app.routes.admin_routes.ServiceStatusService.check_all_services")
def test_get_service_status_includes_process_info(
    mock_check_all, client, app, test_admin_id
):
    """Get service status should include process_info for wiki service"""
    mock_check_all.return_value = {
        "wiki": {
            "status": "healthy",
            "response_time_ms": 5.0,
            "error": None,
            "process_info": {
                "pid": 12345,
                "uptime_seconds": 3600.0,
                "cpu_percent": 2.5,
                "memory_mb": 150.0,
                "memory_percent": 1.2,
                "threads": 8,
                "open_files": 15,
            },
            "details": {},
        }
    }

    with mock_auth(test_admin_id, "admin"):
        headers = auth_headers(test_admin_id, "admin")
        resp = client.get("/api/admin/service-status", headers=headers)

    assert resp.status_code == 200
    data = resp.get_json()
    assert "wiki" in data["services"]
    assert "process_info" in data["services"]["wiki"]
    assert data["services"]["wiki"]["process_info"]["pid"] == 12345
    assert data["services"]["wiki"]["process_info"]["uptime_seconds"] == 3600.0


def test_update_service_status_notes_success(client, app, test_admin_id):
    """Update service status notes should save notes to WikiConfig"""
    with mock_auth(test_admin_id, "admin"):
        headers = auth_headers(test_admin_id, "admin")
        resp = client.put(
            "/api/admin/service-status",
            json={
                "service": "auth",
                "notes": {
                    "notes": "Planned maintenance window",
                    "eta": "2024-01-01T15:00:00Z",
                },
            },
            headers=headers,
        )

    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["service"] == "auth"

    # Verify notes were saved
    with app.app_context():
        import json

        config = WikiConfig.query.filter_by(key="service_status_notes_auth").first()
        assert config is not None
        notes = json.loads(config.value)  # Parse JSON string
        assert notes["notes"] == "Planned maintenance window"
        assert notes["eta"] == "2024-01-01T15:00:00Z"


def test_update_service_status_notes_updates_existing(client, app, test_admin_id):
    """Update service status notes should update existing notes"""
    # Create initial notes
    with app.app_context():
        import json

        config = WikiConfig(
            key="service_status_notes_auth",
            value=json.dumps({"notes": "Old notes"}),  # Store as JSON string
            updated_by=test_admin_id,
        )
        db.session.add(config)
        db.session.commit()

    with mock_auth(test_admin_id, "admin"):
        headers = auth_headers(test_admin_id, "admin")
        resp = client.put(
            "/api/admin/service-status",
            json={
                "service": "auth",
                "notes": {"notes": "New notes", "eta": "2024-01-01T15:00:00Z"},
            },
            headers=headers,
        )

    assert resp.status_code == 200

    # Verify notes were updated
    with app.app_context():
        import json

        config = WikiConfig.query.filter_by(key="service_status_notes_auth").first()
        assert config is not None
        notes = json.loads(config.value)  # Parse JSON string
        assert notes["notes"] == "New notes"
        assert notes["eta"] == "2024-01-01T15:00:00Z"
